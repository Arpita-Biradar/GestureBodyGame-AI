from __future__ import annotations

import time

import cv2
import mediapipe as mp
import pygame

from controllers.base_controller import BaseController, MovementState


class HandController(BaseController):
    def __init__(
        self,
        mode_config,
        camera_index: int = 0,
        calibration_data: dict[str, float] | None = None,
    ) -> None:
        super().__init__(mode_config, camera_index)

        self.cap = cv2.VideoCapture(camera_index)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        self.mp_hands = mp.solutions.hands
        self.mp_draw = mp.solutions.drawing_utils
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            model_complexity=0,
            max_num_hands=2,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self.last_jump_time = 0.0
        self.left_hand_rest_y: float | None = None
        self.right_hand_rest_y: float | None = None
        self.apply_calibration(calibration_data)

    def get_movement(self) -> tuple[MovementState, pygame.Surface | None]:
        state = MovementState(
            message="Disabled Leg Mode: raise left/right hand to move, both hands up to jump.",
        )

        frame, results, status_message = self._read_hand_results()
        if frame is None:
            state.message = status_message
            return state, None

        left_raised = False
        right_raised = False

        if results.multi_hand_landmarks and results.multi_handedness:
            sensitivity = max(0.6, self.mode_config.movement_sensitivity)
            default_raise_threshold = 0.45 + ((sensitivity - 1.0) * 0.05)
            raise_margin = 0.13 / sensitivity
            left_raise_threshold = (
                max(0.12, self.left_hand_rest_y - raise_margin)
                if self.left_hand_rest_y is not None
                else default_raise_threshold
            )
            right_raise_threshold = (
                max(0.12, self.right_hand_rest_y - raise_margin)
                if self.right_hand_rest_y is not None
                else default_raise_threshold
            )

            for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                label = handedness.classification[0].label.lower()
                wrist = hand_landmarks.landmark[self.mp_hands.HandLandmark.WRIST]
                index_mcp = hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_MCP]
                # Disabled Leg mode: classify each hand as "raised" from normalized Y.
                if label == "left":
                    raised = wrist.y < left_raise_threshold and index_mcp.y < (left_raise_threshold + 0.08)
                    left_raised = left_raised or raised
                elif label == "right":
                    raised = wrist.y < right_raise_threshold and index_mcp.y < (right_raise_threshold + 0.08)
                    right_raised = right_raised or raised

                self.mp_draw.draw_landmarks(
                    frame,
                    hand_landmarks,
                    self.mp_hands.HAND_CONNECTIONS,
                )

        if left_raised or right_raised:
            state.tracked = True
            if left_raised and right_raised:
                state.lane = 1
                state.jump = self._trigger_jump()
            elif left_raised:
                state.lane = 0
            elif right_raised:
                state.lane = 2
        else:
            state.message = "Disabled Leg Mode: show one or both hands clearly in frame."

        camera_surface = self._to_pygame_surface(frame)
        return state, camera_surface

    def release_resources(self) -> None:
        if self.cap.isOpened():
            self.cap.release()
        self.hands.close()

    def get_calibration_sample(self) -> tuple[dict[str, float] | None, str, pygame.Surface | None]:
        frame, results, status_message = self._read_hand_results()
        if frame is None:
            return None, status_message, None

        if not (results.multi_hand_landmarks and results.multi_handedness):
            message = "Show both hands at comfortable neutral height."
            return None, message, self._to_pygame_surface(frame)

        left_y = None
        right_y = None
        for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
            wrist = hand_landmarks.landmark[self.mp_hands.HandLandmark.WRIST]
            label = handedness.classification[0].label.lower()
            if label == "left":
                left_y = wrist.y
            elif label == "right":
                right_y = wrist.y
            self.mp_draw.draw_landmarks(frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)

        preview = self._to_pygame_surface(frame)
        if left_y is None or right_y is None:
            return None, "Both left and right hands are needed for calibration.", preview

        sample = {
            "left_hand_rest_y": left_y,
            "right_hand_rest_y": right_y,
        }
        return sample, "Hold your hands steady...", preview

    def apply_calibration(self, calibration_data: dict[str, float] | None) -> None:
        if not calibration_data:
            return
        self.left_hand_rest_y = calibration_data.get("left_hand_rest_y", self.left_hand_rest_y)
        self.right_hand_rest_y = calibration_data.get("right_hand_rest_y", self.right_hand_rest_y)

    def _trigger_jump(self) -> bool:
        now = time.time()
        if (now - self.last_jump_time) >= self.mode_config.jump_cooldown:
            self.last_jump_time = now
            return True
        return False

    def _read_hand_results(self):
        if not self.cap.isOpened():
            return None, None, "Camera unavailable. Keyboard fallback: left/right + up/down."

        ok, frame = self.cap.read()
        if not ok:
            return None, None, "Camera frame unavailable. Keyboard fallback: left/right + up/down."

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb)
        return frame, results, "Show one or both hands in frame."

    def _to_pygame_surface(self, frame_bgr) -> pygame.Surface:
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        return pygame.image.frombuffer(
            frame_rgb.tobytes(),
            (frame_rgb.shape[1], frame_rgb.shape[0]),
            "RGB",
        ).copy()
