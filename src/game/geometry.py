from .config import GROUND_Y, HORIZON_Y, LANE_BOTTOM, LANE_TOP


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def depth_from_y(base_y: float) -> float:
    return clamp((base_y - HORIZON_Y) / (GROUND_Y - HORIZON_Y), 0.0, 1.0)


def lane_x(lane: int, depth: float) -> float:
    return LANE_TOP[lane] + (LANE_BOTTOM[lane] - LANE_TOP[lane]) * depth
