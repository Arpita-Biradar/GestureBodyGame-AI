from __future__ import annotations

import pygame


class HomeScreen:
    def draw(
        self,
        screen: pygame.Surface,
        font_title: pygame.font.Font,
        font_body: pygame.font.Font,
        best_score: int,
    ) -> None:
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((8, 20, 44, 160))
        screen.blit(overlay, (0, 0))

        center_x = screen.get_width() // 2
        center_y = screen.get_height() // 2

        title = font_title.render("GesturePlay AI Runner", True, (255, 255, 255))
        screen.blit(title, title.get_rect(center=(center_x, center_y - 170)))

        lines = [
            "Gesture-controlled runner with multi-mode accessibility",
            "Press ENTER or SPACE to open mode selection",
            "Keyboard fallback: LEFT/RIGHT to move, UP to jump, DOWN to duck",
            f"Best Score: {best_score}",
        ]

        for index, text in enumerate(lines):
            label = font_body.render(text, True, (229, 239, 255))
            screen.blit(label, label.get_rect(center=(center_x, center_y - 42 + (index * 44))))

