"""Tools for mapping affect estimates into the V/A/D affective space."""
import math

from .. import config


def clamp(value, lower=-1.0, upper=1.0):
    """Return a float bounded by the supplied limits."""
    return max(lower, min(upper, float(value)))


def sam_to_unit(rating):
    """Convert a 1-9 Self-Assessment Manikin rating to the -1..1 scale."""
    return (float(rating) - 5.0) / 4.0


def unit_to_sam(value):
    """Convert a -1..1 value back to the 1–9 Self-Assessment Manikin scale."""
    return float(value) * 4.0 + 5.0


def _distance(point, prototype):
    """Return weighted Euclidean distance in V/A/D space."""
    valence_delta = point[0] - prototype[0]
    activity_delta = point[1] - prototype[1]
    dominance_delta = point[2] - prototype[2]
    return math.sqrt(
        valence_delta * valence_delta
        + activity_delta * activity_delta
        + config.LABEL_D_WEIGHT * dominance_delta * dominance_delta
    )


def classify_vad(valence, activity, dominance, prototypes=None):
    """Return the nearest prototype and its runner-up with weighted distances.

    The distance is sqrt((V-Vp)^2 + (A-Ap)^2 +
    LABEL_D_WEIGHT*(D-Dp)^2). A separate radius around the origin preserves a
    neutral region even when another prototype happens to be slightly nearer.
    """
    selected_prototypes = (
        config.LABEL_PROTOTYPES if prototypes is None else prototypes
    )
    if not selected_prototypes:
        raise ValueError("At least one label prototype is required.")

    point = (
        clamp(valence),
        clamp(activity),
        clamp(dominance),
    )
    distances = [
        (label, _distance(point, prototype))
        for label, prototype in selected_prototypes.items()
    ]
    distances.sort(key=lambda item: item[1])

    origin_distance = _distance(point, (0.0, 0.0, 0.0))
    if (
        "neutral" in selected_prototypes
        and origin_distance <= config.LABEL_NEUTRAL_RADIUS
    ):
        label = "neutral"
    else:
        label = distances[0][0]

    runner_up = next((item for item in distances if item[0] != label), None)
    return {
        "label": label,
        "second_label": runner_up[0] if runner_up else None,
        "label_distance": next(
            distance for candidate, distance in distances if candidate == label
        ),
        "second_distance": runner_up[1] if runner_up else None,
    }


def label_for(valence, activity, dominance):
    """Return the nearest prototype label for a V/A/D point."""
    return classify_vad(valence, activity, dominance)["label"]
