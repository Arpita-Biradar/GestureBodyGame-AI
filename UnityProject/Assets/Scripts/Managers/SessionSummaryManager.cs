using System.Collections;
using TMPro;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.UI;

namespace GestureBodyGame
{
    public class SessionSummaryManager : MonoBehaviour
    {
        [Header("Summary UI")]
        [SerializeField] private CanvasGroup summaryPanelGroup;
        [SerializeField] private TMP_Text scoreText;
        [SerializeField] private TMP_Text bestScoreText;
        [SerializeField] private TMP_Text caloriesText;
        [SerializeField] private TMP_Text sessionTimeText;
        [SerializeField] private TMP_Text modeText;
        [SerializeField] private Image intensityMeterFill;
        [SerializeField] private Image panelGlow;

        [Header("Scene Routing")]
        [SerializeField] private string gameplaySceneName = SceneNames.Gameplay;
        [SerializeField] private string modeSelectionSceneName = SceneNames.ModeSelection;
        [SerializeField] private SceneTransitionFader sceneTransitionFader;

        private float targetPanelAlpha = 1f;

        private SceneTransitionFader ActiveFader => sceneTransitionFader != null ? sceneTransitionFader : SceneTransitionFader.Instance;

        private void Start()
        {
            ApplySummary(PersistentGameContext.Instance.LastSession);
        }

        private void Update()
        {
            if (summaryPanelGroup != null)
            {
                summaryPanelGroup.alpha = Mathf.Lerp(
                    summaryPanelGroup.alpha,
                    targetPanelAlpha,
                    1f - Mathf.Exp(-5f * Time.deltaTime));
            }
        }

        public void ReplaySession()
        {
            PersistentGameContext.Instance.SetCalibrationRequested(false);
            LoadScene(gameplaySceneName);
        }

        public void ChangeMode()
        {
            LoadScene(modeSelectionSceneName);
        }

        public void ViewStats()
        {
            StartCoroutine(PanelPulseRoutine());
        }

        private void ApplySummary(SessionData summary)
        {
            if (summary == null)
            {
                return;
            }

            if (scoreText != null)
            {
                scoreText.text = $"Score: {summary.Score}";
            }

            if (bestScoreText != null)
            {
                bestScoreText.text = $"Best Score: {summary.BestScore}";
            }

            if (caloriesText != null)
            {
                caloriesText.text = $"Calories Burned: {summary.Calories:0} kcal";
            }

            if (sessionTimeText != null)
            {
                sessionTimeText.text = $"Session Time: {FormatTime(summary.SessionSeconds)}";
            }

            if (modeText != null)
            {
                var modeProfile = PersistentGameContext.Instance.GetSelectedModeProfile();
                modeText.text = $"{modeProfile.DisplayName} Mode";
                modeText.color = modeProfile.ThemeColor;
            }

            if (intensityMeterFill != null)
            {
                intensityMeterFill.fillAmount = Mathf.Clamp01(summary.IntensityNormalized);
            }
        }

        private void LoadScene(string sceneName)
        {
            if (ActiveFader != null)
            {
                ActiveFader.LoadScene(sceneName);
            }
            else
            {
                SceneManager.LoadScene(sceneName);
            }
        }

        private IEnumerator PanelPulseRoutine()
        {
            if (panelGlow == null)
            {
                yield break;
            }

            var originalColor = panelGlow.color;
            var pulseColor = Color.Lerp(originalColor, Color.white, 0.45f);
            var elapsed = 0f;
            var duration = 0.25f;

            while (elapsed < duration)
            {
                elapsed += Time.deltaTime;
                panelGlow.color = Color.Lerp(originalColor, pulseColor, elapsed / duration);
                yield return null;
            }

            elapsed = 0f;
            while (elapsed < duration)
            {
                elapsed += Time.deltaTime;
                panelGlow.color = Color.Lerp(pulseColor, originalColor, elapsed / duration);
                yield return null;
            }

            panelGlow.color = originalColor;
        }

        private static string FormatTime(float seconds)
        {
            var totalSeconds = Mathf.Max(0, Mathf.FloorToInt(seconds));
            var minutes = totalSeconds / 60;
            var remainder = totalSeconds % 60;
            return $"{minutes:00}:{remainder:00}";
        }
    }
}
