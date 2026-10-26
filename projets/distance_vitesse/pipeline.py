"""Pipeline principal : détection + suivi -> mesures -> plaques -> zones -> rendu/sorties."""

from __future__ import annotations

import csv
import json
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

from vision_lab.config import OutputSettings
from vision_lab.events import EventBus
from vision_lab.outputs import Outputs
from vision_lab.sources import VideoSource, is_image

from . import static_objects
from .classes import COCO_CLASSES, ClassInfo, parse_open_vocab, supports_plates
from .detections import Detection, RiderGrouper
from .draw import draw_detections, draw_hud, draw_zone_counts, draw_zones
from .measure import GroundPlane, SpeedEstimator, camera_position, estimate_distance, focal_length_from_fov
from .settings import Settings
from .zones import ZoneCounter

MIN_DISPLAYED_SPEED_KMH = 2.0   # en dessous : bruit de la boîte, on affiche 0


@dataclass
class TrackStats:
    labels: Counter = field(default_factory=Counter)
    first_t: float = 0.0
    last_t: float = 0.0
    frames: int = 0
    speeds: list[float] = field(default_factory=list)
    min_distance: float | None = None
    plate: str | None = None
    plate_region: str | None = None


class Pipeline:
    def __init__(self, settings: Settings, output_settings: OutputSettings | None = None,
                 bus: EventBus | None = None):
        import torch
        from ultralytics import YOLO

        self.settings = settings
        self.output_settings = output_settings or OutputSettings(view="none")
        self.bus = bus or EventBus("traffic")
        self.has_gpu = torch.cuda.is_available()
        self.device = settings.device or (0 if self.has_gpu else "cpu")
        self.half = settings.half if settings.half is not None else self.has_gpu

        model_path = settings.resolved_model(self.has_gpu)
        self.model_name = Path(model_path).name
        self.model = YOLO(model_path)

        if settings.open_vocab_classes:
            self.catalog: dict[int, ClassInfo] = parse_open_vocab(settings.open_vocab_classes)
            try:
                self.model.set_classes([info.label for info in self.catalog.values()])
            except ModuleNotFoundError as exc:
                raise RuntimeError(
                    "Le vocabulaire ouvert (YOLOE) nécessite CLIP : "
                    "pip install git+https://github.com/ultralytics/CLIP.git"
                ) from exc
            self.class_filter = None
        else:
            self.catalog = COCO_CLASSES
            self.class_filter = list(COCO_CLASSES)

        self.colors = {info.label: info.color for info in self.catalog.values()}
        self.colors.update({"Cycliste": (255, 80, 80), "Motard": (255, 255, 120)})

        self.ground = GroundPlane.from_file(settings.calibration_file) if settings.calibration_file else None
        self.speed = SpeedEstimator(window_s=settings.speed_window_s)
        self.grouper = RiderGrouper()
        self.zones = ZoneCounter.from_file(settings.zones_file)
        self.zones.on_event = lambda event: self.bus.publish(event["type"], event["t"], **{
            k: v for k, v in event.items() if k not in ("type", "t")})
        self.static_objects = static_objects.load(settings.static_objects_file)
        self.static_distances: dict[str, float | None] = {}
        self.all_events: list[dict] = []
        self.bus.add_listener(lambda event: event["type"] != "stats" and self.all_events.append(event))

        self.plates = None
        if settings.plates_enabled:
            try:
                from .plates import PlateReader

                self.plates = PlateReader(
                    settings.plate_detector_model, settings.plate_ocr_model, settings.resolved("plate_every"),
                    device=settings.plate_device, fallback_countries=settings.plate_countries,
                )
            except Exception as exc:  # le reste fonctionne sans les plaques
                print(f"[plaques] désactivées : {exc}")

        self.tracks: dict[int, TrackStats] = defaultdict(TrackStats)

    # ------------------------------------------------------------------ inférence
    def _infer(self, frame: np.ndarray, track: bool):
        kwargs = dict(
            imgsz=self.settings.resolved("imgsz"), conf=self.settings.conf, device=self.device,
            quantize=16 if self.half else 32, classes=self.class_filter, verbose=False,
        )
        if track:
            return self.model.track(frame, persist=True, tracker=self.settings.resolved("tracker"), **kwargs)[0]
        return self.model.predict(frame, **kwargs)[0]

    def process(self, frame: np.ndarray, timestamp: float, frame_index: int, track: bool = True) -> list[Detection]:
        height, width = frame.shape[:2]
        focal = self.settings.focal_length_px or focal_length_from_fov(width, self.settings.camera_hfov_deg)
        result = self._infer(frame, track)

        detections: list[Detection] = []
        boxes = result.boxes
        if boxes is not None and len(boxes):
            xyxy = boxes.xyxy.cpu().numpy().astype(int)
            classes = boxes.cls.cpu().numpy().astype(int)
            confs = boxes.conf.cpu().numpy()
            ids = boxes.id.cpu().numpy().astype(int) if boxes.id is not None else [None] * len(classes)
            for box, class_id, conf, track_id in zip(xyxy, classes, confs, ids, strict=True):
                info = self.catalog.get(int(class_id))
                if info is None:
                    continue
                det = Detection(tuple(int(v) for v in box), int(class_id), info.label, float(conf),
                                None if track_id is None else int(track_id))
                truncated = det.box[1] <= 2 or det.box[3] >= height - 2
                if not truncated:
                    det.distance_m = estimate_distance(det.height_px, info.height_m, focal)
                detections.append(det)

        # Mesures sur les boîtes d'origine, puis regroupement cycliste/motard.
        for det in detections:
            self._measure_speed(det, timestamp, width, height, focal)
            self._read_plate(det, frame, frame_index)
        self.grouper.apply(detections)

        visible = [d for d in detections if not d.hidden]
        self.zones.update(visible, width, height, timestamp)
        self._record(visible, timestamp)
        self.speed.forget({d.track_id for d in detections if d.track_id is not None})
        return detections

    def _measure_speed(self, det: Detection, timestamp: float, width: int, height: int, focal: float) -> None:
        if det.track_id is None:
            return
        if self.ground is not None:
            position = self.ground.to_world(*det.anchor, width, height)
            det.speed_calibrated = True
        elif det.distance_m is not None:
            position = camera_position(det.anchor[0], width, det.distance_m, focal)
        else:
            return
        speed_ms = self.speed.update(det.track_id, timestamp, position)
        if speed_ms is not None:
            kmh = speed_ms * 3.6
            det.speed_kmh = 0.0 if kmh < MIN_DISPLAYED_SPEED_KMH else kmh

    def _read_plate(self, det: Detection, frame: np.ndarray, frame_index: int) -> None:
        info = self.catalog[det.class_id]
        if self.plates is None or not supports_plates(info) or det.height_px < self.settings.plate_min_vehicle_px:
            return
        if det.track_id is None:
            from .plates import crop_box

            reading = self.plates.read_crop(crop_box(frame, det.box), centered=False)
        else:
            reading = self.plates.update(det.track_id, frame_index, frame, det.box)
        if reading:
            det.plate, det.plate_region = reading.text, reading.region

    def _record(self, detections: list[Detection], timestamp: float) -> None:
        for det in detections:
            if det.track_id is None:
                continue
            stats = self.tracks[det.track_id]
            if stats.frames == 0:
                stats.first_t = timestamp
            stats.frames += 1
            stats.last_t = timestamp
            stats.labels[det.label] += 1
            if det.speed_kmh is not None:
                stats.speeds.append(det.speed_kmh)
            if det.distance_m is not None and (stats.min_distance is None or det.distance_m < stats.min_distance):
                stats.min_distance = det.distance_m
            if det.plate and det.plate != stats.plate:
                stats.plate, stats.plate_region = det.plate, det.plate_region
                self.bus.publish("plate", timestamp, track_id=det.track_id, label=det.label,
                                 plate=det.plate, region=det.plate_region, speed_kmh=det.speed_kmh)

    # ------------------------------------------------------------------ rendu
    def render(self, frame: np.ndarray, detections: list[Detection], fps: float | None) -> np.ndarray:
        draw_zones(frame, self.zones)
        draw_detections(frame, detections, self.colors, self.settings.labels)
        draw_zone_counts(frame, self.zones)
        if self.static_objects:
            self.static_distances = static_objects.draw(frame, self.static_objects, self._focal(frame))
        counts = Counter(d.label for d in detections if not d.hidden)
        hud = [f"{self.settings.mode} | {self.model_name}" + (f" | {fps:.1f} FPS" if fps else "")]
        if counts:
            hud.append(", ".join(f"{label}: {n}" for label, n in counts.most_common(5)))
        draw_hud(frame, hud)
        return frame

    def _focal(self, frame: np.ndarray) -> float:
        return self.settings.focal_length_px or focal_length_from_fov(frame.shape[1], self.settings.camera_hfov_deg)

    def current_stats(self, detections: list[Detection], fps: float | None) -> dict:
        visible = [d for d in detections if not d.hidden]
        return {
            "fps": None if fps is None else round(fps, 1),
            "objets_visibles": dict(Counter(d.label for d in visible)),
            "objets_suivis_total": len(self.tracks),
            "vitesses_kmh": {str(d.track_id): round(d.speed_kmh, 1) for d in visible
                             if d.track_id is not None and d.speed_kmh},
            "objets_statiques_m": self.static_distances,
            **self.zones.summary(),
        }

    # ------------------------------------------------------------------ exécution
    def run(self) -> Path:
        source = self.settings.source
        if is_image(source):
            return self._run_image(source)
        return self._run_video(source)

    def _output_dir(self, source: str) -> Path:
        stem = "webcam" if source.isdigit() else Path(source.split("?")[0]).stem or "stream"
        path = self.output_settings.output_dir / f"{stem}_{datetime.now():%Y%m%d_%H%M%S}"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _run_image(self, source: str) -> Path:
        frame = cv2.imread(source)
        if frame is None:
            raise RuntimeError(f"Impossible de lire l'image : {source}")
        detections = self.process(frame, 0.0, 0, track=False)
        self.render(frame, detections, None)
        out_dir = self._output_dir(source)
        cv2.imwrite(str(out_dir / "annotated.jpg"), frame)
        self._write_detections_csv(out_dir / "detections.csv", detections)
        self.bus.update_stats(self.current_stats(detections, None), force=True)
        outputs = Outputs(self.output_settings, self.bus, title="Vision Lab - distance & vitesse")
        outputs.write(frame)
        if outputs.viewer.kind == "window":
            outputs.viewer.show(frame, wait_ms=0)
        elif outputs.viewer.kind == "web" or outputs.api:
            input("Appuyez sur Entrée pour arrêter le serveur…")
        outputs.close()
        print(f"Résultats : {out_dir}")
        return out_dir

    def _run_video(self, source: str) -> Path:
        capture = VideoSource(source, drop_frames=self.settings.resolved("drop_frames"))
        out_dir = self._output_dir(source)
        record = out_dir / "annotated.mp4" if self.settings.resolved("save_video") else None
        outputs = Outputs(self.output_settings, self.bus, record_path=record, fps=capture.fps,
                          live=capture.live, title="Vision Lab - distance & vitesse")

        frame_index, fps, last_tick, last_log = 0, None, time.monotonic(), time.monotonic()
        try:
            for frame, timestamp in capture:
                detections = self.process(frame, timestamp, frame_index)
                now = time.monotonic()
                instant = 1.0 / max(1e-6, now - last_tick)
                fps = instant if fps is None else 0.9 * fps + 0.1 * instant
                last_tick = now
                self.render(frame, detections, fps)
                self.bus.update_stats(self.current_stats(detections, fps), timestamp)
                if not outputs.write(frame):
                    break
                if self.output_settings.view == "none" and now - last_log > 2:
                    total = f"/{capture.frame_count}" if capture.frame_count else ""
                    print(f"image {frame_index + 1}{total} - {fps:.1f} FPS - {len(self.tracks)} objets suivis")
                    last_log = now
                frame_index += 1
        except KeyboardInterrupt:
            print("Arrêt demandé.")
        finally:
            capture.release()
            outputs.close()

        self.bus.update_stats(self.current_stats([], fps), force=True)
        self._write_reports(out_dir)
        print(f"Résultats : {out_dir}")
        return out_dir

    # ------------------------------------------------------------------ rapports
    @staticmethod
    def _write_detections_csv(path: Path, detections: list[Detection]) -> None:
        with open(path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["label", "confiance", "x1", "y1", "x2", "y2", "distance_m", "plaque", "region"])
            for det in detections:
                if det.hidden:
                    continue
                writer.writerow([det.label, f"{det.confidence:.2f}", *det.box,
                                 "" if det.distance_m is None else f"{det.distance_m:.2f}",
                                 det.plate or "", det.plate_region or ""])

    def _write_reports(self, out_dir: Path) -> None:
        with open(out_dir / "tracks.csv", "w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["track_id", "label", "debut_s", "fin_s", "images", "vitesse_moy_kmh",
                             "vitesse_max_kmh", "distance_min_m", "plaque", "region"])
            for track_id, stats in sorted(self.tracks.items()):
                if stats.frames < 3:     # pistes fantômes
                    continue
                speeds = stats.speeds
                writer.writerow([
                    track_id, stats.labels.most_common(1)[0][0], f"{stats.first_t:.2f}", f"{stats.last_t:.2f}",
                    stats.frames,
                    f"{np.mean(speeds):.1f}" if speeds else "", f"{np.percentile(speeds, 95):.1f}" if speeds else "",
                    f"{stats.min_distance:.1f}" if stats.min_distance is not None else "",
                    stats.plate or "", stats.plate_region or "",
                ])
        if self.all_events:
            with open(out_dir / "events.jsonl", "w", encoding="utf-8") as handle:
                for event in self.all_events:
                    handle.write(json.dumps(event, ensure_ascii=False) + "\n")
        summary = {
            "source": self.settings.source,
            "mode": self.settings.mode,
            "model": self.model_name,
            "objets": dict(Counter(s.labels.most_common(1)[0][0] for s in self.tracks.values() if s.frames >= 3)),
            "objets_statiques_m": self.static_distances,
            **self.zones.summary(),
        }
        (out_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
