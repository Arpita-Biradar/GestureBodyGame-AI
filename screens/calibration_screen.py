from __future__ import annotations

import pygame


CALIBRATION_HINTS = {
    "kids": "Stand centered with hands relaxed. Keep body visible and still.",
    "elderly": "Stand naturally and keep both hands visible near a comfortable rest position.",
    "disabled_leg": "Show both hands at comfortable neutral height, elbows relaxed.",
    "disabled_hand": "Stand upright with shoulders and hips visible, keep still briefly.",
}


class CalibrationScreen:
    def draw(
        self,
        screen: pygame.Surface,
        font_title: pygame.font.Font,
        font_ui: pygame.font.Font,
        font_body: pygame.font.Font,
        mode_key: str,
        mode_label: str,
        progress: float,
        status_message: str,
        camera_surface: pygame.Surface | None,
        has_saved_profile: bool,
    ) -> None:
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((8, 18, 40, 192))
        screen.blit(overlay, (0, 0))

        center_x = screen.get_width() // 2
        center_y = screen.get_height() // 2

        title = font_title.render(f"Calibrating: {mode_label}", True, (255, 255, 255))
        screen.blit(title, title.get_rect(center=(center_x, center_y - 235)))

        hint = CALIBRATION_HINTS.get(mode_key, "Hold a neutral position.")
        hint_text = font_body.render(hint, True, (225, 238, 255))
        screen.blit(hint_text, hint_text.get_rect(center=(center_x, center_y - 178)))

        bar_rect = pygame.Rect(center_x - 340, center_y - 130, 680, 34)
        pygame.draw.rect(screen, (20, 40, 82), bar_rect, border_radius=12)
        pygame.draw.rect(screen, (110, 160, 232), bar_rect, 2, border_radius=12)
        fill_w = int((bar_rect.width - 4) * max(0.0, min(1.0, progress)))
        fill_rect = pygame.Rect(bar_rect.x + 2, bar_rect.y + 2, fill_w, bar_rect.height - 4)
        pygame.draw.rect(screen, (32, 126, 238), fill_rect, border_radius=10)

        pct = int(progress * 100)
        progress_text = font_ui.render(f"Progress: {pct}%", True, (255, 255, 255))
        screen.blit(progress_text, progress_text.get_rect(center=(center_x, center_y - 82)))

        if camera_surface is not None:
            preview = pygame.transform.smoothscale(camera_surface, (480, 360))
            preview_rect = preview.get_rect(center=(center_x, center_y + 90))
            screen.blit(preview, preview_rect)
            pygame.draw.rect(screen, (214, 232, 255), preview_rect, 2, border_radius=10)

        status_text = font_body.render(status_message, True, (236, 243, 255))
        screen.blit(status_text, status_text.get_rect(center=(center_x, center_y + 306)))

        profile_line = "Saved profile found: press S to skip and use it." if has_saved_profile else "No saved profile yet for this mode."
        profile_text = font_body.render(profile_line, True, (220, 235, 255))
        screen.blit(profile_text, profile_text.get_rect(center=(center_x, center_y + 338)))

        controls = "R: restart capture   S: skip   ESC: back to mode select"
        controls_text = font_body.render(controls, True, (220, 235, 255))
        screen.blit(controls_text, controls_text.get_rect(center=(center_x, center_y + 368)))

