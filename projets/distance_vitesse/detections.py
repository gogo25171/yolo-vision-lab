"""Objets détectés et regroupement des personnes avec leur véhicule (cycliste, motard).

Sans regroupement, un cycliste compte double : une « Personne » et un « Vélo ». On
associe donc chaque personne au vélo/moto qu'elle chevauche ; le vélo devient un
objet « Cycliste » (ou « Motard ») et la personne est masquée des comptages.

L'association est « collante » : une fois confirmée sur quelques images, elle est
conservée tant que les deux pistes existent et se chevauchent encore un peu, ce
qui évite le clignotement quand le recouvrement varie.
"""

from __future__ import annotations

from dataclasses import dataclass, field

RIDEABLE = {"Vélo": "Cycliste", "Moto": "Motard"}
PERSON_LABEL = "Personne"


@dataclass
class Detection:
    box: tuple[int, int, int, int]       # x1, y1, x2, y2
    class_id: int
    label: str
    confidence: float
    track_id: int | None = None
    distance_m: float | None = None
    speed_kmh: float | None = None
    speed_calibrated: bool = False
    plate: str | None = None
    plate_region: str | None = None
    rider_ids: list[int] = field(default_factory=list)   # personnes portées par ce véhicule
    hidden: bool = False                 # personne fusionnée dans un véhicule

    @property
    def anchor(self) -> tuple[float, float]:
        """Point de contact au sol (bas-centre de la boîte)."""
        x1, _, x2, y2 = self.box
        return (x1 + x2) / 2, float(y2)

    @property
    def height_px(self) -> int:
        return self.box[3] - self.box[1]

    @property
    def width_px(self) -> int:
        return self.box[2] - self.box[0]


def _overlap_ratio(person: tuple, vehicle: tuple) -> float:
    """Part de la boîte de la personne recouverte par celle du véhicule."""
    ix1, iy1 = max(person[0], vehicle[0]), max(person[1], vehicle[1])
    ix2, iy2 = min(person[2], vehicle[2]), min(person[3], vehicle[3])
    inter = max(0, ix2 - ix1) * max(0, iy2 - iy1)
    area = max(1, (person[2] - person[0]) * (person[3] - person[1]))
    return inter / area


def _looks_like_rider(person: Detection, vehicle: Detection, threshold: float) -> bool:
    if _overlap_ratio(person.box, vehicle.box) < threshold:
        return False
    # Le centre de la personne doit être au-dessus du véhicule, à peu près centré.
    px = (person.box[0] + person.box[2]) / 2
    vx1, _, vx2, vy2 = vehicle.box
    margin = 0.25 * (vx2 - vx1)
    return vx1 - margin <= px <= vx2 + margin and person.box[3] <= vy2 + 0.15 * vehicle.height_px


class RiderGrouper:
    def __init__(self, enter_threshold: float = 0.25, keep_threshold: float = 0.08, confirm_frames: int = 3):
        self.enter_threshold = enter_threshold
        self.keep_threshold = keep_threshold
        self.confirm_frames = confirm_frames
        self._pairs: dict[int, int] = {}            # person_track -> vehicle_track (confirmé)
        self._candidates: dict[tuple[int, int], int] = {}

    def apply(self, detections: list[Detection]) -> None:
        persons = [d for d in detections if d.label == PERSON_LABEL]
        vehicles = [d for d in detections if d.label in RIDEABLE]
        by_track = {d.track_id: d for d in vehicles if d.track_id is not None}
        seen_candidates: set[tuple[int, int]] = set()

        for person in persons:
            vehicle = None
            pinned = self._pairs.get(person.track_id) if person.track_id is not None else None
            if pinned in by_track and _overlap_ratio(person.box, by_track[pinned].box) >= self.keep_threshold:
                vehicle = by_track[pinned]
            else:
                if person.track_id in self._pairs:
                    del self._pairs[person.track_id]
                matches = [v for v in vehicles if _looks_like_rider(person, v, self.enter_threshold)]
                if matches:
                    best = max(matches, key=lambda v: _overlap_ratio(person.box, v.box))
                    if person.track_id is None or best.track_id is None:
                        vehicle = best          # image fixe : pas d'historique
                    else:
                        key = (person.track_id, best.track_id)
                        seen_candidates.add(key)
                        self._candidates[key] = self._candidates.get(key, 0) + 1
                        if self._candidates[key] >= self.confirm_frames:
                            self._pairs[person.track_id] = best.track_id
                            vehicle = best
            if vehicle is not None:
                person.hidden = True
                vehicle.rider_ids.append(person.track_id if person.track_id is not None else -1)
                vehicle.label = RIDEABLE.get(vehicle.label, vehicle.label)
                vehicle.box = _union(vehicle.box, person.box)

        self._candidates = {k: v for k, v in self._candidates.items() if k in seen_candidates}


def _union(a: tuple, b: tuple) -> tuple[int, int, int, int]:
    return min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3])
