from __future__ import annotations

import time
from dataclasses import dataclass

import cv2
import mediapipe as mp
import pygame

from controllers.base_controller import BaseController, MovementState


@dataclass(slots=True)
class HandGestureInfo:
    wrist_x: float
    wrist_y: float
    extended_count: int
    is_open: bool
    is_fist: bool


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
        self.mp_pose = mp.solutions.pose
        self.mp_draw = mp.solutions.drawing_utils
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            model_complexity=0,
            max_num_hands=2,
            min_detection_confidence=0.40,
            min_tracking_confidence=0.40,
        )
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=0,
            smooth_landmarks=True,
            min_detection_confidence=0.40,
            min_tracking_confidence=0.40,
        )

        self.last_jump_time = 0.0
        self.left_hand_rest_y: float | None = None
        self.right_hand_rest_y: float | None = None

        self.left_open_hold_frames = 0
        self.right_open_hold_frames = 0
        self.both_open_hold_frames = 0
        self.both_fist_hold_frames = 0
        self.jump_hold_frames = 0
        self.jump_armed = True
        self.apply_calibration(calibration_data)

    def get_movement(self) -> tuple[MovementState, pygame.Surface | None]:
        state = MovementState(
            message=(
                "Leg-Free: LEFT OPEN=left lane, RIGHT OPEN=right lane, BOTH OPEN=center, "
                "BOTH FIST=duck, hands above shoulders=jump."
            ),
        )

        frame, hand_results, pose_results, status_message = self._read_tracking_results()
        if frame is None:
            state.message = status_message
            return state, None

        hands_by_side = self._extract_hands_by_screen_side(hand_results)
        left_hand = hands_by_side.get("left")
        right_hand = hands_by_side.get("right")

        left_open = left_hand is not None and left_hand.is_open
        right_open = right_hand is not None and right_hand.is_open
        left_fist = left_hand is not None and left_hand.is_fist
        right_fist = right_hand is not None and right_hand.is_fist

        only_left_open = left_open and right_hand is None
        only_right_open = right_open and left_hand is None
        both_open = left_open and right_open
        both_fist = left_fist and right_fist
        jump_pose = self._is_jump_pose(left_hand, right_hand, pose_results)

        self.left_open_hold_frames = self._step_hold(self.left_open_hold_frames, only_left_open)
        self.right_open_hold_frames = self._step_hold(self.right_open_hold_frames, only_right_open)
        self.both_open_hold_frames = self._step_hold(self.both_open_hold_frames, both_open)
        self.both_fist_hold_frames = self._step_hold(self.both_fist_hold_frames, both_fist)
        self.jump_hold_frames = self._step_hold(self.jump_hold_frames, jump_pose)

        if self.jump_hold_frames >= 2:
            state.tracked = True
            state.lane = 1
            if self.jump_armed:
                state.jump = self._trigger_jump()
            if state.jump:
                self.jump_armed = False
            state.message = "JUMP: both wrists above shoulder line."
        elif self.both_fist_hold_frames >= 2:
            state.tracked = True
            state.lane = 1
            state.duck = True
            state.message = "BOTH FIST detected: duck."
        elif self.left_open_hold_frames >= 2:
            state.tracked = True
            state.lane = 0
            state.message = "LEFT HAND OPEN detected: move left."
        elif self.right_open_hold_frames >= 2:
            state.tracked = True
            state.lane = 2
            state.message = "RIGHT HAND OPEN detected: move right."
        elif self.both_open_hold_frames >= 2:
            state.tracked = True
            state.lane = 1
            state.message = "BOTH HANDS OPEN detected: center lane."
        elif left_hand is not None or right_hand is not None:
            state.message = "Show open palm on left/right side. For jump, raise both wrists above shoulders."
        else:
            state.message = "Leg-Free: show one or both hands clearly in frame."

        if not jump_pose:
            self.jump_armed = True

        camera_surface = self._to_pygame_surface(frame)
        return state, camera_surface

    def release_resources(self) -> None:
        if self.cap.isOpened():
            self.cap.release()
        self.hands.close()
        self.pose.close()

    def get_calibration_sample(self) -> tuple[dict[str, float] | None, str, pygame.Surface | None]:
        frame, hand_results, _pose_results, status_message = self._read_tracking_results()
        if frame is None:
            return None, status_message, None

        hands = self._extract_hands_by_screen_side(hand_results)
        left_hand = hands.get("left")
        right_hand = hands.get("right")

        preview = self._to_pygame_surface(frame)
        if left_hand is None or right_hand is None:
            return None, "Show both hands at comfortable neutral height.", preview

        sample = {
            "left_hand_rest_y": left_hand.wrist_y,
            "right_hand_rest_y": right_hand.wrist_y,
        }
        return sample, "Hold your hands steady...", preview

    def apply_calibration(self, calibration_data: dict[str, float] | None) -> None:
        if not calibration_data:
            return
        left = calibration_data.get("left_hand_rest_y", self.left_hand_rest_y)
        right = calibration_data.get("right_hand_rest_y", self.right_hand_rest_y)
        if left is not None:
            self.left_hand_rest_y = min(0.82, max(0.36, float(left)))
        if right is not None:
            self.right_hand_rest_y = min(0.82, max(0.36, float(right)))

    def _trigger_jump(self) -> bool:
        now = time.time()
        if (now - self.last_jump_time) >= self.mode_config.jump_cooldown:
            self.last_jump_time = now
            return True
        return False

    def _read_tracking_results(self):
        if not self.cap.isOpened():
            return None, None, None, "Camera unavailable. Keyboard fallback: left/right + up/down."

        ok, frame = self.cap.read()
        if not ok:
            return None, None, None, "Camera frame unavailable. Keyboard fallback: left/right + up/down."

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        hand_results = self.hands.process(rgb)
        pose_results = self.pose.process(rgb)

        if hand_results.multi_hand_landmarks:
            for hand_landmarks in hand_results.multi_hand_landmarks:
                self.mp_draw.draw_landmarks(
                    frame,
                    hand_landmarks,
                    self.mp_hands.HAND_CONNECTIONS,
                )

        return frame, hand_results, pose_results, "Show one or both hands in frame."

    def _extract_hands_by_screen_side(self, hand_results) -> dict[str, HandGestureInfo]:
        if hand_results is None or not hand_results.multi_hand_landmarks:
            return {}

        by_side: dict[str, tuple[float, HandGestureInfo]] = {}
        for hand_landmarks in hand_results.multi_hand_landmarks:
            info = self._summarize_hand(hand_landmarks)
            side = "left" if info.wrist_x < 0.50 else "right"
            side_center_x = 0.25 if side == "left" else 0.75
            closeness = abs(info.wrist_x - side_center_x)

            existing = by_side.get(side)
            if existing is None:
                by_side[side] = (closeness, info)
                continue

            # Prefer clearer hand posture and then better side placement.
            existing_info = existing[1]
            better_posture = info.extended_count > existing_info.extended_count
            better_side_fit = closeness < existing[0]
            if better_posture or better_side_fit:
                by_side[side] = (closeness, info)

        return {side: entry[1] for side, entry in by_side.items()}

    def _summarize_hand(self, hand_landmarks) -> HandGestureInfo:
        landmarks = hand_landmarks.landmark
        wrist = landmarks[self.mp_hands.HandLandmark.WRIST]

        extended_count = 0
        finger_pairs = (
            (self.mp_hands.HandLandmark.INDEX_FINGER_TIP, self.mp_hands.HandLandmark.INDEX_FINGER_PIP),
            (self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP, self.mp_hands.HandLandmark.MIDDLE_FINGER_PIP),
            (self.mp_hands.HandLandmark.RING_FINGER_TIP, self.mp_hands.HandLandmark.RING_FINGER_PIP),
            (self.mp_hands.HandLandmark.PINKY_TIP, self.mp_hands.HandLandmark.PINKY_PIP),
        )

        for tip_lm, pip_lm in finger_pairs:
            tip = landmarks[tip_lm]
            pip = landmarks[pip_lm]
            if self._distance_sq(tip, wrist) > (self._distance_sq(pip, wrist) * 1.14):
                extended_count += 1

        thumb_tip = landmarks[self.mp_hands.HandLandmark.THUMB_TIP]
        thumb_ip = landmarks[self.mp_hands.HandLandmark.THUMB_IP]
        if self._distance_sq(thumb_tip, wrist) > (self._distance_sq(thumb_ip, wrist) * 1.12):
            extended_count += 1

        is_open = extended_count >= 3
        is_fist = extended_count <= 1

        return HandGestureInfo(
            wrist_x=wrist.x,
            wrist_y=wrist.y,
            extended_count=extended_count,
            is_open=is_open,
            is_fist=is_fist,
        )

    def _is_jump_pose(self, left_hand: HandGestureInfo | None, right_hand: HandGestureInfo | None, pose_results) -> bool:
        if left_hand is None or right_hand is None:
            return False
        if pose_results is None or pose_results.pose_landmarks is None:
            return False

        landmarks = pose_results.pose_landmarks.landmark
        left_shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value]
        right_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
        if left_shoulder.visibility < 0.20 or right_shoulder.visibility < 0.20:
            return False

        margin = 0.012
        return (
            left_hand.wrist_y < (left_shoulder.y - margin)
            and right_hand.wrist_y < (right_shoulder.y - margin)
        )

    @staticmethod
    def _step_hold(current: int, condition: bool) -> int:
        if condition:
            return min(8, current + 1)
        return max(0, current - 1)

    @staticmethod
    def _distance_sq(a, b) -> float:
        dx = a.x - b.x
        dy = a.y - b.y
        return (dx * dx) + (dy * dy)

    @staticmethod
    def _to_pygame_surface(frame_bgr) -> pygame.Surface:
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        return pygame.image.frombuffer(
            frame_rgb.tobytes(),
            (frame_rgb.shape[1], frame_rgb.shape[0]),
            "RGB",
        ).copy()
