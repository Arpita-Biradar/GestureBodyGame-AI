import random

import pygame

from pose.controller import BodyController, ControlState

from .config import FPS, HEIGHT, HORIZON_Y, PLAYER_Z, ROAD_HALF_WIDTH, WIDTH
from .entities import Coin, Obstacle, Player
from .geometry import lane_x, project_world


class RunnerGame:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Gesture Body Runner - 3D")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()

        self.font_title = pygame.font.SysFont("segoe ui", 60, bold=True)
        self.font_prompt = pygame.font.SysFont("arial", 56, bold=True)
        self.font_ui = pygame.font.SysFont("arial", 32, bold=True)
        self.font_body = pygame.font.SysFont("segoe ui", 24)

        self.background = self.build_background()
        self.body = BodyController()

        self.mode = "menu"
        self.best_score = 0

        self.reset_run()

    def reset_run(self) -> None:
        self.player = Player()
        self.obstacles: list[Obstacle] = []
        self.coins: list[Coin] = []

        self.score = 0
        self.coin_count = 0
        self.elapsed = 0.0
        self.speed = 11.5
        self.world_scroll = 0.0

        self.spawn_timer = 1.3
        self.coin_timer = 0.45
        self.next_prompt = "RUN"

    def build_background(self) -> pygame.Surface:
        surface = pygame.Surface((WIDTH, HEIGHT))

        for y in range(HEIGHT):
            t = y / max(1, HEIGHT - 1)
            if y < HORIZON_Y:
                k = y / max(1, HORIZON_Y)
                color = (
                    int(28 + (110 * k)),
                    int(94 + (120 * k)),
                    int(198 + (45 * k)),
                )
            else:
                k = (y - HORIZON_Y) / max(1, HEIGHT - HORIZON_Y)
                color = (
                    int(174 - (110 * k)),
                    int(208 - (128 * k)),
                    int(238 - (140 * k)),
                )
            pygame.draw.line(surface, color, (0, y), (WIDTH, y))

        for cx, cy, r in ((170, 92, 52), (410, 72, 45), (830, 84, 58), (1060, 70, 42)):
            pygame.draw.circle(surface, (255, 255, 255), (cx, cy), r)
            pygame.draw.circle(surface, (255, 255, 255), (cx + (r // 2), cy + 8), int(r * 0.66))
            pygame.draw.circle(surface, (255, 255, 255), (cx - (r // 2), cy + 12), int(r * 0.62))

        haze = pygame.Surface((WIDTH, 90), pygame.SRCALPHA)
        haze.fill((230, 244, 255, 82))
        surface.blit(haze, (0, HORIZON_Y - 6))

        return surface

    def draw_road(self) -> None:
        near_z = 2.35
        far_z = 74.0

        left_near = project_world(-ROAD_HALF_WIDTH, 0.0, near_z)
        right_near = project_world(ROAD_HALF_WIDTH, 0.0, near_z)
        left_far = project_world(-ROAD_HALF_WIDTH, 0.0, far_z)
        right_far = project_world(ROAD_HALF_WIDTH, 0.0, far_z)

        shoulder_width = ROAD_HALF_WIDTH + 1.45
        shoulder_left_near = project_world(-shoulder_width, 0.0, near_z)
        shoulder_right_near = project_world(shoulder_width, 0.0, near_z)
        shoulder_left_far = project_world(-shoulder_width, 0.0, far_z)
        shoulder_right_far = project_world(shoulder_width, 0.0, far_z)

        curb_drop = -0.16
        left_near_low = project_world(-ROAD_HALF_WIDTH, curb_drop, near_z)
        right_near_low = project_world(ROAD_HALF_WIDTH, curb_drop, near_z)
        left_far_low = project_world(-ROAD_HALF_WIDTH, curb_drop, far_z)
        right_far_low = project_world(ROAD_HALF_WIDTH, curb_drop, far_z)

        if (
            left_near is None
            or right_near is None
            or left_far is None
            or right_far is None
            or shoulder_left_near is None
            or shoulder_right_near is None
            or shoulder_left_far is None
            or shoulder_right_far is None
            or left_near_low is None
            or right_near_low is None
            or left_far_low is None
            or right_far_low is None
        ):
            return

        ln_x, ln_y, _ = left_near
        rn_x, rn_y, _ = right_near
        lf_x, lf_y, _ = left_far
        rf_x, rf_y, _ = right_far
        sln_x, sln_y, _ = shoulder_left_near
        srn_x, srn_y, _ = shoulder_right_near
        slf_x, slf_y, _ = shoulder_left_far
        srf_x, srf_y, _ = shoulder_right_far
        ln_low_x, ln_low_y, _ = left_near_low
        rn_low_x, rn_low_y, _ = right_near_low
        lf_low_x, lf_low_y, _ = left_far_low
        rf_low_x, rf_low_y, _ = right_far_low

        dirt_left = [
            (0, HEIGHT),
            (int(sln_x), int(sln_y)),
            (int(slf_x), int(slf_y)),
            (0, int(slf_y)),
        ]
        dirt_right = [
            (WIDTH, HEIGHT),
            (int(srn_x), int(srn_y)),
            (int(srf_x), int(srf_y)),
            (WIDTH, int(srf_y)),
        ]
        shoulder_left = [
            (int(sln_x), int(sln_y)),
            (int(ln_x), int(ln_y)),
            (int(lf_x), int(lf_y)),
            (int(slf_x), int(slf_y)),
        ]
        shoulder_right = [
            (int(rn_x), int(rn_y)),
            (int(srn_x), int(srn_y)),
            (int(srf_x), int(srf_y)),
            (int(rf_x), int(rf_y)),
        ]
        road_left_side = [
            (int(ln_x), int(ln_y)),
            (int(lf_x), int(lf_y)),
            (int(lf_low_x), int(lf_low_y)),
            (int(ln_low_x), int(ln_low_y)),
        ]
        road_right_side = [
            (int(rn_x), int(rn_y)),
            (int(rf_x), int(rf_y)),
            (int(rf_low_x), int(rf_low_y)),
            (int(rn_low_x), int(rn_low_y)),
        ]
        road_poly = [
            (int(ln_x), int(ln_y)),
            (int(rn_x), int(rn_y)),
            (int(rf_x), int(rf_y)),
            (int(lf_x), int(lf_y)),
        ]

        pygame.draw.polygon(self.screen, (192, 141, 96), dirt_left)
        pygame.draw.polygon(self.screen, (192, 141, 96), dirt_right)
        pygame.draw.polygon(self.screen, (144, 112, 80), shoulder_left)
        pygame.draw.polygon(self.screen, (144, 112, 80), shoulder_right)
        pygame.draw.polygon(self.screen, (38, 46, 68), road_left_side)
        pygame.draw.polygon(self.screen, (38, 46, 68), road_right_side)
        pygame.draw.polygon(self.screen, (67, 76, 102), road_poly)
        pygame.draw.polygon(self.screen, (37, 45, 67), road_poly, 3)

        pygame.draw.line(self.screen, (235, 214, 180), (int(ln_x), int(ln_y)), (int(lf_x), int(lf_y)), 4)
        pygame.draw.line(self.screen, (235, 214, 180), (int(rn_x), int(rn_y)), (int(rf_x), int(rf_y)), 4)

        center_strip_near_left = project_world(-0.25, 0.0, near_z)
        center_strip_near_right = project_world(0.25, 0.0, near_z)
        center_strip_far_left = project_world(-0.25, 0.0, far_z)
        center_strip_far_right = project_world(0.25, 0.0, far_z)
        if (
            center_strip_near_left is not None
            and center_strip_near_right is not None
            and center_strip_far_left is not None
            and center_strip_far_right is not None
        ):
            strip_poly = [
                (int(center_strip_near_left[0]), int(center_strip_near_left[1])),
                (int(center_strip_near_right[0]), int(center_strip_near_right[1])),
                (int(center_strip_far_right[0]), int(center_strip_far_right[1])),
                (int(center_strip_far_left[0]), int(center_strip_far_left[1])),
            ]
            pygame.draw.polygon(self.screen, (74, 85, 112), strip_poly)

        dash_spacing = 2.3
        dash_len = 1.1
        phase = self.world_scroll % dash_spacing
        for lane_divider in (-0.93, 0.93):
            z = near_z + phase
            while z < far_z:
                p0 = project_world(lane_divider, 0.0, z)
                p1 = project_world(lane_divider, 0.0, z + dash_len)
                if p0 is not None and p1 is not None:
                    x0, y0, s0 = p0
                    x1, y1, s1 = p1
                    width0 = max(2, int(s0 * 0.012))
                    width1 = max(1, int(s1 * 0.009))
                    poly = [
                        (int(x0 - width0), int(y0)),
                        (int(x0 + width0), int(y0)),
                        (int(x1 + width1), int(y1)),
                        (int(x1 - width1), int(y1)),
                    ]
                    pygame.draw.polygon(self.screen, (244, 244, 229), poly)
                z += dash_spacing

        rail_spacing = 3.2
        rail_phase = self.world_scroll % rail_spacing
        for side in (-1, 1):
            prev_top: tuple[float, float, float] | None = None
            prev_mid: tuple[float, float, float] | None = None
            z = near_z + rail_phase
            while z < far_z:
                x = side * (ROAD_HALF_WIDTH + 1.06)
                post_base = project_world(x, 0.0, z)
                post_mid = project_world(x, 0.42, z)
                post_top = project_world(x, 0.72, z)
                if post_base is not None and post_mid is not None and post_top is not None:
                    post_w = max(1, int(post_base[2] * 0.0048))
                    pygame.draw.line(
                        self.screen,
                        (196, 202, 216),
                        (int(post_base[0]), int(post_base[1])),
                        (int(post_top[0]), int(post_top[1])),
                        post_w,
                    )
                    if prev_top is not None and prev_mid is not None:
                        rail_w = max(1, int(((post_top[2] + prev_top[2]) * 0.5) * 0.0036))
                        pygame.draw.line(
                            self.screen,
                            (214, 222, 236),
                            (int(prev_top[0]), int(prev_top[1])),
                            (int(post_top[0]), int(post_top[1])),
                            rail_w,
                        )
                        pygame.draw.line(
                            self.screen,
                            (184, 192, 208),
                            (int(prev_mid[0]), int(prev_mid[1])),
                            (int(post_mid[0]), int(post_mid[1])),
                            rail_w,
                        )
                    prev_top = post_top
                    prev_mid = post_mid
                z += rail_spacing

    def draw_scenery(self) -> None:
        near_z = 5.0
        far_z = 70.0
        spacing = 3.8
        phase = self.world_scroll % spacing

        items: list[tuple[float, int, str]] = []
        z = near_z + phase
        idx = 0
        while z < far_z:
            items.append((z, idx, "building"))
            if idx % 2 == 0:
                items.append((z + 1.4, idx, "tree"))
            z += spacing
            idx += 1

        items.sort(reverse=True, key=lambda item: item[0])
        for z, idx, kind in items:
            for side in (-1, 1):
                x = side * (ROAD_HALF_WIDTH + 1.3 + ((idx % 3) * 0.55))
                if kind == "building":
                    self.draw_building(x, z, idx)
                else:
                    self.draw_tree(x, z)

    def draw_building(self, x: float, z: float, idx: int) -> None:
        half_w = 0.42 + ((idx % 3) * 0.08)
        height = 1.85 + ((idx % 4) * 0.34)
        depth = 0.9 + ((idx % 2) * 0.2)

        flb = project_world(x - half_w, 0.0, z)
        frb = project_world(x + half_w, 0.0, z)
        flt = project_world(x - half_w, height, z)
        frt = project_world(x + half_w, height, z)

        blb = project_world(x - half_w, 0.0, z + depth)
        brb = project_world(x + half_w, 0.0, z + depth)
        blt = project_world(x - half_w, height, z + depth)
        brt = project_world(x + half_w, height, z + depth)
        if (
            flb is None
            or frb is None
            or flt is None
            or frt is None
            or blb is None
            or brb is None
            or blt is None
            or brt is None
        ):
            return

        def pt(vertex: tuple[float, float, float]) -> tuple[int, int]:
            return int(vertex[0]), int(vertex[1])

        front_face = [pt(flb), pt(frb), pt(frt), pt(flt)]
        roof_face = [pt(flt), pt(frt), pt(brt), pt(blt)]
        if x < 0:
            side_face = [pt(frb), pt(brb), pt(brt), pt(frt)]
        else:
            side_face = [pt(flb), pt(blb), pt(blt), pt(flt)]

        base_color = (
            154 + ((idx % 4) * 8),
            112 + ((idx % 3) * 7),
            93 + ((idx % 2) * 10),
        )
        side_color = (
            max(0, base_color[0] - 28),
            max(0, base_color[1] - 28),
            max(0, base_color[2] - 24),
        )
        roof_color = (
            min(255, base_color[0] + 20),
            min(255, base_color[1] + 18),
            min(255, base_color[2] + 16),
        )

        pygame.draw.polygon(self.screen, roof_color, roof_face)
        pygame.draw.polygon(self.screen, side_color, side_face)
        pygame.draw.polygon(self.screen, base_color, front_face)
        pygame.draw.polygon(self.screen, (205, 170, 146), front_face, 1)

        front_min_x = int(min(flb[0], frb[0], flt[0], frt[0]))
        front_max_x = int(max(flb[0], frb[0], flt[0], frt[0]))
        front_top = int(min(flt[1], frt[1]))
        front_bottom = int(max(flb[1], frb[1]))
        face_w = front_max_x - front_min_x
        face_h = front_bottom - front_top
        if face_w > 10 and face_h > 20:
            win_w = max(2, face_w // 6)
            win_h = max(3, face_h // 10)
            for r in range(1, 7):
                for c in range(1, 4):
                    wx = front_min_x + int((c / 4) * face_w) - (win_w // 2)
                    wy = front_top + int((r / 8) * face_h)
                    if wy + win_h >= front_bottom - 2:
                        continue
                    pygame.draw.rect(self.screen, (214, 233, 252), pygame.Rect(wx, wy, win_w, win_h), border_radius=2)

    def draw_tree(self, x: float, z: float) -> None:
        trunk_w = 0.1
        trunk_h = 0.82
        trunk_depth = 0.32

        tflb = project_world(x - trunk_w, 0.0, z)
        tfrb = project_world(x + trunk_w, 0.0, z)
        tflt = project_world(x - trunk_w, trunk_h, z)
        tfrt = project_world(x + trunk_w, trunk_h, z)
        tblb = project_world(x - trunk_w, 0.0, z + trunk_depth)
        tbrb = project_world(x + trunk_w, 0.0, z + trunk_depth)
        tblt = project_world(x - trunk_w, trunk_h, z + trunk_depth)
        tbrt = project_world(x + trunk_w, trunk_h, z + trunk_depth)
        if (
            tflb is None
            or tfrb is None
            or tflt is None
            or tfrt is None
            or tblb is None
            or tbrb is None
            or tblt is None
            or tbrt is None
        ):
            return

        def pt(vertex: tuple[float, float, float]) -> tuple[int, int]:
            return int(vertex[0]), int(vertex[1])

        trunk_front = [pt(tflb), pt(tfrb), pt(tfrt), pt(tflt)]
        if x < 0:
            trunk_side = [pt(tfrb), pt(tbrb), pt(tbrt), pt(tfrt)]
        else:
            trunk_side = [pt(tflb), pt(tblb), pt(tblt), pt(tflt)]
        pygame.draw.polygon(self.screen, (88, 62, 47), trunk_side)
        pygame.draw.polygon(self.screen, (124, 86, 58), trunk_front)

        crown_back = project_world(x + 0.04, 1.16, z + 0.32)
        crown_front = project_world(x - 0.02, 1.2, z + 0.08)
        crown_top = project_world(x, 1.46, z + 0.12)
        if crown_back is None or crown_front is None or crown_top is None:
            return

        back_radius = max(4, int(crown_back[2] * 0.13))
        front_radius = max(6, int(crown_front[2] * 0.19))
        top_radius = max(4, int(crown_top[2] * 0.12))

        pygame.draw.circle(self.screen, (56, 120, 58), (int(crown_back[0]), int(crown_back[1])), back_radius)
        pygame.draw.circle(self.screen, (74, 151, 72), (int(crown_front[0]), int(crown_front[1])), front_radius)
        pygame.draw.circle(self.screen, (102, 186, 93), (int(crown_top[0]), int(crown_top[1])), top_radius)
        pygame.draw.circle(
            self.screen,
            (134, 206, 118),
            (int(crown_front[0] - (front_radius * 0.35)), int(crown_front[1] - (front_radius * 0.35))),
            max(3, int(front_radius * 0.56)),
        )

    def update_prompt(self) -> None:
        ahead = [item for item in self.obstacles if item.z > PLAYER_Z]
        if not ahead:
            self.next_prompt = "RUN"
            return
        nearest = min(ahead, key=lambda item: item.z)
        self.next_prompt = "JUMP" if nearest.kind == "jump" else "DUCK"

    def hits_obstacle(self, obstacle: Obstacle) -> bool:
        if abs(obstacle.z - PLAYER_Z) > 0.44:
            return False
        if abs(self.player.x - lane_x(obstacle.lane)) > 0.58:
            return False
        if obstacle.kind == "jump":
            return self.player.y < 0.57
        return not self.player.ducking

    def takes_coin(self, coin: Coin) -> bool:
        if abs(coin.z - PLAYER_Z) > 0.48:
            return False
        if abs(self.player.x - lane_x(coin.lane)) > 0.62:
            return False
        return True

    def update_playing(
        self,
        dt: float,
        controls: ControlState,
        keys: pygame.key.ScancodeWrapper,
    ) -> None:
        self.elapsed += dt
        self.speed = 11.5 + min(7.5, self.elapsed * 0.55)
        self.world_scroll += self.speed * dt
        self.score += int(dt * (58 + (self.speed * 5.8)))

        if keys[pygame.K_LEFT]:
            self.player.set_lane(0)
        elif keys[pygame.K_RIGHT]:
            self.player.set_lane(2)
        elif controls.tracked:
            self.player.set_lane(controls.lane)

        if controls.jump or keys[pygame.K_UP]:
            self.player.jump()

        duck_hold = controls.duck or keys[pygame.K_DOWN]
        self.player.update(dt, duck_hold, self.speed)

        self.spawn_timer -= dt
        if self.spawn_timer <= 0.0:
            lane = random.randint(0, 2)
            kind = "duck" if random.random() < 0.35 else "jump"
            spawn_z = random.uniform(41.0, 56.0)
            self.obstacles.append(Obstacle(lane, kind, spawn_z))
            base_gap = max(0.72, 1.28 - (self.elapsed * 0.016))
            self.spawn_timer = base_gap + random.uniform(-0.08, 0.18)

        self.coin_timer -= dt
        if self.coin_timer <= 0.0:
            spawn_z = random.uniform(33.0, 57.0)
            self.coins.append(Coin(random.randint(0, 2), spawn_z, phase=random.uniform(0.0, 6.0)))
            self.coin_timer = random.uniform(0.22, 0.48)

        distance = self.speed * dt
        for obstacle in self.obstacles:
            obstacle.advance(distance)
        for coin in self.coins:
            coin.advance(distance)

        self.obstacles = [obstacle for obstacle in self.obstacles if obstacle.z > 0.55]
        self.coins = [coin for coin in self.coins if coin.z > 0.55]

        for obstacle in self.obstacles:
            if self.hits_obstacle(obstacle):
                self.best_score = max(self.best_score, self.score)
                self.mode = "game_over"
                return

        remaining: list[Coin] = []
        for coin in self.coins:
            if self.takes_coin(coin):
                self.coin_count += 1
                self.score += 25
            else:
                remaining.append(coin)
        self.coins = remaining

        self.update_prompt()

    def draw_hud(self, controls: ControlState, camera_surface: pygame.Surface | None) -> None:
        prompt_panel = pygame.Rect((WIDTH // 2) - 170, 22, 340, 84)
        pygame.draw.rect(self.screen, (27, 99, 222), prompt_panel, border_radius=20)
        pygame.draw.rect(self.screen, (191, 225, 255), prompt_panel, 3, border_radius=20)
        prompt_text = self.font_prompt.render(f"{self.next_prompt}!", True, (255, 255, 255))
        self.screen.blit(prompt_text, prompt_text.get_rect(center=(prompt_panel.centerx, prompt_panel.centery + 2)))

        score_panel = pygame.Rect(18, 18, 320, 66)
        pygame.draw.rect(self.screen, (16, 36, 76), score_panel, border_radius=16)
        score_text = self.font_ui.render(f"Score: {self.score}", True, (255, 255, 255))
        self.screen.blit(score_text, (score_panel.x + 18, score_panel.y + 16))

        coin_panel = pygame.Rect(WIDTH - 274, 18, 256, 66)
        pygame.draw.rect(self.screen, (16, 36, 76), coin_panel, border_radius=16)
        coin_text = self.font_ui.render(f"Coins: {self.coin_count}", True, (255, 255, 255))
        self.screen.blit(coin_text, (coin_panel.x + 18, coin_panel.y + 16))

        if camera_surface is not None:
            preview = pygame.transform.smoothscale(camera_surface, (250, 188))
            preview_rect = preview.get_rect(topright=(WIDTH - 18, 96))
            self.screen.blit(preview, preview_rect)
            pygame.draw.rect(self.screen, (255, 255, 255), preview_rect, 2, border_radius=8)

        state_text = self.font_ui.render(f"State: {self.player.state().upper()}", True, (238, 248, 255))
        self.screen.blit(state_text, (22, HEIGHT - 98))

        status_bar = pygame.Rect(20, HEIGHT - 54, WIDTH - 40, 34)
        pygame.draw.rect(self.screen, (20, 33, 64), status_bar, border_radius=10)
        status_text = self.font_body.render(controls.message, True, (225, 235, 255))
        self.screen.blit(status_text, (status_bar.x + 12, status_bar.y + 6))

    def draw_menu_overlay(self) -> None:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((8, 22, 42, 156))
        self.screen.blit(overlay, (0, 0))

        title = self.font_title.render("Gesture Body Runner 3D", True, (255, 255, 255))
        self.screen.blit(title, title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 164)))

        lines = [
            "3D track + depth-based gameplay",
            "Move left/right: lane",
            "Raise both hands: jump",
            "Move body down: duck",
            "Press SPACE or raise hands to start",
            "Keyboard fallback: left/right, up, down",
        ]

        for index, text in enumerate(lines):
            label = self.font_body.render(text, True, (230, 240, 255))
            self.screen.blit(label, label.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 46 + (index * 42))))

    def draw_game_over_overlay(self) -> None:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((8, 14, 32, 170))
        self.screen.blit(overlay, (0, 0))

        title = self.font_title.render("Game Over", True, (255, 255, 255))
        self.screen.blit(title, title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 122)))

        stats = [
            f"Score: {self.score}",
            f"Coins: {self.coin_count}",
            f"Best: {self.best_score}",
            "Press R or raise hands to restart",
            "Press M for menu",
        ]

        for index, text in enumerate(stats):
            label = self.font_body.render(text, True, (232, 238, 255))
            self.screen.blit(label, label.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 36 + (index * 42))))

    def draw_frame(self, controls: ControlState, camera_surface: pygame.Surface | None) -> None:
        self.screen.blit(self.background, (0, 0))
        self.draw_road()
        self.draw_scenery()

        for coin in sorted(self.coins, key=lambda item: item.z, reverse=True):
            coin.draw(self.screen)
        for obstacle in sorted(self.obstacles, key=lambda item: item.z, reverse=True):
            obstacle.draw(self.screen)

        self.player.draw(self.screen)
        self.draw_hud(controls, camera_surface)

        if self.mode == "menu":
            self.draw_menu_overlay()
        elif self.mode == "game_over":
            self.draw_game_over_overlay()

        pygame.draw.rect(self.screen, (8, 24, 58), pygame.Rect(8, 8, WIDTH - 16, HEIGHT - 16), 4, border_radius=24)

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
