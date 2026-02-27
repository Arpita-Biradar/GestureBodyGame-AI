from __future__ import annotations

import time

import cv2
import mediapipe as mp
import pygame

from controllers.base_controller import BaseController, MovementState


class PoseController(BaseController):
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

        self.mp_pose = mp.solutions.pose
        self.mp_draw = mp.solutions.drawing_utils
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=0,
            smooth_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self.pose_landmark = self.mp_pose.PoseLandmark

        self.baseline_torso_x: float | None = None
        self.baseline_shoulder_y: float | None = None
        self.baseline_left_wrist_y: float | None = None
        self.baseline_right_wrist_y: float | None = None
        self.last_jump_time = 0.0
        self.smoothed_lane = 1.0
        self.elderly_jump_hold_frames = 0
        self.duck_filter = 0.0
        self.disabled_hand_jump_hold_frames = 0
        self.disabled_hand_jump_armed = True
        self.disabled_hand_duck_filter = 0.0

        self._handlers = {
            "kids": self._handle_kids_profile,
            "elderly": self._handle_elderly_profile,
            "disabled_hand": self._handle_disabled_hand_profile,
        }

        self._kids_required = [
            self.pose_landmark.NOSE.value,
            self.pose_landmark.LEFT_SHOULDER.value,
            self.pose_landmark.RIGHT_SHOULDER.value,
            self.pose_landmark.LEFT_WRIST.value,
            self.pose_landmark.RIGHT_WRIST.value,
            self.pose_landmark.LEFT_HIP.value,
            self.pose_landmark.RIGHT_HIP.value,
        ]
        self._elderly_required = self._kids_required
        self._disabled_hand_required = [
            self.pose_landmark.LEFT_SHOULDER.value,
            self.pose_landmark.RIGHT_SHOULDER.value,
            self.pose_landmark.LEFT_HIP.value,
            self.pose_landmark.RIGHT_HIP.value,
        ]

        self.apply_calibration(calibration_data)

    def get_movement(self) -> tuple[MovementState, pygame.Surface | None]:
        default_state = MovementState(
            message="No pose detected. Stand where shoulders and hips are visible.",
        )

        frame, landmarks, pose_landmarks, default_message = self._read_pose_landmarks()
        if frame is None:
            default_state.message = default_message
            return default_state, None

        if landmarks is None:
            default_state.message = default_message
            camera_surface = self._to_pygame_surface(frame)
            return default_state, camera_surface

        handler = self._handlers.get(self.mode_config.gesture_profile, self._handle_kids_profile)
        movement_state = handler(landmarks)

        self._draw_pose_landmarks(frame, pose_landmarks)
        camera_surface = self._to_pygame_surface(frame)
        return movement_state, camera_surface

    def release_resources(self) -> None:
        if self.cap.isOpened():
            self.cap.release()
        self.pose.close()

    def get_calibration_sample(self) -> tuple[dict[str, float] | None, str, pygame.Surface | None]:
        frame, landmarks, pose_landmarks, message = self._read_pose_landmarks()
        if frame is None:
            return None, message, None

        if landmarks is None:
            return None, "No pose detected. Stand naturally and keep torso visible.", self._to_pygame_surface(frame)

        self._draw_pose_landmarks(frame, pose_landmarks)
        preview = self._to_pygame_surface(frame)
        sample = self._extract_calibration_sample(landmarks)
        if sample is None:
            return None, message, preview
        return sample, "Hold still in a neutral position...", preview

    def apply_calibration(self, calibration_data: dict[str, float] | None) -> None:
        if not calibration_data:
            return
        self.baseline_torso_x = calibration_data.get("pose_baseline_torso_x", self.baseline_torso_x)
        self.baseline_shoulder_y = calibration_data.get("pose_baseline_shoulder_y", self.baseline_shoulder_y)
        self.baseline_left_wrist_y = calibration_data.get("pose_baseline_left_wrist_y", self.baseline_left_wrist_y)
        self.baseline_right_wrist_y = calibration_data.get("pose_baseline_right_wrist_y", self.baseline_right_wrist_y)
        smoothed_lane = calibration_data.get("smoothed_lane")
        if smoothed_lane is not None:
            self.smoothed_lane = float(smoothed_lane)

    def _to_pygame_surface(self, frame_bgr) -> pygame.Surface:
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        return pygame.image.frombuffer(
            frame_rgb.tobytes(),
            (frame_rgb.shape[1], frame_rgb.shape[0]),
            "RGB",
        ).copy()

    def _read_pose_landmarks(self):
        if not self.cap.isOpened():
            return None, None, None, "Camera unavailable. Keyboard fallback: left/right + up/down."

        ok, frame = self.cap.read()
        if not ok:
            return None, None, None, "Camera frame unavailable. Keyboard fallback: left/right + up/down."

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose.process(rgb)
        landmarks = results.pose_landmarks.landmark if results.pose_landmarks else None
        return frame, landmarks, results.pose_landmarks, "No pose detected. Stand where shoulders and hips are visible."

    def _draw_pose_landmarks(self, frame, pose_landmarks) -> None:
        if pose_landmarks is None:
            return
        self.mp_draw.draw_landmarks(
            frame,
            pose_landmarks,
            self.mp_pose.POSE_CONNECTIONS,
        )

    def _extract_calibration_sample(self, landmarks) -> dict[str, float] | None:
        profile = self.mode_config.gesture_profile
        if profile in ("kids", "elderly"):
            required = self._kids_required
            if not self._visibility_ok(landmarks, required):
                return None
            left_wrist = landmarks[self.pose_landmark.LEFT_WRIST.value]
            right_wrist = landmarks[self.pose_landmark.RIGHT_WRIST.value]
        elif profile == "disabled_hand":
            required = self._disabled_hand_required
            if not self._visibility_ok(landmarks, required):
                return None
            left_wrist = None
            right_wrist = None
        else:
            return None

        left_shoulder = landmarks[self.pose_landmark.LEFT_SHOULDER.value]
        right_shoulder = landmarks[self.pose_landmark.RIGHT_SHOULDER.value]
        left_hip = landmarks[self.pose_landmark.LEFT_HIP.value]
        right_hip = landmarks[self.pose_landmark.RIGHT_HIP.value]

        shoulder_mid_x = (left_shoulder.x + right_shoulder.x) * 0.5
        shoulder_mid_y = (left_shoulder.y + right_shoulder.y) * 0.5
        hip_mid_x = (left_hip.x + right_hip.x) * 0.5
        torso_mid_x = (shoulder_mid_x + hip_mid_x) * 0.5
        sample = {
            "pose_baseline_torso_x": torso_mid_x,
            "pose_baseline_shoulder_y": shoulder_mid_y,
            "smoothed_lane": 1.0,
        }
        if left_wrist is not None and right_wrist is not None:
            sample["pose_baseline_left_wrist_y"] = left_wrist.y
            sample["pose_baseline_right_wrist_y"] = right_wrist.y
        return sample

    def _visibility_ok(
        self,
        landmarks,
        indices: list[int],
        threshold: float = 0.45,
    ) -> bool:
        return all(landmarks[index].visibility > threshold for index in indices)

    def _smooth_lane(self, target_lane: int, smoothing: float | None = None) -> int:
        alpha = smoothing if smoothing is not None else self.mode_config.lane_smoothing
        self.smoothed_lane = (self.smoothed_lane * (1.0 - alpha)) + (target_lane * alpha)
        return max(0, min(2, int(round(self.smoothed_lane))))

    def _trigger_jump(self) -> bool:
        now = time.time()
        if (now - self.last_jump_time) >= self.mode_config.jump_cooldown:
            self.last_jump_time = now
            return True
        return False

    def _handle_kids_profile(self, landmarks) -> MovementState:
        if not self._visibility_ok(landmarks, self._kids_required):
            return MovementState(message="Kids Mode: keep nose, shoulders, wrists, and hips visible.")

        nose = landmarks[self.pose_landmark.NOSE.value]
        left_shoulder = landmarks[self.pose_landmark.LEFT_SHOULDER.value]
        right_shoulder = landmarks[self.pose_landmark.RIGHT_SHOULDER.value]
        left_wrist = landmarks[self.pose_landmark.LEFT_WRIST.value]
        right_wrist = landmarks[self.pose_landmark.RIGHT_WRIST.value]
        left_hip = landmarks[self.pose_landmark.LEFT_HIP.value]
        right_hip = landmarks[self.pose_landmark.RIGHT_HIP.value]

        sensitivity = max(0.55, self.mode_config.movement_sensitivity)
        shoulder_width = abs(right_shoulder.x - left_shoulder.x)
        shoulder_mid_x = (left_shoulder.x + right_shoulder.x) * 0.5
        shoulder_mid_y = (left_shoulder.y + right_shoulder.y) * 0.5
        hip_mid_x = (left_hip.x + right_hip.x) * 0.5
        torso_mid_x = (shoulder_mid_x + hip_mid_x) * 0.5

        if self.baseline_torso_x is None:
            self.baseline_torso_x = torso_mid_x
        if self.baseline_shoulder_y is None:
            self.baseline_shoulder_y = shoulder_mid_y

        # Kids mode expects larger, clear body-lean gestures for lane control.
        lean_threshold = max(0.03, shoulder_width * (0.31 / sensitivity))
        torso_delta = torso_mid_x - self.baseline_torso_x
        target_lane = 1
        if torso_delta < -lean_threshold:
            target_lane = 0
        elif torso_delta > lean_threshold:
            target_lane = 2
        lane = self._smooth_lane(target_lane, smoothing=max(0.24, self.mode_config.lane_smoothing))

        if abs(torso_delta) < (lean_threshold * 0.60):
            self.baseline_torso_x = (self.baseline_torso_x * 0.92) + (torso_mid_x * 0.08)

        # Jump is triggered by raising both hands well above shoulder line.
        hand_raise_margin = 0.055 / sensitivity
        jump_pose = (
            left_wrist.y < (left_shoulder.y - hand_raise_margin)
            and right_wrist.y < (right_shoulder.y - hand_raise_margin)
        )
        if self.baseline_left_wrist_y is not None and self.baseline_right_wrist_y is not None:
            jump_pose = jump_pose and (
                left_wrist.y < (self.baseline_left_wrist_y - (0.13 / sensitivity))
                and right_wrist.y < (self.baseline_right_wrist_y - (0.13 / sensitivity))
            )
        jump = jump_pose and self._trigger_jump()

        # Duck is a slight forward bend / downward torso shift.
        bend_margin = 0.078 / sensitivity
        down_pose = (
            nose.y > (shoulder_mid_y + bend_margin)
            or shoulder_mid_y > (self.baseline_shoulder_y + (0.05 / sensitivity))
        )

        if not down_pose:
            self.baseline_shoulder_y = (self.baseline_shoulder_y * 0.96) + (shoulder_mid_y * 0.04)

        return MovementState(
            lane=lane,
            jump=jump,
            duck=down_pose,
            tracked=True,
            message="Kids Mode: lean wide to move, both hands high to jump, bend forward to duck.",
        )

    def _handle_elderly_profile(self, landmarks) -> MovementState:
        if not self._visibility_ok(landmarks, self._elderly_required):
            return MovementState(message="Elderly Mode: keep shoulders, wrists, and hips visible.")

        nose = landmarks[self.pose_landmark.NOSE.value]
        left_shoulder = landmarks[self.pose_landmark.LEFT_SHOULDER.value]
        right_shoulder = landmarks[self.pose_landmark.RIGHT_SHOULDER.value]
        left_wrist = landmarks[self.pose_landmark.LEFT_WRIST.value]
        right_wrist = landmarks[self.pose_landmark.RIGHT_WRIST.value]

        sensitivity = max(0.55, self.mode_config.movement_sensitivity)
        shoulder_mid_x = (left_shoulder.x + right_shoulder.x) * 0.5
        shoulder_mid_y = (left_shoulder.y + right_shoulder.y) * 0.5
        shoulder_width = abs(right_shoulder.x - left_shoulder.x)

        if self.baseline_shoulder_y is None:
            self.baseline_shoulder_y = shoulder_mid_y

        # Elderly mode maps calm two-hand side extensions to lane changes.
        side_threshold = max(0.05, shoulder_width * (0.56 / sensitivity))
        both_left = (
            left_wrist.x < (shoulder_mid_x - side_threshold)
            and right_wrist.x < (shoulder_mid_x - (side_threshold * 0.72))
        )
        both_right = (
            left_wrist.x > (shoulder_mid_x + (side_threshold * 0.72))
            and right_wrist.x > (shoulder_mid_x + side_threshold)
        )

        target_lane = 1
        if both_left:
            target_lane = 0
        elif both_right:
            target_lane = 2
        lane = self._smooth_lane(target_lane, smoothing=min(0.16, self.mode_config.lane_smoothing))

        # Require a stable multi-frame raise for jump to avoid sudden spikes.
        hands_above_head = (
            left_wrist.y < (nose.y - (0.01 / sensitivity))
            and right_wrist.y < (nose.y - (0.01 / sensitivity))
        )
        if self.baseline_left_wrist_y is not None and self.baseline_right_wrist_y is not None:
            hands_above_head = hands_above_head and (
                left_wrist.y < (self.baseline_left_wrist_y - (0.09 / sensitivity))
                and right_wrist.y < (self.baseline_right_wrist_y - (0.09 / sensitivity))
            )
        if hands_above_head:
            self.elderly_jump_hold_frames += 1
        else:
            self.elderly_jump_hold_frames = 0

        jump = self.elderly_jump_hold_frames >= 3 and self._trigger_jump()
        if jump:
            self.elderly_jump_hold_frames = 0

        # Gentle forward bend/downward shoulder shift triggers duck.
        forward_bend = nose.y > (shoulder_mid_y + (0.098 / sensitivity))
        gentle_shoulder_drop = shoulder_mid_y > (self.baseline_shoulder_y + (0.038 / sensitivity))
        duck_pose = forward_bend or gentle_shoulder_drop

        self.duck_filter = (self.duck_filter * 0.82) + (0.18 if duck_pose else 0.0)
        duck = self.duck_filter > 0.48

        if not duck:
            self.baseline_shoulder_y = (self.baseline_shoulder_y * 0.98) + (shoulder_mid_y * 0.02)

        return MovementState(
            lane=lane,
            jump=jump,
            duck=duck,
            tracked=True,
            message="Elderly Mode: both hands left/right to move, slow raise above head to jump.",
        )

    def _handle_disabled_hand_profile(self, landmarks) -> MovementState:
        left_shoulder = landmarks[self.pose_landmark.LEFT_SHOULDER.value]
        right_shoulder = landmarks[self.pose_landmark.RIGHT_SHOULDER.value]
        left_hip = landmarks[self.pose_landmark.LEFT_HIP.value]
        right_hip = landmarks[self.pose_landmark.RIGHT_HIP.value]

        shoulders_visible = left_shoulder.visibility > 0.30 and right_shoulder.visibility > 0.30
        hips_visible = left_hip.visibility > 0.18 and right_hip.visibility > 0.18
        if not shoulders_visible:
            self.disabled_hand_jump_hold_frames = 0
            return MovementState(message="Disabled Hand Mode: keep shoulders visible to control movement.")

        sensitivity = max(0.55, self.mode_config.movement_sensitivity)
        shoulder_mid_x = (left_shoulder.x + right_shoulder.x) * 0.5
        shoulder_mid_y = (left_shoulder.y + right_shoulder.y) * 0.5
        if hips_visible:
            hip_mid_x = (left_hip.x + right_hip.x) * 0.5
            torso_mid_x = (shoulder_mid_x + hip_mid_x) * 0.5
        else:
            torso_mid_x = shoulder_mid_x
        shoulder_width = max(0.08, abs(right_shoulder.x - left_shoulder.x))
        tilt = left_shoulder.y - right_shoulder.y

        if self.baseline_torso_x is None:
            self.baseline_torso_x = torso_mid_x
        if self.baseline_shoulder_y is None:
            self.baseline_shoulder_y = shoulder_mid_y

        # No wrist landmarks: combine shoulder tilt + torso lean for lane selection.
        tilt_norm = tilt / shoulder_width
        torso_lean = torso_mid_x - self.baseline_torso_x
        lateral_signal = torso_lean - (tilt_norm * 0.08)
        lateral_threshold = 0.030 / sensitivity
        target_lane = 1
        if lateral_signal < -lateral_threshold:
            target_lane = 0
        elif lateral_signal > lateral_threshold:
            target_lane = 2
        lane = self._smooth_lane(target_lane, smoothing=max(0.24, self.mode_config.lane_smoothing))

        # Vertical shoulder baseline movement maps to jump (up) and duck (down).
        upward_shift = self.baseline_shoulder_y - shoulder_mid_y
        downward_shift = shoulder_mid_y - self.baseline_shoulder_y
        jump_threshold = 0.040 / sensitivity
        jump_release_threshold = jump_threshold * 0.45
        duck_threshold = 0.052 / sensitivity

        jump_pose = upward_shift > jump_threshold
        if jump_pose and self.disabled_hand_jump_armed:
            self.disabled_hand_jump_hold_frames += 1
        elif not jump_pose:
            self.disabled_hand_jump_hold_frames = 0

        jump = False
        if self.disabled_hand_jump_hold_frames >= 3 and self._trigger_jump():
            jump = True
            self.disabled_hand_jump_armed = False
            self.disabled_hand_jump_hold_frames = 0

        if upward_shift < jump_release_threshold:
            self.disabled_hand_jump_armed = True

        duck_pose = downward_shift > duck_threshold
        self.disabled_hand_duck_filter = (self.disabled_hand_duck_filter * 0.80) + (0.20 if duck_pose else 0.0)
        duck = self.disabled_hand_duck_filter > 0.50

        neutral_window = abs(upward_shift) < (jump_threshold * 0.55) and downward_shift < (duck_threshold * 0.55)
        if neutral_window:
            self.baseline_shoulder_y = (self.baseline_shoulder_y * 0.95) + (shoulder_mid_y * 0.05)
            self.baseline_torso_x = (self.baseline_torso_x * 0.94) + (torso_mid_x * 0.06)

        return MovementState(
            lane=lane,
            jump=jump,
            duck=duck,
            tracked=True,
            message="Disabled Hand Mode: lean torso/tilt shoulders to move, rise body to jump, small squat to duck.",
        )
