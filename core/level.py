from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

import pygame

from config.modes import ModeConfig

if TYPE_CHECKING:
    from core.player import Player


WIDTH = 1280
HEIGHT = 720
FPS = 30
HORIZON_Y = int(HEIGHT * 0.27)
GROUND_Y = HEIGHT - 68

CAMERA_HEIGHT = 1.45
PROJECTION_SCALE = 760.0
PLAYER_Z = 3.2
ROAD_HALF_WIDTH = 2.8
LANE_X = [-1.2, 0.0, 1.2]


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


@dataclass
class Obstacle:
    lane: int
    kind: str
    z: float

    def advance(self, distance: float) -> None:
        self.z -= distance

    def draw(self, screen: pygame.Surface) -> None:
        x_world = lane_x(self.lane)
        proj_ground = project_world(x_world, 0.0, self.z)
        if proj_ground is None:
            return
        sx, sy, scale = proj_ground

        if self.kind == "jump":
            width = max(12, int(scale * 0.70))
            height = max(10, int(scale * 0.35))
            rect = pygame.Rect(int(sx - (width * 0.5)), int(sy - height), width, height)
            pygame.draw.rect(screen, (237, 121, 72), rect, border_radius=8)
            pygame.draw.rect(screen, (255, 226, 188), rect, 2, border_radius=8)
            pygame.draw.rect(
                screen,
                (194, 86, 48),
                pygame.Rect(rect.x + 3, rect.bottom - max(6, height // 3), rect.width - 6, max(3, height // 5)),
                border_radius=4,
            )
        else:
            bar_y = project_world(x_world, 1.05, self.z)
            if bar_y is None:
                return
            _, bar_sy, _ = bar_y
            width = max(22, int(scale * 0.95))
            height = max(7, int(scale * 0.13))
            rect = pygame.Rect(int(sx - (width * 0.5)), int(bar_sy - (height * 0.5)), width, height)
            pygame.draw.rect(screen, (83, 158, 246), rect, border_radius=6)
            pygame.draw.rect(screen, (228, 245, 255), rect, 2, border_radius=6)


@dataclass
class Coin:
    lane: int
    z: float
    height: float = 0.75
    phase: float = 0.0

    def advance(self, distance: float) -> None:
        self.z -= distance

    def draw(self, screen: pygame.Surface) -> None:
        y = self.height + (math.sin(self.phase + (self.z * 0.35)) * 0.08)
        proj = project_world(lane_x(self.lane), y, self.z)
        if proj is None:
            return
        sx, sy, scale = proj
        radius = max(4, int(scale * 0.16))

        glow = pygame.Surface((radius * 5, radius * 5), pygame.SRCALPHA)
        center = glow.get_width() // 2
        pygame.draw.circle(glow, (255, 204, 58, 116), (center, center), int(radius * 1.6))
        pygame.draw.circle(glow, (255, 236, 133, 62), (center, center), int(radius * 2.0))
        screen.blit(glow, (int(sx - center), int(sy - center)))

        pygame.draw.circle(screen, (250, 198, 40), (int(sx), int(sy)), radius)
        pygame.draw.circle(screen, (255, 235, 128), (int(sx - (radius * 0.25)), int(sy - (radius * 0.25))), max(2, radius // 3))
        pygame.draw.circle(screen, (235, 151, 24), (int(sx), int(sy)), radius, max(1, radius // 6))


class Level:
    def __init__(self, mode_config: ModeConfig) -> None:
        self.mode_config = mode_config
        self.background = self._build_background()
        self.reset()

    def reset(self) -> None:
        self.obstacles: list[Obstacle] = []
        self.coins: list[Coin] = []
        self.elapsed = 0.0
        self.world_scroll = 0.0
        self.spawn_timer = self.mode_config.obstacle_spawn_rate
        self.coin_timer = 0.45

    def update(self, dt: float, speed: float) -> None:
        self.elapsed += dt
        self.world_scroll += speed * dt

        self.spawn_timer -= dt
        if self.spawn_timer <= 0.0:
            self._spawn_obstacle()
            jitter = random.uniform(-0.10, 0.18)
            min_gap = max(0.6, self.mode_config.obstacle_spawn_rate * 0.68)
            self.spawn_timer = max(min_gap, self.mode_config.obstacle_spawn_rate + jitter)

        self.coin_timer -= dt
        if self.coin_timer <= 0.0:
            self._spawn_coin()
            self.coin_timer = random.uniform(0.22, 0.48)

        distance = speed * dt
        for obstacle in self.obstacles:
            obstacle.advance(distance)
        for coin in self.coins:
            coin.advance(distance)

        self.obstacles = [obstacle for obstacle in self.obstacles if obstacle.z > 0.55]
        self.coins = [coin for coin in self.coins if coin.z > 0.55]

    def _spawn_obstacle(self) -> None:
        jump_bias = 0.65 if self.mode_config.gesture_profile == "kids" else 0.55
        kind = "jump" if random.random() < jump_bias else "duck"
        lane = random.randint(0, 2)
        spawn_z = random.uniform(41.0, 56.0)
        self.obstacles.append(Obstacle(lane, kind, spawn_z))

    def _spawn_coin(self) -> None:
        spawn_z = random.uniform(33.0, 57.0)
        self.coins.append(
            Coin(
                random.randint(0, 2),
                spawn_z,
                phase=random.uniform(0.0, 6.0),
            )
        )

    def hits_obstacle(self, player: Player, obstacle: Obstacle) -> bool:
        if abs(obstacle.z - PLAYER_Z) > 0.44:
            return False
        if abs(player.x - lane_x(obstacle.lane)) > 0.58:
            return False
        if obstacle.kind == "jump":
            return player.y < 0.57
        return not player.ducking

    def takes_coin(self, player: Player, coin: Coin) -> bool:
        if abs(coin.z - PLAYER_Z) > 0.48:
            return False
        if abs(player.x - lane_x(coin.lane)) > 0.62:
            return False
        return True

    def check_collision(self, player: Player) -> bool:
        return any(self.hits_obstacle(player, obstacle) for obstacle in self.obstacles)

    def collect_coins(self, player: Player) -> int:
        collected = 0
        remaining: list[Coin] = []
        for coin in self.coins:
            if self.takes_coin(player, coin):
                collected += 1
            else:
                remaining.append(coin)
        self.coins = remaining
        return collected

    def next_prompt(self) -> str:
        ahead = [item for item in self.obstacles if item.z > PLAYER_Z]
        if not ahead:
            return "RUN"
        nearest = min(ahead, key=lambda item: item.z)
        return "JUMP" if nearest.kind == "jump" else "DUCK"

    def draw(self, screen: pygame.Surface) -> None:
        screen.blit(self.background, (0, 0))
        self.draw_road(screen)
        self.draw_scenery(screen)

        for coin in sorted(self.coins, key=lambda item: item.z, reverse=True):
            coin.draw(screen)
        for obstacle in sorted(self.obstacles, key=lambda item: item.z, reverse=True):
            obstacle.draw(screen)

    def _build_background(self) -> pygame.Surface:
        surface = pygame.Surface((WIDTH, HEIGHT))
        for y in range(HEIGHT):
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

    def draw_road(self, screen: pygame.Surface) -> None:
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

        pygame.draw.polygon(screen, (192, 141, 96), dirt_left)
        pygame.draw.polygon(screen, (192, 141, 96), dirt_right)
        pygame.draw.polygon(screen, (144, 112, 80), shoulder_left)
        pygame.draw.polygon(screen, (144, 112, 80), shoulder_right)
        pygame.draw.polygon(screen, (38, 46, 68), road_left_side)
        pygame.draw.polygon(screen, (38, 46, 68), road_right_side)
        pygame.draw.polygon(screen, (67, 76, 102), road_poly)
        pygame.draw.polygon(screen, (37, 45, 67), road_poly, 3)

        pygame.draw.line(screen, (235, 214, 180), (int(ln_x), int(ln_y)), (int(lf_x), int(lf_y)), 4)
        pygame.draw.line(screen, (235, 214, 180), (int(rn_x), int(rn_y)), (int(rf_x), int(rf_y)), 4)

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
            pygame.draw.polygon(screen, (74, 85, 112), strip_poly)

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
                    pygame.draw.polygon(screen, (244, 244, 229), poly)
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
                        screen,
                        (196, 202, 216),
                        (int(post_base[0]), int(post_base[1])),
                        (int(post_top[0]), int(post_top[1])),
                        post_w,
                    )
                    if prev_top is not None and prev_mid is not None:
                        rail_w = max(1, int(((post_top[2] + prev_top[2]) * 0.5) * 0.0036))
                        pygame.draw.line(
                            screen,
                            (214, 222, 236),
                            (int(prev_top[0]), int(prev_top[1])),
                            (int(post_top[0]), int(post_top[1])),
                            rail_w,
                        )
                        pygame.draw.line(
                            screen,
                            (184, 192, 208),
                            (int(prev_mid[0]), int(prev_mid[1])),
                            (int(post_mid[0]), int(post_mid[1])),
                            rail_w,
                        )
                    prev_top = post_top
                    prev_mid = post_mid
                z += rail_spacing

    def draw_scenery(self, screen: pygame.Surface) -> None:
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
                    self._draw_building(screen, x, z, idx)
                else:
                    self._draw_tree(screen, x, z)

    def _draw_building(self, screen: pygame.Surface, x: float, z: float, idx: int) -> None:
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

        pygame.draw.polygon(screen, roof_color, roof_face)
        pygame.draw.polygon(screen, side_color, side_face)
        pygame.draw.polygon(screen, base_color, front_face)
        pygame.draw.polygon(screen, (205, 170, 146), front_face, 1)

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
                    pygame.draw.rect(screen, (214, 233, 252), pygame.Rect(wx, wy, win_w, win_h), border_radius=2)

    def _draw_tree(self, screen: pygame.Surface, x: float, z: float) -> None:
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
        pygame.draw.polygon(screen, (88, 62, 47), trunk_side)
        pygame.draw.polygon(screen, (124, 86, 58), trunk_front)

        crown_back = project_world(x + 0.04, 1.16, z + 0.32)
        crown_front = project_world(x - 0.02, 1.2, z + 0.08)
        crown_top = project_world(x, 1.46, z + 0.12)
        if crown_back is None or crown_front is None or crown_top is None:
            return

        back_radius = max(4, int(crown_back[2] * 0.13))
        front_radius = max(6, int(crown_front[2] * 0.19))
        top_radius = max(4, int(crown_top[2] * 0.12))
        pygame.draw.circle(screen, (56, 120, 58), (int(crown_back[0]), int(crown_back[1])), back_radius)
        pygame.draw.circle(screen, (74, 151, 72), (int(crown_front[0]), int(crown_front[1])), front_radius)
        pygame.draw.circle(screen, (102, 186, 93), (int(crown_top[0]), int(crown_top[1])), top_radius)
        pygame.draw.circle(
            screen,
            (134, 206, 118),
            (int(crown_front[0] - (front_radius * 0.35)), int(crown_front[1] - (front_radius * 0.35))),
            max(3, int(front_radius * 0.56)),
        )

