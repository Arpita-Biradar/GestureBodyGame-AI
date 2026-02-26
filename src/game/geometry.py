from .config import CAMERA_HEIGHT, HORIZON_Y, LANE_X, PROJECTION_SCALE, WIDTH


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def lane_x(lane: int) -> float:
    return LANE_X[int(clamp(lane, 0, 2))]


def project_world(x: float, y: float, z: float) -> tuple[float, float, float] | None:
    if z <= 0.12:
        return None
    scale = PROJECTION_SCALE / z
    screen_x = (WIDTH * 0.5) + (x * scale)
    screen_y = HORIZON_Y + ((CAMERA_HEIGHT - y) * scale)
    return screen_x, screen_y, scale
