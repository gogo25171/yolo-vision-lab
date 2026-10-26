"""Tests de la logique pure (sans modèle ni GPU) : python -m pytest"""

import math

import pytest

from projets.distance_vitesse.detections import Detection, RiderGrouper
from projets.distance_vitesse.measure import GroundPlane, SpeedEstimator, estimate_distance, focal_length_from_fov
from projets.distance_vitesse.plate_formats import normalize
from projets.distance_vitesse.zones import Line, Zone, ZoneCounter


@pytest.mark.parametrize(
    ("raw", "region", "expected"),
    [
        ("AB123CD", None, ("AB-123-CD", "France")),
        ("AB12SCD", "France", ("AB-125-CD", "France")),      # S lu à la place de 5
        ("0B123CO", None, ("DB-123-CD", "France")),          # 0/O interdits en SIV -> D
        ("1234AB75", None, ("1234 AB 75", "France")),        # ancien FNI
        ("SS123AA", None, ("SS123AA", None)),                # SS jamais attribué en tête
        ("5AU5341", "Czech Republic", ("5AU5341", "Czech Republic")),  # pays sans format : inchangé
        ("1ABC123", "Belgium", ("1-ABC-123", "Belgium")),
    ],
)
def test_plate_normalize(raw, region, expected):
    assert normalize(raw, region) == expected


def test_distance_pinhole():
    focal = focal_length_from_fov(1920, 90)
    assert focal == pytest.approx(960)
    # Une personne de 1,7 m qui fait 170 px de haut avec f=960 px est à 9,6 m.
    assert estimate_distance(170, 1.7, focal) == pytest.approx(9.6)
    assert estimate_distance(170, None, focal) is None


def test_speed_constant_motion():
    estimator = SpeedEstimator(window_s=1.0, min_span_s=0.4, smoothing=1.0)
    speed = None
    for i in range(50):                       # 10 m/s pendant 2 s, 25 images/s
        t = i / 25
        speed = estimator.update(1, t, (10 * t, 0.0))
    assert speed * 3.6 == pytest.approx(36, rel=0.1)


def test_ground_plane_normalized():
    plane = GroundPlane([[0, 0], [1, 0], [1, 1], [0, 1]], [[0, 0], [10, 0], [10, 20], [0, 20]])
    x, y = plane.to_world(960, 540, 1920, 1080)
    assert (x, y) == (pytest.approx(5), pytest.approx(10))


def _det(box, label, track_id):
    return Detection(box=box, class_id=0, label=label, confidence=0.9, track_id=track_id)


def test_rider_grouping_needs_confirmation():
    grouper = RiderGrouper(confirm_frames=3)
    for frame in range(3):
        person = _det((100, 50, 140, 200), "Personne", 1)
        bike = _det((90, 120, 160, 220), "Vélo", 2)
        grouper.apply([person, bike])
        if frame < 2:
            assert not person.hidden
    assert person.hidden
    assert bike.label == "Cycliste"
    assert bike.box == (90, 50, 160, 220)


def test_pedestrian_next_to_bike_is_not_rider():
    grouper = RiderGrouper(confirm_frames=1)
    person = _det((300, 50, 340, 200), "Personne", 1)
    bike = _det((90, 120, 160, 220), "Vélo", 2)
    grouper.apply([person, bike])
    assert not person.hidden and bike.label == "Vélo"


def test_zone_exit_is_debounced():
    zone = Zone("Z", [[0, 0], [1, 0], [1, 1], [0, 1]])
    counter = ZoneCounter([zone], [])
    counter.exit_after_frames = 5
    car = _det((100, 100, 200, 200), "Voiture", 3)
    frames = [[car]] * 3 + [[]] * 3 + [[car]] * 3 + [[]] * 6   # clignotement de 3 images, puis départ
    for i, dets in enumerate(frames):
        counter.update(dets, 1000, 1000, i / 25)
    types = [e["type"] for e in counter.events]
    assert types == ["zone_enter", "zone_exit"]


def test_zone_and_line_counting():
    zone = Zone("Z", [[0, 0.5], [1, 0.5], [1, 1], [0, 1]])
    line = Line("L", [[0.5, 0], [0.5, 1]])
    counter = ZoneCounter([zone], [line])
    for step, x in enumerate([400, 450, 500, 550, 600]):   # traverse x=500 vers la droite, en bas
        car = _det((x - 20, 900, x + 20, 1000), "Voiture", 7)
        counter.update([car], 1000, 1000, step / 25)
    assert zone.totals()["Voiture"] == 1
    assert sum(line.count_in.values()) + sum(line.count_out.values()) == 1
    assert any(e["type"].startswith("line_") for e in counter.events)
    assert math.isclose(len([e for e in counter.events if e["type"] == "zone_enter"]), 1)
