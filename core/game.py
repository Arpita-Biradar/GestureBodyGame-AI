from __future__ import annotations

from collections import defaultdict

import pygame

from config.modes import DEFAULT_MODE_KEY, MODES, MODE_ORDER, ModeConfig, get_mode_config
from controllers.base_controller import BaseController, MovementState
from controllers.hand_controller import HandController
from controllers.pose_controller import PoseController
from core.calibration_store import CalibrationStore
from core.level import FPS, HEIGHT, WIDTH, Level
from core.player import Player
from core.sound_manager import SoundManager
from screens.calibration_screen import CalibrationScreen
from screens.home_screen import HomeScreen
from screens.mode_select_screen import ModeSelectScreen


class Game:
    def __init__(self, mode_config: ModeConfig | None = None) -> None:
        pygame.init()
        pygame.display.set_caption("GesturePlay AI Runner")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()

        self.font_title = pygame.font.SysFont("segoe ui", 60, bold=True)
        self.font_prompt = pygame.font.SysFont("arial", 56, bold=True)
        self.font_ui = pygame.font.SysFont("arial", 32, bold=True)
        self.font_body = pygame.font.SysFont("segoe ui", 24)

        self.home_screen = HomeScreen()
        self.mode_select_screen = ModeSelectScreen(MODE_ORDER)
        self.calibration_screen = CalibrationScreen()
        self.sound_manager = SoundManager(enabled=False)
        self.calibration_store = CalibrationStore()

        self.mode_config = mode_config or MODES[DEFAULT_MODE_KEY]
        if self.mode_config.key in MODE_ORDER:
            self.mode_select_screen.selected_index = MODE_ORDER.index(self.mode_config.key)

        self.controller: BaseController | None = None
        self.player: Player | None = None
        self.level: Level | None = None
        self.menu_level = Level(MODES[DEFAULT_MODE_KEY])

        self.score = 0
        self.coin_count = 0
        self.best_score = 0
        self.elapsed = 0.0
        self.current_speed = self.mode_config.speed
        self.next_prompt = "RUN"
        self.controls = MovementState()
        self.camera_surface: pygame.Surface | None = None
        self.calibration_samples: list[dict[str, float]] = []
        self.calibration_target_samples = 45
        self.calibration_progress = 0.0
        self.calibration_status = "Hold a neutral position..."
        self.calibration_has_saved_profile = False

        self.state = "home" if mode_config is None else "playing"
        self._state_handlers = {
            "home": self._update_home,
            "mode_select": self._update_mode_select,
            "calibration": self._update_calibration,
            "playing": self._update_playing,
            "game_over": self._update_game_over,
        }

        if self.state == "playing":
            self._activate_mode(self.mode_config.key)

    def run(self) -> None:
        self.running = True
        try:
            while self.running:
                dt = self.clock.tick(FPS) / 1000.0
                events = pygame.event.get()

                if any(event.type == pygame.QUIT for event in events):
                    self.running = False
                    continue

                handler = self._state_handlers.get(self.state)
                if handler is not None:
                    handler(dt, events)

                self._draw_frame()
                pygame.display.flip()
        finally:
            self._release_controller()
            pygame.quit()

    def _activate_mode(self, mode_key: str) -> None:
        self.mode_config = get_mode_config(mode_key)
        self._release_controller()
        calibration_data = self.calibration_store.get_mode(mode_key)
        self.controller = self._build_controller(self.mode_config, calibration_data)
        self._reset_run()
        self.state = "playing"

    def _reset_run(self) -> None:
        self.player = Player()
        self.level = Level(self.mode_config)
        self.score = 0
        self.coin_count = 0
        self.elapsed = 0.0
        self.current_speed = self.mode_config.speed
        self.next_prompt = "RUN"
        self.controls = MovementState(message=f"{self.mode_config.label} active.")
        self.camera_surface = None

    def _build_controller(self, mode_config: ModeConfig, calibration_data: dict[str, float] | None = None) -> BaseController:
        if mode_config.control_type == "hand":
            return HandController(mode_config, calibration_data=calibration_data)
        return PoseController(mode_config, calibration_data=calibration_data)

    def _release_controller(self) -> None:
        if self.controller is not None:
            self.controller.release_resources()
            self.controller = None

    def _start_calibration_session(self, mode_key: str) -> None:
        self.mode_config = get_mode_config(mode_key)
        self._release_controller()
        saved_profile = self.calibration_store.get_mode(mode_key)
        self.calibration_has_saved_profile = bool(saved_profile)
        self.controller = self._build_controller(self.mode_config, saved_profile)
        self._reset_calibration_capture()
        self.state = "calibration"

    def _reset_calibration_capture(self) -> None:
        self.calibration_samples = []
        self.calibration_progress = 0.0
        self.calibration_status = "Hold a neutral position..."
        self.camera_surface = None

    def _finalize_calibration(self) -> None:
        if not self.calibration_samples:
            return

        totals: dict[str, float] = defaultdict(float)
        counts: dict[str, int] = defaultdict(int)
        for sample in self.calibration_samples:
            for key, value in sample.items():
                totals[key] += float(value)
                counts[key] += 1

        averaged = {
            key: totals[key] / counts[key]
            for key in totals
            if counts[key] > 0
        }
        self.calibration_store.save_mode(self.mode_config.key, averaged)
        self.calibration_has_saved_profile = True
        if self.controller is not None:
            self.controller.apply_calibration(averaged)

        self._reset_run()
        self.state = "playing"

    def _speed_for_time(self) -> float:
        profile_speed_bonus = {
            "kids": 6.6,
            "elderly": 2.6,
            "disabled_leg": 4.3,
            "disabled_hand": 4.0,
        }
        cap = profile_speed_bonus.get(self.mode_config.gesture_profile, 4.0)
        return self.mode_config.speed + min(cap, self.elapsed * 0.45)

    def _update_home(self, dt: float, events: list[pygame.event.Event]) -> None:
        self.menu_level.world_scroll += dt * 3.0
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.state = "mode_select"
                elif event.key == pygame.K_ESCAPE:
                    self.running = False

    def _update_mode_select(self, dt: float, events: list[pygame.event.Event]) -> None:
        self.menu_level.world_scroll += dt * 3.0
        for event in events:
            if event.type != pygame.KEYDOWN:
                continue
            if event.key in (pygame.K_UP, pygame.K_w):
                self.mode_select_screen.move_selection(-1)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.mode_select_screen.move_selection(1)
            elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
                key_to_number = {
                    pygame.K_1: 1,
                    pygame.K_2: 2,
                    pygame.K_3: 3,
                    pygame.K_4: 4,
                }
                self.mode_select_screen.select_by_number(key_to_number[event.key])
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._start_calibration_session(self.mode_select_screen.current_mode_key())
            elif event.key == pygame.K_ESCAPE:
                self.state = "home"

    def _update_calibration(self, _dt: float, events: list[pygame.event.Event]) -> None:
        for event in events:
            if event.type != pygame.KEYDOWN:
                continue
            if event.key == pygame.K_ESCAPE:
                self._release_controller()
                self.state = "mode_select"
                return
            if event.key == pygame.K_r:
                self._reset_calibration_capture()
            if event.key == pygame.K_s and self.calibration_has_saved_profile:
                self._reset_run()
                self.state = "playing"
                return

        if self.controller is None:
            self._start_calibration_session(self.mode_config.key)
            return

        sample, status_message, preview = self.controller.get_calibration_sample()
        self.camera_surface = preview
        self.calibration_status = status_message

        if sample is not None:
            self.calibration_samples.append(sample)

        self.calibration_progress = min(1.0, len(self.calibration_samples) / float(self.calibration_target_samples))
        if len(self.calibration_samples) >= self.calibration_target_samples:
            self._finalize_calibration()

    def _update_playing(self, dt: float, events: list[pygame.event.Event]) -> None:
        if self.controller is None or self.player is None or self.level is None:
            self._activate_mode(self.mode_config.key)
            return

        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self._release_controller()
                self.state = "mode_select"
                return

        self.controls, self.camera_surface = self.controller.get_movement()
        keys = pygame.key.get_pressed()

        self.elapsed += dt
        self.current_speed = self._speed_for_time()
        self.score += int(dt * (58 + (self.current_speed * 5.8)))

        if keys[pygame.K_LEFT]:
            self.player.set_lane(0)
        elif keys[pygame.K_RIGHT]:
            self.player.set_lane(2)
        elif self.controls.tracked:
            self.player.set_lane(self.controls.lane)

        if self.controls.jump or keys[pygame.K_UP]:
            self.player.jump()
            self.sound_manager.play("jump")

        duck_hold = self.controls.duck or keys[pygame.K_DOWN]
        self.player.update(dt, duck_hold, self.current_speed)
        self.level.update(dt, self.current_speed)

        if self.level.check_collision(self.player):
            self.best_score = max(self.best_score, self.score)
            self.state = "game_over"
            return

        coins_gained = self.level.collect_coins(self.player)
        if coins_gained:
            self.coin_count += coins_gained
            self.score += coins_gained * 25

        self.next_prompt = self.level.next_prompt()

    def _update_game_over(self, _dt: float, events: list[pygame.event.Event]) -> None:
        restart_requested = False
        menu_requested = False

        for event in events:
            if event.type != pygame.KEYDOWN:
                continue
            if event.key in (pygame.K_r, pygame.K_RETURN, pygame.K_SPACE):
                restart_requested = True
            elif event.key in (pygame.K_m, pygame.K_ESCAPE):
                menu_requested = True

        if self.controller is not None:
            self.controls, self.camera_surface = self.controller.get_movement()
            if self.controls.jump:
                restart_requested = True

        if restart_requested:
            self._reset_run()
            self.state = "playing"
            return
        if menu_requested:
            self._release_controller()
            self.state = "mode_select"

    def _draw_frame(self) -> None:
        if self.state in ("playing", "game_over") and self.level is not None and self.player is not None:
            self.level.draw(self.screen)
            self.player.draw(self.screen)
            self._draw_hud()
            if self.state == "game_over":
                self._draw_game_over_overlay()
        elif self.state == "calibration":
            self.menu_level.draw(self.screen)
            self.calibration_screen.draw(
                self.screen,
                self.font_title,
                self.font_ui,
                self.font_body,
                self.mode_config.key,
                self.mode_config.label,
                self.calibration_progress,
                self.calibration_status,
                self.camera_surface,
                self.calibration_has_saved_profile,
            )
        else:
            self.menu_level.draw(self.screen)
            if self.state == "home":
                self.home_screen.draw(self.screen, self.font_title, self.font_body, self.best_score)
            else:
                self.mode_select_screen.draw(self.screen, self.font_title, self.font_ui, self.font_body)

        pygame.draw.rect(
            self.screen,
            (8, 24, 58),
            pygame.Rect(8, 8, WIDTH - 16, HEIGHT - 16),
            4,
            border_radius=24,
        )

    def _draw_hud(self) -> None:
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

        mode_panel = pygame.Rect(18, 96, 420, 52)
        pygame.draw.rect(self.screen, (16, 36, 76), mode_panel, border_radius=12)
        mode_text = self.font_body.render(f"Mode: {self.mode_config.label}", True, (221, 237, 255))
        self.screen.blit(mode_text, (mode_panel.x + 12, mode_panel.y + 12))

        if self.camera_surface is not None:
            preview = pygame.transform.smoothscale(self.camera_surface, (250, 188))
            preview_rect = preview.get_rect(topright=(WIDTH - 18, 96))
            self.screen.blit(preview, preview_rect)
            pygame.draw.rect(self.screen, (255, 255, 255), preview_rect, 2, border_radius=8)

        state_text = self.font_ui.render(f"State: {self.player.state().upper()}", True, (238, 248, 255))
        self.screen.blit(state_text, (22, HEIGHT - 98))

        status_bar = pygame.Rect(20, HEIGHT - 54, WIDTH - 40, 34)
        pygame.draw.rect(self.screen, (20, 33, 64), status_bar, border_radius=10)
        status_text = self.font_body.render(self.controls.message, True, (225, 235, 255))
        self.screen.blit(status_text, (status_bar.x + 12, status_bar.y + 6))

    def _draw_game_over_overlay(self) -> None:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((8, 14, 32, 170))
        self.screen.blit(overlay, (0, 0))

        title = self.font_title.render("Game Over", True, (255, 255, 255))
        self.screen.blit(title, title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 122)))

        stats = [
            f"Mode: {self.mode_config.label}",
            f"Score: {self.score}",
            f"Coins: {self.coin_count}",
            f"Best: {self.best_score}",
            "Press R or jump gesture to restart",
            "Press M or ESC for mode select",
        ]
        for index, text in enumerate(stats):
            label = self.font_body.render(text, True, (232, 238, 255))
            self.screen.blit(label, label.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 36 + (index * 42))))
