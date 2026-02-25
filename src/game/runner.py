import random

import pygame

from pose.controller import BodyController, ControlState

from .config import FPS, GROUND_Y, HEIGHT, HORIZON_Y, WIDTH
from .entities import Coin, Obstacle, Player
from .geometry import clamp


class RunnerGame:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Gesture Body Runner")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()

        self.font_title = pygame.font.SysFont("verdana", 62, bold=True)
        self.font_prompt = pygame.font.SysFont("verdana", 50, bold=True)
        self.font_ui = pygame.font.SysFont("verdana", 30, bold=True)
        self.font_body = pygame.font.SysFont("verdana", 24)

        self.background = self.build_background()
        self.body = BodyController()

        self.mode = "menu"
        self.best_score = 0
        self.road_phase = 0.0

        self.reset_run()

    def reset_run(self) -> None:
        self.player = Player()
        self.obstacles: list[Obstacle] = []
        self.coins: list[Coin] = []

        self.score = 0
        self.coin_count = 0
        self.elapsed = 0.0
        self.speed = 220.0

        self.spawn_timer = 1.5
        self.coin_timer = 0.7
        self.next_prompt = "RUN"

    def build_background(self) -> pygame.Surface:
        surface = pygame.Surface((WIDTH, HEIGHT))

        for y in range(HEIGHT):
            t = clamp(y / (HEIGHT * 0.75), 0.0, 1.0)
            color = (
                int(45 + ((176 - 45) * t)),
                int(124 + ((214 - 124) * t)),
                int(218 + ((252 - 218) * t)),
            )
            pygame.draw.line(surface, color, (0, y), (WIDTH, y))

        rng = random.Random(7)

        x = 0
        while x < int(WIDTH * 0.34):
            width = rng.randint(56, 118)
            height = rng.randint(130, 320)
            y = HORIZON_Y - height + 20
            color = (rng.randint(128, 188), rng.randint(88, 134), rng.randint(100, 166))
            pygame.draw.rect(surface, color, pygame.Rect(x, y, width, height), border_radius=6)
            for _ in range(8):
                win_x = x + rng.randint(6, max(8, width - 12))
                win_y = y + rng.randint(10, max(14, height - 18))
                pygame.draw.rect(
                    surface,
                    (241, 210, 153),
                    pygame.Rect(win_x, win_y, 6, 10),
                    border_radius=2,
                )
            x += width + rng.randint(3, 12)

        x = WIDTH
        while x > int(WIDTH * 0.66):
            width = rng.randint(56, 118)
            height = rng.randint(130, 320)
            x -= width
            y = HORIZON_Y - height + 20
            color = (rng.randint(128, 188), rng.randint(88, 134), rng.randint(100, 166))
            pygame.draw.rect(surface, color, pygame.Rect(x, y, width, height), border_radius=6)
            for _ in range(8):
                win_x = x + rng.randint(6, max(8, width - 12))
                win_y = y + rng.randint(10, max(14, height - 18))
                pygame.draw.rect(
                    surface,
                    (241, 210, 153),
                    pygame.Rect(win_x, win_y, 6, 10),
                    border_radius=2,
                )
            x -= rng.randint(3, 12)

        for index in range(12):
            tree_x = int(50 + (index * (WIDTH - 100) / 11))
            if tree_x < int(WIDTH * 0.34) or tree_x > int(WIDTH * 0.66):
                tree_y = HORIZON_Y + 34 + ((index % 3) * 18)
                pygame.draw.circle(surface, (88, 166, 92), (tree_x, tree_y), 34)
                pygame.draw.circle(surface, (120, 199, 106), (tree_x - 10, tree_y - 8), 22)
                pygame.draw.rect(surface, (118, 82, 58), pygame.Rect(tree_x - 4, tree_y + 18, 8, 24))

        return surface

    def draw_road(self) -> None:
        left_bottom = int(WIDTH * 0.24)
        right_bottom = int(WIDTH * 0.76)
        left_top = int(WIDTH * 0.44)
        right_top = int(WIDTH * 0.56)

        pygame.draw.polygon(
            self.screen,
            (214, 153, 102),
            [(0, HEIGHT), (left_bottom, HEIGHT), (left_top, HORIZON_Y), (0, HORIZON_Y + 45)],
        )
        pygame.draw.polygon(
            self.screen,
            (214, 153, 102),
            [(right_bottom, HEIGHT), (WIDTH, HEIGHT), (WIDTH, HORIZON_Y + 45), (right_top, HORIZON_Y)],
        )

        pygame.draw.polygon(
            self.screen,
            (57, 65, 92),
            [(left_bottom, HEIGHT), (right_bottom, HEIGHT), (right_top, HORIZON_Y), (left_top, HORIZON_Y)],
        )
        pygame.draw.polygon(
            self.screen,
            (39, 45, 67),
            [(left_bottom, HEIGHT), (right_bottom, HEIGHT), (right_top, HORIZON_Y), (left_top, HORIZON_Y)],
            3,
        )

        for split in (1, 2):
            for index in range(22):
                z = (index * 130 + self.road_phase * 500.0) % 2700.0
                t = z / 2700.0
                y = int(HORIZON_Y + (t * (HEIGHT - HORIZON_Y)))

                road_left = left_top + ((left_bottom - left_top) * t)
                road_right = right_top + ((right_bottom - right_top) * t)
                x = road_left + ((road_right - road_left) * (split / 3.0))

                dash_w = int(2 + (4 * t))
                dash_h = int(8 + (28 * t))
                pygame.draw.rect(
                    self.screen,
                    (245, 245, 229),
                    pygame.Rect(int(x - (dash_w * 0.5)), y, dash_w, dash_h),
                    border_radius=2,
                )

    def update_prompt(self) -> None:
        ahead = [obstacle for obstacle in self.obstacles if obstacle.base_y <= (GROUND_Y + 30)]
        if not ahead:
            self.next_prompt = "RUN"
            return

        nearest = max(ahead, key=lambda obstacle: obstacle.base_y)
        self.next_prompt = "JUMP" if nearest.kind == "jump" else "DUCK"

    def update_playing(
        self,
        dt: float,
        controls: ControlState,
        keys: pygame.key.ScancodeWrapper,
    ) -> None:
        self.elapsed += dt
        self.speed = 220.0 + min(140.0, self.elapsed * 6.0)
        self.road_phase = (self.road_phase + (dt * (self.speed / 260.0))) % 100.0

        self.score += int(dt * (70 + (self.speed * 0.07)))

        if keys[pygame.K_LEFT]:
            self.player.set_lane(0)
        elif keys[pygame.K_RIGHT]:
            self.player.set_lane(2)
        elif controls.tracked:
            self.player.set_lane(controls.lane)

        if controls.jump or keys[pygame.K_UP]:
            self.player.jump()

        duck_hold = controls.duck or keys[pygame.K_DOWN]
        self.player.update(dt, duck_hold)

        self.spawn_timer -= dt
        if self.spawn_timer <= 0.0:
            obstacle_lane = random.randint(0, 2)
            obstacle_kind = "duck" if random.random() < 0.35 else "jump"
            self.obstacles.append(Obstacle(obstacle_lane, obstacle_kind, HORIZON_Y - 48))

            base_gap = max(0.90, 1.55 - (self.elapsed * 0.008))
            self.spawn_timer = base_gap + random.uniform(-0.12, 0.18)

        self.coin_timer -= dt
        if self.coin_timer <= 0.0:
            self.coins.append(Coin(random.randint(0, 2), HORIZON_Y - 20))
            self.coin_timer = random.uniform(0.35, 0.90)

        scroll = self.speed * dt
        for obstacle in self.obstacles:
            obstacle.advance(scroll)
        for coin in self.coins:
            coin.advance(scroll)

        self.obstacles = [obstacle for obstacle in self.obstacles if obstacle.base_y < (HEIGHT + 150)]
        self.coins = [coin for coin in self.coins if coin.base_y < (HEIGHT + 150)]

        player_rect = self.player.rect()
        for obstacle in self.obstacles:
            if obstacle.rect().colliderect(player_rect):
                self.best_score = max(self.best_score, self.score)
                self.mode = "game_over"
                return

        remaining_coins = []
        for coin in self.coins:
            if coin.rect().colliderect(player_rect):
                self.coin_count += 1
                self.score += 25
            else:
                remaining_coins.append(coin)
        self.coins = remaining_coins

        self.update_prompt()

    def draw_hud(self, controls: ControlState, camera_surface: pygame.Surface | None) -> None:
        prompt_panel = pygame.Rect((WIDTH // 2) - 160, 24, 320, 84)
        pygame.draw.rect(self.screen, (42, 105, 220), prompt_panel, border_radius=20)
        pygame.draw.rect(self.screen, (186, 217, 255), prompt_panel, 3, border_radius=20)
        prompt_text = self.font_prompt.render(f"{self.next_prompt}!", True, (255, 255, 255))
        self.screen.blit(prompt_text, prompt_text.get_rect(center=prompt_panel.center))

        score_panel = pygame.Rect(20, 20, 300, 66)
        pygame.draw.rect(self.screen, (26, 42, 76), score_panel, border_radius=18)
        score_text = self.font_ui.render(f"Score: {self.score}", True, (255, 255, 255))
        self.screen.blit(score_text, (score_panel.x + 20, score_panel.y + 17))

        coin_panel = pygame.Rect(WIDTH - 260, 20, 240, 66)
        pygame.draw.rect(self.screen, (26, 42, 76), coin_panel, border_radius=18)
        coin_text = self.font_ui.render(f"Coins: {self.coin_count}", True, (255, 255, 255))
        self.screen.blit(coin_text, (coin_panel.x + 20, coin_panel.y + 17))

        if camera_surface is not None:
            preview = pygame.transform.smoothscale(camera_surface, (280, 210))
            preview_rect = preview.get_rect(topright=(WIDTH - 20, 100))
            self.screen.blit(preview, preview_rect)
            pygame.draw.rect(self.screen, (255, 255, 255), preview_rect, 2, border_radius=8)

        status_bar = pygame.Rect(20, HEIGHT - 54, WIDTH - 40, 34)
        pygame.draw.rect(self.screen, (20, 33, 64), status_bar, border_radius=10)
        status_text = self.font_body.render(controls.message, True, (225, 235, 255))
        self.screen.blit(status_text, (status_bar.x + 12, status_bar.y + 6))

    def draw_menu_overlay(self) -> None:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((8, 22, 42, 150))
        self.screen.blit(overlay, (0, 0))

        title = self.font_title.render("Gesture Body Runner", True, (255, 255, 255))
        self.screen.blit(title, title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 170)))

        lines = [
            "Body controls:",
            "Move body left/right: lane",
            "Raise both hands: jump",
            "Move body down: duck",
            "Press SPACE or raise hands to start",
            "Keyboard fallback: left/right, up, down",
        ]

        for index, text in enumerate(lines):
            label = self.font_body.render(text, True, (230, 240, 255))
            self.screen.blit(label, label.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 45 + (index * 44))))

    def draw_game_over_overlay(self) -> None:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((8, 14, 32, 165))
        self.screen.blit(overlay, (0, 0))

        title = self.font_title.render("Game Over", True, (255, 255, 255))
        self.screen.blit(title, title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 120)))

        stats = [
            f"Score: {self.score}",
            f"Coins: {self.coin_count}",
            f"Best: {self.best_score}",
            "Press R or raise hands to restart",
            "Press M for menu",
        ]

        for index, text in enumerate(stats):
            label = self.font_body.render(text, True, (232, 238, 255))
            self.screen.blit(label, label.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 35 + (index * 42))))

    def draw_frame(self, controls: ControlState, camera_surface: pygame.Surface | None) -> None:
        self.screen.blit(self.background, (0, 0))
        self.draw_road()

        for coin in sorted(self.coins, key=lambda item: item.base_y):
            coin.draw(self.screen)
        for obstacle in sorted(self.obstacles, key=lambda item: item.base_y):
            obstacle.draw(self.screen)

        self.player.draw(self.screen)
        self.draw_hud(controls, camera_surface)

        if self.mode == "menu":
            self.draw_menu_overlay()
        elif self.mode == "game_over":
            self.draw_game_over_overlay()

    def run(self) -> None:
        running = True
        try:
            while running:
                dt = self.clock.tick(FPS) / 1000.0
                controls, camera_surface = self.body.update()
                keys = pygame.key.get_pressed()

                start_pressed = False
                restart_pressed = False
                menu_pressed = False

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            running = False
                        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                            start_pressed = True
                        elif event.key == pygame.K_r:
                            restart_pressed = True
                        elif event.key == pygame.K_m:
                            menu_pressed = True

                if self.mode == "menu":
                    if start_pressed or controls.jump:
                        self.reset_run()
                        self.mode = "playing"
                elif self.mode == "playing":
                    self.update_playing(dt, controls, keys)
                elif self.mode == "game_over":
                    if restart_pressed or controls.jump:
                        self.reset_run()
                        self.mode = "playing"
                    elif menu_pressed:
                        self.mode = "menu"

                self.draw_frame(controls, camera_surface)
                pygame.display.flip()
        finally:
            self.body.close()
            pygame.quit()
