from __future__ import annotations

import math

import pygame

from core.game_manager import SessionMetrics


class UIManager:
    def __init__(self) -> None:
        self._intensity_display = 0.0
        self._calories_display = 0.0
        self._progress_display = 0.0
        self._summary_pop: dict[str, float] = {}
        self._fade_alpha = 0.0
        self._stats_flash = 0.0

    def trigger_fade(self, alpha: float = 180.0) -> None:
        self._fade_alpha = max(self._fade_alpha, alpha)

    def update(self, dt: float) -> None:
        self._fade_alpha = max(0.0, self._fade_alpha - (dt * 420.0))
        self._stats_flash = max(0.0, self._stats_flash - dt)
        for key in list(self._summary_pop.keys()):
            self._summary_pop[key] = max(0.0, self._summary_pop[key] - dt)
            if self._summary_pop[key] <= 0.0:
                del self._summary_pop[key]

    def draw_hud(
        self,
        screen: pygame.Surface,
        font_prompt: pygame.font.Font,
        font_ui: pygame.font.Font,
        font_body: pygame.font.Font,
        font_small: pygame.font.Font,
        mode_label: str,
        score: int,
        coin_count: int,
        next_prompt: str,
        instruction: str,
        status_message: str,
        metrics: SessionMetrics,
        timer_text: str,
        current_speed: float,
        camera_surface: pygame.Surface | None,
    ) -> None:
        self._intensity_display += (metrics.intensity - self._intensity_display) * 0.15
        self._calories_display += (metrics.calories - self._calories_display) * 0.12
        self._progress_display += (metrics.progress - self._progress_display) * 0.18

        prompt_panel = pygame.Rect((screen.get_width() // 2) - 170, 18, 340, 74)
        self._draw_glass_panel(screen, prompt_panel, (80, 244, 255), (20, 36, 58), 164, 18)
        prompt_text = font_prompt.render(f"{next_prompt}!", True, (232, 255, 255))
        screen.blit(prompt_text, prompt_text.get_rect(center=(prompt_panel.centerx, prompt_panel.centery + 2)))

        top_right = pygame.Rect(screen.get_width() - 372, 20, 352, 208)
        self._draw_glass_panel(screen, top_right, (82, 247, 255), (10, 24, 42), 168, 20)

        combo_text = font_ui.render(f"Combo: {metrics.combo}", True, (228, 255, 255))
        coins_text = font_body.render(f"Coins: {coin_count}", True, (236, 249, 255))
        calories_text = font_body.render(f"Calories Burned: {self._calories_display:0.0f} kcal", True, (241, 249, 255))
        speed_text = font_body.render(f"Speed: {current_speed:0.1f} m/s", True, (225, 248, 255))
        timer_caption = font_small.render("Session Timer", True, (176, 224, 255))
        timer_value = font_ui.render(timer_text, True, (216, 248, 255))

        screen.blit(combo_text, (top_right.x + 20, top_right.y + 18))
        screen.blit(coins_text, (top_right.right - 150, top_right.y + 24))
        screen.blit(calories_text, (top_right.x + 20, top_right.y + 62))
        screen.blit(speed_text, (top_right.x + 20, top_right.y + 84))
        screen.blit(timer_caption, (top_right.x + 20, top_right.y + 162))
        screen.blit(timer_value, (top_right.right - 120, top_right.y + 152))

        intensity_label = font_small.render("Movement Intensity", True, (172, 227, 255))
        screen.blit(intensity_label, (top_right.x + 20, top_right.y + 112))
        bar_bg = pygame.Rect(top_right.x + 20, top_right.y + 136, top_right.width - 40, 14)
        pygame.draw.rect(screen, (16, 38, 58), bar_bg, border_radius=8)
        fill_width = int((bar_bg.width - 4) * max(0.0, min(1.0, self._intensity_display)))
        fill = pygame.Rect(bar_bg.x + 2, bar_bg.y + 2, fill_width, bar_bg.height - 4)
        pygame.draw.rect(screen, (72, 244, 255), fill, border_radius=7)
        pygame.draw.rect(screen, (198, 239, 255), bar_bg, 1, border_radius=8)

        bottom_panel = pygame.Rect(20, screen.get_height() - 118, screen.get_width() - 40, 98)
        self._draw_glass_panel(screen, bottom_panel, (109, 92, 255), (8, 18, 36), 172, 18)

        mode_text = font_ui.render(mode_label, True, (178, 223, 255))
        score_text = font_ui.render(f"Score: {score}", True, (236, 251, 255))
        screen.blit(mode_text, (bottom_panel.x + 18, bottom_panel.y + 10))
        screen.blit(score_text, (bottom_panel.right - 210, bottom_panel.y + 10))

        progress_bg = pygame.Rect(bottom_panel.x + 18, bottom_panel.y + 50, bottom_panel.width - 36, 10)
        pygame.draw.rect(screen, (18, 42, 66), progress_bg, border_radius=6)
        progress_fill_w = int((progress_bg.width - 4) * max(0.0, min(1.0, self._progress_display)))
        progress_fill = pygame.Rect(progress_bg.x + 2, progress_bg.y + 2, progress_fill_w, progress_bg.height - 4)
        pygame.draw.rect(screen, (118, 84, 255), progress_fill, border_radius=6)

        instruction_text = font_body.render(instruction, True, (222, 238, 255))
        screen.blit(instruction_text, (bottom_panel.x + 18, bottom_panel.y + 64))

        status_text = font_small.render(status_message, True, (186, 229, 255))
        screen.blit(status_text, (bottom_panel.x + 18, bottom_panel.y + 78))

        if camera_surface is not None:
            preview = pygame.transform.smoothscale(camera_surface, (220, 164))
            preview_rect = preview.get_rect(topleft=(20, 20))
            screen.blit(preview, preview_rect)
            pygame.draw.rect(screen, (82, 247, 255), preview_rect, 2, border_radius=10)

        self._draw_fade(screen)

    def draw_summary(
        self,
        screen: pygame.Surface,
        dt: float,
        mouse_pos: tuple[int, int],
        click: bool,
        font_title: pygame.font.Font,
        font_ui: pygame.font.Font,
        font_body: pygame.font.Font,
        mode_label: str,
        score: int,
        best_score: int,
        coin_count: int,
        metrics: SessionMetrics,
        timer_text: str,
    ) -> str | None:
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((5, 10, 30, 190))
        screen.blit(overlay, (0, 0))

        panel = pygame.Rect((screen.get_width() // 2) - 350, (screen.get_height() // 2) - 250, 700, 500)
        self._draw_glass_panel(screen, panel, (87, 238, 255), (10, 22, 42), 186, 24)

        flash_boost = int(30 * self._stats_flash)
        title = font_title.render("Session Summary", True, (214 + flash_boost, 249, 255))

        trophy_x = panel.x + 48
        trophy_y = panel.y + 34
        self._draw_trophy(screen, trophy_x, trophy_y)

        # Keep a safe horizontal gap between trophy art and title text.
        title_rect = title.get_rect(center=(panel.centerx, panel.y + 54))
        trophy_right = trophy_x + 108
        min_title_left = trophy_right + 18
        if title_rect.left < min_title_left:
            title_rect.left = min_title_left
        if title_rect.right > panel.right - 24:
            title_rect.right = panel.right - 24
        screen.blit(title, title_rect)

        lines = [
            f"Mode: {mode_label}",
            f"Score: {score}",
            f"Best Score: {best_score}",
            f"Coins Collected: {coin_count}",
            f"Calories Burned: {metrics.calories:0.0f} kcal",
            f"Session Time: {timer_text}",
        ]
        stats_x = panel.x + 164
        stats_top = panel.y + 122
        stats_width = panel.right - stats_x - 24
        line_gap = font_body.get_height() + 4
        for idx, text in enumerate(lines):
            safe_text = self._truncate_to_width(text, font_body, stats_width)
            label = font_body.render(safe_text, True, (228, 243, 255))
            screen.blit(label, (stats_x, stats_top + (idx * line_gap)))

        actions = [
            ("replay", "Replay", (84, 255, 136)),
            ("mode", "Change Mode", (88, 184, 255)),
            ("stats", "View Stats", (202, 110, 255)),
        ]
        clicked_action: str | None = None
        for idx, (key, label, color) in enumerate(actions):
            base = pygame.Rect(panel.x + 54 + (idx * 216), panel.bottom - 102, 196, 48)
            hovered = base.collidepoint(mouse_pos)
            if click and hovered:
                self._summary_pop[key] = 0.16
                clicked_action = key
                if key == "stats":
                    self._stats_flash = 0.35

            pop = self._summary_pop.get(key, 0.0)
            hover_scale = 1.05 if hovered else 1.0
            pop_scale = 1.0 + (0.08 * math.sin((0.16 - pop) * 18.0)) if pop > 0.0 else 1.0
            scale = hover_scale * pop_scale
            button_rect = self._scaled_rect(base, scale)

            self._draw_glass_panel(screen, button_rect, color, (12, 26, 44), 192, 12)
            text = font_ui.render(label, True, (237, 249, 255))
            screen.blit(text, text.get_rect(center=button_rect.center))

        hint = font_body.render("Enter/R: replay   M/Esc: mode select   Click buttons", True, (194, 227, 255))
        screen.blit(hint, hint.get_rect(center=(panel.centerx, panel.bottom - 16)))

        self._draw_fade(screen)
        return clicked_action

    def _draw_glass_panel(
        self,
        screen: pygame.Surface,
        rect: pygame.Rect,
        border_rgb: tuple[int, int, int],
        fill_rgb: tuple[int, int, int],
        fill_alpha: int,
        radius: int,
    ) -> None:
        glow_pad = 14
        glow = pygame.Surface((rect.width + (glow_pad * 2), rect.height + (glow_pad * 2)), pygame.SRCALPHA)
        pygame.draw.rect(
            glow,
            (border_rgb[0], border_rgb[1], border_rgb[2], 44),
            glow.get_rect(),
            width=3,
            border_radius=radius + 8,
        )
        screen.blit(glow, (rect.x - glow_pad, rect.y - glow_pad))

        panel = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        pygame.draw.rect(panel, (fill_rgb[0], fill_rgb[1], fill_rgb[2], fill_alpha), panel.get_rect(), border_radius=radius)
        pygame.draw.rect(panel, (border_rgb[0], border_rgb[1], border_rgb[2], 200), panel.get_rect(), 2, border_radius=radius)
        screen.blit(panel, rect.topleft)

    def _draw_trophy(self, screen: pygame.Surface, x: int, y: int) -> None:
        cup = pygame.Rect(x + 20, y + 18, 72, 54)
        pygame.draw.rect(screen, (255, 210, 72), cup, border_radius=18)
        pygame.draw.rect(screen, (255, 239, 136), cup, 2, border_radius=18)
        pygame.draw.circle(screen, (255, 196, 64), (x + 20, y + 45), 14, 4)
        pygame.draw.circle(screen, (255, 196, 64), (x + 92, y + 45), 14, 4)
        pygame.draw.rect(screen, (255, 196, 64), pygame.Rect(x + 49, y + 72, 14, 18), border_radius=4)
        pygame.draw.rect(screen, (182, 204, 255), pygame.Rect(x + 36, y + 90, 40, 12), border_radius=6)

    def _draw_fade(self, screen: pygame.Surface) -> None:
        if self._fade_alpha <= 0.5:
            return
        fade = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        fade.fill((0, 0, 0, int(self._fade_alpha)))
        screen.blit(fade, (0, 0))

    @staticmethod
    def _scaled_rect(rect: pygame.Rect, scale: float) -> pygame.Rect:
        width = max(8, int(rect.width * scale))
        height = max(8, int(rect.height * scale))
        return pygame.Rect(rect.centerx - (width // 2), rect.centery - (height // 2), width, height)

    @staticmethod
    def _truncate_to_width(text: str, font: pygame.font.Font, max_width: int) -> str:
        if font.size(text)[0] <= max_width:
            return text
        ellipsis = "..."
        clipped = text
        while clipped and font.size(clipped + ellipsis)[0] > max_width:
            clipped = clipped[:-1]
        return (clipped + ellipsis) if clipped else ellipsis
