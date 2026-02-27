using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace GestureBodyGame
{
    public class UIManager : MonoBehaviour
    {
        [Header("Panels")]
        [SerializeField] private CanvasGroup topRightPanel;
        [SerializeField] private CanvasGroup bottomPanel;
        [SerializeField] private float panelFadeSpeed = 5f;

        [Header("Top Right HUD")]
        [SerializeField] private TMP_Text comboText;
        [SerializeField] private TMP_Text caloriesText;
        [SerializeField] private TMP_Text timerText;
        [SerializeField] private Image intensityFillImage;
        [SerializeField] private Image topPanelAccent;

        [Header("Bottom HUD")]
        [SerializeField] private TMP_Text modeLabelText;
        [SerializeField] private TMP_Text scoreText;
        [SerializeField] private TMP_Text instructionText;
        [SerializeField] private TMP_Text calibrationText;
        [SerializeField] private Image progressFillImage;
        [SerializeField] private Image bottomPanelAccent;

        private float targetPanelAlpha = 1f;
        private float smoothedIntensity;
        private float smoothedProgress;
        private float smoothedCalories;
        private Color accentColor = new Color(0.2f, 0.95f, 1f, 1f);

        private void Update()
        {
            var lerpFactor = 1f - Mathf.Exp(-panelFadeSpeed * Time.deltaTime);

            if (topRightPanel != null)
            {
                topRightPanel.alpha = Mathf.Lerp(topRightPanel.alpha, targetPanelAlpha, lerpFactor);
            }

            if (bottomPanel != null)
            {
                bottomPanel.alpha = Mathf.Lerp(bottomPanel.alpha, targetPanelAlpha, lerpFactor);
            }
        }

        public void InitializeHud(ModeProfile profile)
        {
            accentColor = profile.ThemeColor;

            if (modeLabelText != null)
            {
                modeLabelText.text = $"{profile.DisplayName} Mode";
                modeLabelText.color = profile.ThemeColor;
            }

            if (topPanelAccent != null)
            {
                topPanelAccent.color = profile.ThemeColor;
            }

            if (bottomPanelAccent != null)
            {
                bottomPanelAccent.color = profile.ThemeColor;
            }

            if (progressFillImage != null)
            {
                progressFillImage.color = profile.ThemeColor;
            }

            if (intensityFillImage != null)
            {
                intensityFillImage.color = profile.ThemeColor;
            }

            if (instructionText != null)
            {
                instructionText.text = "Keep shoulders, wrists, and hips visible.";
            }

            if (calibrationText != null)
            {
                calibrationText.text = string.Empty;
            }

            SetHudVisible(true);
        }

        public void RenderGameHud(SessionData data, float progress01)
        {
            if (data == null)
            {
                return;
            }

            var blend = 1f - Mathf.Exp(-8f * Time.deltaTime);
            smoothedIntensity = Mathf.Lerp(smoothedIntensity, data.IntensityNormalized, blend);
            smoothedProgress = Mathf.Lerp(smoothedProgress, progress01, blend);
            smoothedCalories = Mathf.Lerp(smoothedCalories, data.Calories, blend);

            if (comboText != null)
            {
                comboText.text = $"Combo: {data.Combo}";
            }

            if (caloriesText != null)
            {
                caloriesText.text = $"Calories Burned: {smoothedCalories:0} kcal";
            }

            if (timerText != null)
            {
                timerText.text = FormatTime(data.SessionSeconds);
            }

            if (scoreText != null)
            {
                scoreText.text = $"Score: {data.Score}";
            }

            if (intensityFillImage != null)
            {
                intensityFillImage.fillAmount = Mathf.Clamp01(smoothedIntensity);
                var glowColor = Color.Lerp(accentColor * 0.65f, Color.white, Mathf.Clamp01(smoothedIntensity * 0.6f));
                intensityFillImage.color = glowColor;
            }

            if (progressFillImage != null)
            {
                progressFillImage.fillAmount = Mathf.Clamp01(smoothedProgress);
            }
        }

        public void SetCalibrationText(string message)
        {
            if (calibrationText != null)
            {
                calibrationText.text = message;
            }
        }

        public void SetHudVisible(bool visible)
        {
            targetPanelAlpha = visible ? 1f : 0f;
        }

        private static string FormatTime(float seconds)
        {
            var totalSeconds = Mathf.Max(0, Mathf.FloorToInt(seconds));
            var minutes = totalSeconds / 60;
            var remainingSeconds = totalSeconds % 60;
            return $"{minutes:00}:{remainingSeconds:00}";
        }
    }
}
