"""Télécharge les échantillons de test (vidéos libres de droits) dans samples/.

Usage :
    python scripts/download_samples.py            # télécharge + découpe (ffmpeg si dispo)
    python scripts/download_samples.py --force    # retélécharge tout

Les originaux sont gardés dans samples/.cache/ (ignoré par git). Si ffmpeg est
disponible, chaque vidéo est découpée et réencodée en H.264 (mp4, sans son) pour
rester légère ; sinon l'original .webm est copié tel quel.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SAMPLES_DIR = ROOT / "samples"
CACHE_DIR = SAMPLES_DIR / ".cache"
USER_AGENT = "traffic-vision-samples/1.0 (https://github.com/gogo25171/yolo_distance_calculator)"


@dataclass(frozen=True)
class Sample:
    name: str          # nom du fichier de sortie (sans extension)
    url: str
    page: str          # page de description (licence / auteur)
    author: str
    license: str
    use_case: str
    start: float = 0.0
    duration: float | None = 30.0
    max_height: int = 1080


VIDEOS = [
    Sample(
        name="street_ljubljana",
        url="https://upload.wikimedia.org/wikipedia/commons/2/20/Road_traffic_on_Stritarjeva_street.webm",
        page="https://commons.wikimedia.org/wiki/File:Road_traffic_on_Stritarjeva_street.webm",
        author="Sounds of Changes",
        license="CC BY 3.0",
        use_case="Rue urbaine (Slovénie) : voitures, distance, vitesse, plaques UE",
    ),
    Sample(
        name="parking_cctv",
        url="https://upload.wikimedia.org/wikipedia/commons/1/14/BLK-HDPTZ12_Security_Camera_Parking_Lot_Surveillance_Video.webm",
        page="https://commons.wikimedia.org/wiki/File:BLK-HDPTZ12_Security_Camera_Parking_Lot_Surveillance_Video.webm",
        author="Supercircuits",
        license="Domaine public",
        use_case="Vraie caméra CCTV de parking : mode fast, zones, plaques US",
        start=10.0,
    ),
    Sample(
        name="crosswalk_toronto",
        url="https://upload.wikimedia.org/wikipedia/commons/d/d2/DiagonalCrosswalkYongeDundas.webm",
        page="https://commons.wikimedia.org/wiki/File:DiagonalCrosswalkYongeDundas.webm",
        author="Raysonho @ Open Grid Scheduler / Grid Engine",
        license="CC0",
        use_case="Carrefour piéton (Canada) : comptage de personnes, lignes de passage",
        max_height=720,
    ),
    Sample(
        name="roundabout",
        url="https://upload.wikimedia.org/wikipedia/commons/c/cc/Roundabout_14_61.webm",
        page="https://commons.wikimedia.org/wiki/File:Roundabout_14_61.webm",
        author="Wikideas1",
        license="CC0",
        use_case="Rond-point : comptage de véhicules par zone",
        max_height=720,
    ),
    Sample(
        name="dogs_tokyo",
        url="https://upload.wikimedia.org/wikipedia/commons/0/0c/Pro_dog_walker_-_Tokyo_-_2024_Nov_1.webm",
        page="https://commons.wikimedia.org/wiki/File:Pro_dog_walker_-_Tokyo_-_2024_Nov_1.webm",
        author="Nesnad",
        license="CC BY-SA 4.0 (la version découpée reste sous CC BY-SA 4.0)",
        use_case="Animaux (chiens) + piétons",
        duration=None,
        max_height=720,
    ),
]

IMAGES = [
    Sample(
        name="plate_test",
        url="https://raw.githubusercontent.com/ankandrew/fast-alpr/master/assets/test_image.png",
        page="https://github.com/ankandrew/fast-alpr",
        author="ankandrew (projet fast-alpr)",
        license="MIT",
        use_case="Image de test pour la lecture de plaques",
        duration=None,
    ),
]


def download(url: str, dest: Path, force: bool) -> Path:
    if dest.exists() and not force:
        print(f"  déjà en cache : {dest.name}")
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"  téléchargement : {url}")
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    tmp = dest.with_suffix(dest.suffix + ".part")
    with urllib.request.urlopen(request, timeout=60) as response, open(tmp, "wb") as out:
        shutil.copyfileobj(response, out)
    tmp.replace(dest)
    return dest


def transcode(src: Path, sample: Sample, dest: Path) -> None:
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-ss", str(sample.start), "-i", str(src)]
    if sample.duration:
        cmd += ["-t", str(sample.duration)]
    cmd += [
        "-vf", f"scale=-2:'min({sample.max_height},ih)'",
        "-c:v", "libx264", "-preset", "medium", "-crf", "24", "-pix_fmt", "yuv420p",
        "-an", "-movflags", "+faststart", str(dest),
    ]
    subprocess.run(cmd, check=True)


def write_sources(entries: list[tuple[Sample, Path]]) -> None:
    lines = [
        "# Sources des échantillons de test",
        "",
        "Fichiers générés par `scripts/download_samples.py`. Les vidéos ont été découpées",
        "et réencodées (H.264, sans son) ; les licences d'origine s'appliquent.",
        "",
        "| Fichier | Usage | Auteur | Licence | Source |",
        "|---|---|---|---|---|",
    ]
    for sample, path in entries:
        rel = path.relative_to(SAMPLES_DIR).as_posix()
        lines.append(
            f"| `{rel}` | {sample.use_case} | {sample.author} | {sample.license} | [lien]({sample.page}) |"
        )
    (SAMPLES_DIR / "SOURCES.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--force", action="store_true", help="retélécharge et réencode tout")
    args = parser.parse_args()

    has_ffmpeg = shutil.which("ffmpeg") is not None
    if not has_ffmpeg:
        print("ffmpeg introuvable : les vidéos seront copiées sans découpage (.webm).")

    entries: list[tuple[Sample, Path]] = []
    for sample in VIDEOS:
        print(f"[vidéo] {sample.name}")
        raw = download(sample.url, CACHE_DIR / f"{sample.name}.webm", args.force)
        out_dir = SAMPLES_DIR / "videos"
        out_dir.mkdir(parents=True, exist_ok=True)
        if has_ffmpeg:
            dest = out_dir / f"{sample.name}.mp4"
            if args.force or not dest.exists():
                transcode(raw, sample, dest)
        else:
            dest = out_dir / f"{sample.name}.webm"
            shutil.copyfile(raw, dest)
        print(f"  -> {dest.relative_to(ROOT)} ({dest.stat().st_size / 1e6:.1f} Mo)")
        entries.append((sample, dest))

    for sample in IMAGES:
        print(f"[image] {sample.name}")
        dest = download(sample.url, SAMPLES_DIR / "images" / f"{sample.name}{Path(sample.url).suffix}", args.force)
        entries.append((sample, dest))

    write_sources(entries)
    print(f"OK : {len(entries)} fichiers, crédits dans samples/SOURCES.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
