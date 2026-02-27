from __future__ import annotations

import math

import pygame

from config.modes import MODES
from core.mode_manager import ModeManager

MODE_SPEED_BONUS = {
    "kids": 4.0,
    "elderly": 1.7,
    "disabled_leg": 2.8,
    "disabled_hand": 2.3,
}


class ModeSelectScreen:
    def __init__(self, mode_keys: list[str]) -> None:
        self.mode_manager = ModeManager(mode_keys)
        self._card_rects: list[pygame.Rect] = []

    @property
    def selected_index(self) -> int:
        return self.mode_manager.selected_index

    @selected_index.setter
    def selected_index(self, value: int) -> None:
        self.mode_manager.selected_index = max(0, min(len(self.mode_manager.mode_keys) - 1, int(value)))

    def current_mode_key(self) -> str:
        return self.mode_manager.current_mode_key()

    def move_selection(self, delta: int) -> None:
        self.mode_manager.move_selection(delta)

    def select_by_number(self, number: int) -> None:
        self.mode_manager.select_by_number(number)

    def update(self, dt: float, events: list[pygame.event.Event]) -> None:
        surface = pygame.display.get_surface()
        if surface is None:
            return
        mouse_pos = pygame.mouse.get_pos()
        self._card_rects = self._build_card_rects(
            surface.get_width(),
            surface.get_height(),
        )
        self.mode_manager.update(dt, mouse_pos, self._card_rects)

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.mode_manager.click_select(event.pos, self._card_rects)

    def draw(
        self,
        screen: pygame.Surface,
        font_title: pygame.font.Font,
        font_ui: pygame.font.Font,
        font_body: pygame.font.Font,
    ) -> None:
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((4, 10, 28, 184))
        screen.blit(overlay, (0, 0))

        self._draw_city_haze(screen)

        center_x = screen.get_width() // 2
        center_y = screen.get_height() // 2

        title = font_title.render("Mode Selection", True, (226, 248, 255))
        screen.blit(title, title.get_rect(center=(center_x, center_y - 260)))

        sub = font_body.render("Pick a gesture profile for this session", True, (175, 219, 255))
        screen.blit(sub, sub.get_rect(center=(center_x, center_y - 216)))

        self._card_rects = self._build_card_rects(screen.get_width(), screen.get_height())
        card_title_font = pygame.font.SysFont("segoe ui", 24, bold=True)
        card_body_font = pygame.font.SysFont("segoe ui", 18)
        card_meta_font = pygame.font.SysFont("segoe ui", 16)
        for index, panel in enumerate(self._card_rects):
            style = self.mode_manager.style_for_index(index)
            selected = index == self.mode_manager.selected_index
            hovered = index == self.mode_manager.hover_index

            float_offset = int(math.sin(self.mode_manager.float_time * 2.0 + (index * 0.7)) * 6.0)
            draw_rect = panel.move(0, float_offset)
            scale = 1.08 if selected else (1.04 if hovered else 1.0)
            draw_rect = self._scaled_rect(draw_rect, scale)

            self._draw_card(screen, draw_rect, style.accent, selected, hovered)

            mode = MODES[style.mode_key]
            top_speed = mode.speed + MODE_SPEED_BONUS.get(mode.gesture_profile, 2.5)
            content_x = draw_rect.x + 14
            content_y = draw_rect.y + 10
            content_w = draw_rect.width - 28
            content_bottom = draw_rect.bottom - 10

            title_line = self._truncate_text(f"{index + 1}. {style.title}", card_title_font, content_w)
            title_text = card_title_font.render(title_line, True, (233, 250, 255))
            screen.blit(title_text, (content_x, content_y))
            content_y += title_text.get_height() + 6

            subtitle_lines = self._wrap_text(style.subtitle, card_body_font, content_w, max_lines=2)
            for line in subtitle_lines:
                if content_y + card_body_font.get_height() > content_bottom:
                    break
                screen.blit(card_body_font.render(line, True, (196, 230, 255)), (content_x, content_y))
                content_y += card_body_font.get_height() + 2

            detail_lines = self._wrap_text(style.detail, card_meta_font, content_w, max_lines=2)
            for line in detail_lines:
                if content_y + card_meta_font.get_height() > content_bottom:
                    break
                screen.blit(card_meta_font.render(line, True, (179, 218, 248)), (content_x, content_y))
                content_y += card_meta_font.get_height() + 2

            speed_line = f"Speed {mode.speed:.1f}-{top_speed:.1f} m/s | Spawn {mode.obstacle_spawn_rate:.2f}s"
            speed_lines = self._wrap_text(speed_line, card_meta_font, content_w, max_lines=2)
            for line in speed_lines:
                if content_y + card_meta_font.get_height() > content_bottom:
                    break
                screen.blit(card_meta_font.render(line, True, (162, 208, 246)), (content_x, content_y))
                content_y += card_meta_font.get_height() + 1

        hint = "Press 1-4 or Click to choose. ENTER for calibration."
        hint_text = font_body.render(hint, True, (232, 240, 255))
        screen.blit(hint_text, hint_text.get_rect(center=(center_x, center_y + 270)))

    def _build_card_rects(self, width: int, height: int) -> list[pygame.Rect]:
        card_w = 280
        card_h = 176
        gap_x = 44
        gap_y = 28
        start_x = (width // 2) - card_w - (gap_x // 2)
        start_y = (height // 2) - 138

        rects: list[pygame.Rect] = []
        for idx in range(4):
            col = idx % 2
            row = idx // 2
            x = start_x + col * (card_w + gap_x)
            y = start_y + row * (card_h + gap_y)
            rects.append(pygame.Rect(x, y, card_w, card_h))
        return rects

    def _draw_card(
        self,
        screen: pygame.Surface,
        rect: pygame.Rect,
        accent: tuple[int, int, int],
        selected: bool,
        hovered: bool,
    ) -> None:
        glow_alpha = 80 if selected else (56 if hovered else 30)
        glow = pygame.Surface((rect.width + 26, rect.height + 26), pygame.SRCALPHA)
        pygame.draw.rect(glow, (accent[0], accent[1], accent[2], glow_alpha), glow.get_rect(), border_radius=22, width=3)
        screen.blit(glow, (rect.x - 13, rect.y - 13))

        panel = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        fill_alpha = 198 if selected else 166
        panel.fill((0, 0, 0, 0))
        pygame.draw.rect(panel, (10, 22, 42, fill_alpha), panel.get_rect(), border_radius=16)
        border_color = accent if (selected or hovered) else (78, 124, 172)
        pygame.draw.rect(panel, border_color, panel.get_rect(), 2, border_radius=16)
        screen.blit(panel, rect.topleft)

    @staticmethod
    def _scaled_rect(rect: pygame.Rect, scale: float) -> pygame.Rect:
        width = int(rect.width * scale)
        height = int(rect.height * scale)
        return pygame.Rect(rect.centerx - (width // 2), rect.centery - (height // 2), width, height)

    @staticmethod
    def _draw_city_haze(screen: pygame.Surface) -> None:
        haze = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        base_y = int(screen.get_height() * 0.27)
        for idx in range(16):
            alpha = 12 + (idx * 2)
            row = pygame.Rect(0, base_y + (idx * 18), screen.get_width(), 26)
            pygame.draw.rect(haze, (24, 38, 74, alpha), row)
        screen.blit(haze, (0, 0))

    @staticmethod
    def _truncate_text(text: str, font: pygame.font.Font, max_width: int) -> str:
        if font.size(text)[0] <= max_width:
            return text
        if max_width <= 8:
            return ""
        ellipsis = "..."
        truncated = text
        while truncated and font.size(truncated + ellipsis)[0] > max_width:
            truncated = truncated[:-1]
        return (truncated + ellipsis) if truncated else ellipsis

    @classmethod
    def _wrap_text(
        cls,
        text: str,
        font: pygame.font.Font,
        max_width: int,
        max_lines: int,
    ) -> list[str]:
        words = text.split()
        if not words:
            return [""]

        lines: list[str] = []
        current = words[0]
        clipped = False
        for word in words[1:]:
            candidate = f"{current} {word}"
            if font.size(candidate)[0] <= max_width:
                current = candidate
            else:
                lines.append(current)
                current = word
                if len(lines) >= max_lines:
                    clipped = True
                    break

        if len(lines) < max_lines and current:
            lines.append(current)
        elif len(lines) >= max_lines:
            clipped = True

        if len(lines) > max_lines:
            lines = lines[:max_lines]
            clipped = True

        for idx, line in enumerate(lines):
            if font.size(line)[0] > max_width:
                lines[idx] = cls._truncate_text(line, font, max_width)

        if clipped and lines:
            lines[-1] = cls._truncate_text(f"{lines[-1]}...", font, max_width)
        return lines
