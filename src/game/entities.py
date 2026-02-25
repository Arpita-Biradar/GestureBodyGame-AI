from dataclasses import dataclass

import pygame

from .config import GROUND_Y, HORIZON_Y
from .geometry import clamp, depth_from_y, lane_x


@dataclass
class Obstacle:
    lane: int
    kind: str
    base_y: float

    def advance(self, distance: float) -> None:
        self.base_y += distance

    def rect(self) -> pygame.Rect:
        depth = depth_from_y(self.base_y)
        x = lane_x(self.lane, depth)

        if self.kind == "jump":
            width = int(40 + (62 * depth))
            height = int(30 + (58 * depth))
            return pygame.Rect(
                int(x - (width * 0.5)),
                int(self.base_y - height),
                width,
                height,
            )

        width = int(56 + (80 * depth))
        height = int(20 + (28 * depth))
        top = self.base_y - int(95 + (45 * depth))
        return pygame.Rect(int(x - (width * 0.5)), int(top), width, height)

    def draw(self, screen: pygame.Surface) -> None:
        rect = self.rect()
        if self.kind == "jump":
            pygame.draw.rect(screen, (245, 126, 81), rect, border_radius=10)
            pygame.draw.rect(screen, (255, 223, 178), rect, 3, border_radius=10)
        else:
            pygame.draw.rect(screen, (86, 164, 255), rect, border_radius=10)
            pygame.draw.rect(screen, (224, 243, 255), rect, 2, border_radius=10)


@dataclass
class Coin:
    lane: int
    base_y: float

    def advance(self, distance: float) -> None:
        self.base_y += distance

    def position_radius(self) -> tuple[int, int, int]:
        depth = depth_from_y(self.base_y)
        x = lane_x(self.lane, depth)
        y = self.base_y - int(80 + (30 * depth))
        radius = int(10 + (14 * depth))
        return int(x), int(y), radius

    def rect(self) -> pygame.Rect:
        x, y, radius = self.position_radius()
        return pygame.Rect(x - radius, y - radius, radius * 2, radius * 2)

    def draw(self, screen: pygame.Surface) -> None:
        x, y, radius = self.position_radius()
        pygame.draw.circle(screen, (249, 212, 58), (x, y), radius)
        pygame.draw.circle(screen, (255, 242, 172), (x, y), max(2, radius // 4))
        pygame.draw.circle(screen, (235, 163, 36), (x, y), radius, 2)


class Player:
    def __init__(self) -> None:
        self.target_lane = 1
        self.x = lane_x(self.target_lane, 1.0)
        self.foot_y = float(GROUND_Y)
        self.velocity_y = 0.0
        self.ducking = False

    def set_lane(self, lane: int) -> None:
        self.target_lane = int(clamp(lane, 0, 2))

    def jump(self) -> None:
        if self.on_ground():
            self.velocity_y = -980.0

    def on_ground(self) -> bool:
        return abs(self.foot_y - GROUND_Y) < 1.0 and self.velocity_y >= 0.0

    def update(self, dt: float, duck_hold: bool) -> None:
        target_x = lane_x(self.target_lane, 1.0)
        self.x += (target_x - self.x) * min(1.0, dt * 12.0)

        self.velocity_y += 2500.0 * dt
        self.foot_y += self.velocity_y * dt
        if self.foot_y > GROUND_Y:
            self.foot_y = float(GROUND_Y)
            self.velocity_y = 0.0

        self.ducking = duck_hold and self.on_ground()

    def rect(self) -> pygame.Rect:
        width = 76
        height = 74 if self.ducking else 124
        return pygame.Rect(
            int(self.x - (width * 0.5)),
            int(self.foot_y - height),
            width,
            height,
        )

    def draw(self, screen: pygame.Surface) -> None:
        body = self.rect()
        pygame.draw.rect(screen, (237, 84, 84), body, border_radius=16)
        pygame.draw.rect(screen, (255, 241, 241), body, 2, border_radius=16)

        if self.ducking:
            head_center = (body.centerx + 10, body.top + 12)
            head_radius = 11
        else:
            head_center = (body.centerx, body.top - 16)
            head_radius = 16
        pygame.draw.circle(screen, (255, 214, 181), head_center, head_radius)
        pygame.draw.circle(
            screen,
            (97, 66, 44),
            (head_center[0], head_center[1] - max(4, head_radius // 2)),
            max(4, head_radius // 2),
        )
