from __future__ import annotations

from dataclasses import dataclass


def _clamp01(value: float) -> float:
    if value <= 0.0:
        return 0.0
    if value >= 1.0:
        return 1.0
    return value


@dataclass(slots=True)
class SessionMetrics:
    combo: int = 0
    calories: float = 0.0
    intensity: float = 0.0
    elapsed_seconds: float = 0.0
    progress: float = 0.0
    _combo_decay_timer: float = 0.0


class GameManager:
    """Tracks gameplay metrics used by the futuristic HUD and summary panel."""

    def __init__(self, session_target_seconds: float = 180.0) -> None:
        self.session_target_seconds = max(30.0, float(session_target_seconds))
        self.metrics = SessionMetrics()

    def reset_session(self) -> None:
        self.metrics = SessionMetrics()

    def update_metrics(
        self,
        dt: float,
        speed: float,
        tracked: bool,
        lane_changed: bool,
        jumped: bool,
        duck_hold: bool,
        coins_gained: int,
    ) -> None:
        metrics = self.metrics
        metrics.elapsed_seconds += dt
        metrics.progress = _clamp01(metrics.elapsed_seconds / self.session_target_seconds)

        # Intensity decays passively and rises from body movement events.
        metrics.intensity = _clamp01(metrics.intensity - (dt * 0.22))
        if tracked:
            metrics.intensity = _clamp01(metrics.intensity + (0.06 * dt))
        if lane_changed:
            metrics.intensity = _clamp01(metrics.intensity + 0.18)
        if jumped:
            metrics.intensity = _clamp01(metrics.intensity + 0.22)
        if duck_hold:
            metrics.intensity = _clamp01(metrics.intensity + (0.08 * dt))

        if coins_gained > 0:
            metrics.combo = min(999, metrics.combo + coins_gained)
            metrics._combo_decay_timer = 0.0
            metrics.calories += coins_gained * 0.22
        else:
            metrics._combo_decay_timer += dt
            if metrics._combo_decay_timer > 2.2:
                metrics.combo = max(0, metrics.combo - 1)
                metrics._combo_decay_timer = 1.7

        # Passive calorie burn scales with movement intensity and pace.
        pace_factor = min(1.0, speed / 16.0)
        burn_rate = 0.06 + (metrics.intensity * 0.22) + (pace_factor * 0.05)
        metrics.calories += burn_rate * dt

    def reset_combo(self) -> None:
        self.metrics.combo = 0
        self.metrics._combo_decay_timer = 0.0

    def formatted_timer(self) -> str:
        total = max(0, int(self.metrics.elapsed_seconds))
        minutes = total // 60
        seconds = total % 60
        return f"{minutes:02}:{seconds:02}"
