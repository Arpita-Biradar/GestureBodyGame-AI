from dataclasses import dataclass


@dataclass(frozen=True)
class ModeConfig:
    key: str
    label: str
    speed: float
    obstacle_spawn_rate: float
    control_type: str
    movement_sensitivity: float
    gesture_profile: str
    jump_cooldown: float = 0.5
    lane_smoothing: float = 0.2


MODES: dict[str, ModeConfig] = {
    "kids": ModeConfig(
        key="kids",
        label="Kids Mode",
        speed=11.6,
        obstacle_spawn_rate=1.02,
        control_type="pose",
        movement_sensitivity=1.18,
        gesture_profile="kids",
        jump_cooldown=0.45,
        lane_smoothing=0.30,
    ),
    "elderly": ModeConfig(
        key="elderly",
        label="Elderly Mode",
        speed=7.0,
        obstacle_spawn_rate=2.05,
        control_type="pose",
        movement_sensitivity=0.72,
        gesture_profile="elderly",
        jump_cooldown=0.80,
        lane_smoothing=0.14,
    ),
    "disabled_leg": ModeConfig(
        key="disabled_leg",
        label="Disabled Leg Mode",
        speed=9.3,
        obstacle_spawn_rate=1.46,
        control_type="hand",
        movement_sensitivity=1.0,
        gesture_profile="disabled_leg",
        jump_cooldown=0.55,
        lane_smoothing=0.22,
    ),
    "disabled_hand": ModeConfig(
        key="disabled_hand",
        label="Disabled Hand Mode",
        speed=8.7,
        obstacle_spawn_rate=1.58,
        control_type="pose",
        movement_sensitivity=1.10,
        gesture_profile="disabled_hand",
        jump_cooldown=0.55,
        lane_smoothing=0.22,
    ),
}

MODE_ORDER = ["kids", "elderly", "disabled_leg", "disabled_hand"]
DEFAULT_MODE_KEY = "kids"


def get_mode_config(mode_key: str) -> ModeConfig:
    return MODES.get(mode_key, MODES[DEFAULT_MODE_KEY])
