import time
from dataclasses import dataclass

import cv2
import mediapipe as mp
import pygame


@dataclass
class ControlState:
    lane: int = 1
    jump: bool = False
    duck: bool = False
    tracked: bool = False
    message: str = "No body detected. Stand in front of the camera."


class BodyController:
    def __init__(self, camera_index: int = 0) -> None:
        self.cap = cv2.VideoCapture(camera_index)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=0,
            smooth_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self.mp_draw = mp.solutions.drawing_utils

        self.baseline_shoulder_y = None
        self.baseline_torso_x = None
        self.last_jump_time = 0.0

    def update(self) -> tuple[ControlState, pygame.Surface | None]:
        state = ControlState()
        frame_surface = None

        if not self.cap.isOpened():
            state.message = "Camera unavailable. Keyboard: left/right + up/down."
            return state, frame_surface

        ok, frame = self.cap.read()
        if not ok:
            state.message = "No camera frame. Keyboard: left/right + up/down."
            return state, frame_surface

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose.process(rgb)

        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            pose_landmark = self.mp_pose.PoseLandmark

            needed_points = [
                pose_landmark.NOSE.value,
                pose_landmark.LEFT_SHOULDER.value,
                pose_landmark.RIGHT_SHOULDER.value,
                pose_landmark.LEFT_WRIST.value,
                pose_landmark.RIGHT_WRIST.value,
                pose_landmark.LEFT_HIP.value,
                pose_landmark.RIGHT_HIP.value,
            ]

            if all(landmarks[index].visibility > 0.45 for index in needed_points):
                nose = landmarks[pose_landmark.NOSE.value]
                left_shoulder = landmarks[pose_landmark.LEFT_SHOULDER.value]
                right_shoulder = landmarks[pose_landmark.RIGHT_SHOULDER.value]
                left_wrist = landmarks[pose_landmark.LEFT_WRIST.value]
                right_wrist = landmarks[pose_landmark.RIGHT_WRIST.value]
                left_hip = landmarks[pose_landmark.LEFT_HIP.value]
                right_hip = landmarks[pose_landmark.RIGHT_HIP.value]

                shoulder_mid_x = (left_shoulder.x + right_shoulder.x) * 0.5
                shoulder_mid_y = (left_shoulder.y + right_shoulder.y) * 0.5
                hip_mid_x = (left_hip.x + right_hip.x) * 0.5
                torso_mid_x = (shoulder_mid_x + hip_mid_x) * 0.5

                if self.baseline_torso_x is None:
                    self.baseline_torso_x = torso_mid_x

                shoulder_width = abs(right_shoulder.x - left_shoulder.x)
                lean_threshold = max(0.035, shoulder_width * 0.28)
                torso_delta = torso_mid_x - self.baseline_torso_x
                if torso_delta < -lean_threshold:
                    state.lane = 0
                elif torso_delta > lean_threshold:
                    state.lane = 2
                else:
                    state.lane = 1

                if abs(torso_delta) < (lean_threshold * 0.6):
                    self.baseline_torso_x = (
                        self.baseline_torso_x * 0.94
                    ) + (torso_mid_x * 0.06)

                jump_pose = (
                    left_wrist.y < (left_shoulder.y - 0.04)
                    and right_wrist.y < (right_shoulder.y - 0.04)
                )
                now = time.time()
                if jump_pose and (now - self.last_jump_time) > 0.50:
                    state.jump = True
                    self.last_jump_time = now

                if self.baseline_shoulder_y is None:
                    self.baseline_shoulder_y = shoulder_mid_y

                crouch_pose = (
                    shoulder_mid_y > (self.baseline_shoulder_y + 0.055)
                    or nose.y > (shoulder_mid_y + 0.09)
                )
                state.duck = crouch_pose
                if not crouch_pose:
                    self.baseline_shoulder_y = (
                        self.baseline_shoulder_y * 0.98
                    ) + (shoulder_mid_y * 0.02)

                state.tracked = True
                state.message = "Move body left/right = lane | Hands up = jump | Move down = duck"
            else:
                state.message = "Move back so head, shoulders, wrists and hips are visible."

            self.mp_draw.draw_landmarks(
                frame,
                results.pose_landmarks,
                self.mp_pose.POSE_CONNECTIONS,
            )
        else:
            state.message = "No body detected. Stand in front of the camera."

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_surface = pygame.image.frombuffer(
            frame_rgb.tobytes(),
            (frame_rgb.shape[1], frame_rgb.shape[0]),
            "RGB",
        ).copy()

        return state, frame_surface

    def close(self) -> None:
        if self.cap.isOpened():
            self.cap.release()
        self.pose.close()
