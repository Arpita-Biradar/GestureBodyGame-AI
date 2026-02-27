using System;
using UnityEngine;

namespace GestureBodyGame
{
    public class PlayerController : MonoBehaviour
    {
        [SerializeField] private Transform visualRoot;
        [SerializeField] private float laneWidth = 2.8f;
        [SerializeField] private float laneSwitchSmoothTime = 0.16f;
        [SerializeField] private float tiltAngle = 14f;
        [SerializeField] private float tiltSmooth = 10f;

        private float currentInputSensitivity = 1f;
        private float laneSwitchVelocity;
        private float targetX;
        private bool inputEnabled = true;

        public event Action<int> LaneChanged;
        public event Action OrbCollected;

        public int CurrentLane { get; private set; } = 1;

        public float LaneWidth => laneWidth;

        private void Awake()
        {
            targetX = LaneToX(CurrentLane);
        }

        private void Update()
        {
            if (inputEnabled)
            {
                HandleKeyboardInput();
            }

            SmoothLaneMovement(Time.deltaTime);
            UpdateTilt(Time.deltaTime);
        }

        public void ConfigureLaneControl(float sensitivity)
        {
            currentInputSensitivity = Mathf.Clamp(sensitivity, 0.6f, 1.4f);
        }

        public void SetInputEnabled(bool enabled)
        {
            inputEnabled = enabled;
        }

        public void InjectGestureLane(float normalizedHorizontalValue)
        {
            if (normalizedHorizontalValue < -0.33f)
            {
                SetLane(0);
            }
            else if (normalizedHorizontalValue > 0.33f)
            {
                SetLane(2);
            }
            else
            {
                SetLane(1);
            }
        }

        public void NotifyOrbCollected()
        {
            OrbCollected?.Invoke();
        }

        private void HandleKeyboardInput()
        {
            if (Input.GetKeyDown(KeyCode.LeftArrow) || Input.GetKeyDown(KeyCode.A))
            {
                ShiftLane(-1);
            }
            else if (Input.GetKeyDown(KeyCode.RightArrow) || Input.GetKeyDown(KeyCode.D))
            {
                ShiftLane(1);
            }
        }

        private void ShiftLane(int direction)
        {
            SetLane(CurrentLane + direction);
        }

        private void SetLane(int lane)
        {
            var clampedLane = Mathf.Clamp(lane, 0, 2);
            if (clampedLane == CurrentLane)
            {
                return;
            }

            CurrentLane = clampedLane;
            targetX = LaneToX(CurrentLane);
            LaneChanged?.Invoke(CurrentLane);
        }

        private void SmoothLaneMovement(float deltaTime)
        {
            var position = transform.position;
            position.x = Mathf.SmoothDamp(
                position.x,
                targetX,
                ref laneSwitchVelocity,
                laneSwitchSmoothTime / currentInputSensitivity,
                Mathf.Infinity,
                deltaTime);
            transform.position = position;
        }

        private void UpdateTilt(float deltaTime)
        {
            if (visualRoot == null || laneWidth < 0.01f)
            {
                return;
            }

            var laneOffset = Mathf.Clamp((targetX - transform.position.x) / laneWidth, -1f, 1f);
            var targetTiltZ = -laneOffset * tiltAngle;
            var targetRotation = Quaternion.Euler(0f, 0f, targetTiltZ);

            visualRoot.localRotation = Quaternion.Slerp(
                visualRoot.localRotation,
                targetRotation,
                1f - Mathf.Exp(-tiltSmooth * deltaTime));
        }

        private float LaneToX(int lane)
        {
            return (lane - 1) * laneWidth;
        }
    }
}
