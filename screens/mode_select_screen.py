from __future__ import annotations

import pygame

from config.modes import MODES


MODE_DESCRIPTIONS = {
    "kids": "Exaggerated body gestures with higher speed.",
    "elderly": "Calm yoga-style movements with smooth control.",
    "disabled_leg": "Hand-only control. Raise left/right/both hands.",
    "disabled_hand": "Pose-only control using shoulder tilt and body rise/squat.",
}


class ModeSelectScreen:
    def __init__(self, mode_keys: list[str]) -> None:
        self.mode_keys = mode_keys
        self.selected_index = 0

    def current_mode_key(self) -> str:
        return self.mode_keys[self.selected_index]

    def move_selection(self, delta: int) -> None:
        self.selected_index = (self.selected_index + delta) % len(self.mode_keys)

    def select_by_number(self, number: int) -> None:
        index = number - 1
        if 0 <= index < len(self.mode_keys):
            self.selected_index = index

    def draw(
        self,
        screen: pygame.Surface,
        font_title: pygame.font.Font,
        font_ui: pygame.font.Font,
        font_body: pygame.font.Font,
    ) -> None:
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((6, 14, 36, 186))
        screen.blit(overlay, (0, 0))

        center_x = screen.get_width() // 2
        center_y = screen.get_height() // 2

        title = font_title.render("Select Mode", True, (255, 255, 255))
        screen.blit(title, title.get_rect(center=(center_x, center_y - 190)))

        for index, mode_key in enumerate(self.mode_keys):
            mode = MODES[mode_key]
            selected = index == self.selected_index
            row_y = center_y - 74 + (index * 74)

            panel = pygame.Rect(center_x - 420, row_y - 26, 840, 56)
            fill = (27, 99, 222) if selected else (16, 35, 72)
            border = (202, 226, 255) if selected else (86, 124, 184)
            pygame.draw.rect(screen, fill, panel, border_radius=14)
            pygame.draw.rect(screen, border, panel, 2, border_radius=14)

            line = f"{index + 1}. {mode.label}"
            label = font_ui.render(line, True, (255, 255, 255))
            screen.blit(label, (panel.x + 18, panel.y + 12))

            info = MODE_DESCRIPTIONS.get(mode_key, "")
            info_text = font_body.render(info, True, (219, 232, 255))
            screen.blit(info_text, (panel.x + 290, panel.y + 15))

        hint = "UP/DOWN or 1-4 to choose, ENTER for calibration, ESC to go back"
        hint_text = font_body.render(hint, True, (232, 240, 255))
        screen.blit(hint_text, hint_text.get_rect(center=(center_x, center_y + 220)))
