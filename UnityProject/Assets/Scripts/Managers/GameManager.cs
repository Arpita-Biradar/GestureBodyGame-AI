using System.Collections;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace GestureBodyGame
{
    public class GameManager : MonoBehaviour
    {
        [Header("Scene References")]
        [SerializeField] private PlayerController playerController;
        [SerializeField] private InfiniteRoadController infiniteRoadController;
        [SerializeField] private OrbSpawner orbSpawner;
        [SerializeField] private UIManager uiManager;
        [SerializeField] private SceneTransitionFader sceneTransitionFader;

        [Header("Session Tuning")]
        [SerializeField] private float maxSessionDurationSeconds = 180f;
        [SerializeField] private float baseRunSpeed = 14f;
        [SerializeField] private float intensityFromLaneSwitch = 0.08f;
        [SerializeField] private float intensityFromOrb = 0.16f;
        [SerializeField] private bool allowEscapeToEndSession = true;

        [Header("Scene Routing")]
        [SerializeField] private string summarySceneName = SceneNames.SessionSummary;

        private readonly SessionData activeSession = new SessionData();

        private GameState currentState = GameState.Boot;
        private ModeProfile activeMode;

        private SceneTransitionFader ActiveFader => sceneTransitionFader != null ? sceneTransitionFader : SceneTransitionFader.Instance;

        private void Start()
        {
            activeMode = PersistentGameContext.Instance.GetSelectedModeProfile();
            ConfigureSystems();
            BindEvents();

            activeSession.Reset();
            uiManager?.InitializeHud(activeMode);

            if (PersistentGameContext.Instance.CalibrationRequested)
            {
                StartCoroutine(CalibrationRoutine());
            }
            else
            {
                BeginGameplay();
            }
        }

        private void OnDisable()
        {
            UnbindEvents();
        }

        private void Update()
        {
            if (currentState != GameState.Playing)
            {
                return;
            }

            TickSession(Time.deltaTime);

            if (allowEscapeToEndSession && Input.GetKeyDown(KeyCode.Escape))
            {
                EndSession();
            }
        }

        public void PauseSession()
        {
            if (currentState != GameState.Playing)
            {
                return;
            }

            SetState(GameState.Paused);
            playerController?.SetInputEnabled(false);
            infiniteRoadController?.SetRunning(false);
            orbSpawner?.SetRunning(false);
        }

        public void ResumeSession()
        {
            if (currentState != GameState.Paused)
            {
                return;
            }

            BeginGameplay();
        }

        public void EndSession()
        {
            if (currentState == GameState.SessionEnded)
            {
                return;
            }

            SetState(GameState.SessionEnded);
            playerController?.SetInputEnabled(false);
            infiniteRoadController?.SetRunning(false);
            orbSpawner?.SetRunning(false);

            PersistentGameContext.Instance.CommitSession(activeSession);

            if (ActiveFader != null)
            {
                ActiveFader.LoadScene(summarySceneName);
            }
            else
            {
                SceneManager.LoadScene(summarySceneName);
            }
        }

        private void ConfigureSystems()
        {
            if (playerController == null)
            {
                playerController = FindObjectOfType<PlayerController>();
            }

            if (infiniteRoadController == null)
            {
                infiniteRoadController = FindObjectOfType<InfiniteRoadController>();
            }

            if (orbSpawner == null)
            {
                orbSpawner = FindObjectOfType<OrbSpawner>();
            }

            if (uiManager == null)
            {
                uiManager = FindObjectOfType<UIManager>();
            }

            var runSpeed = baseRunSpeed * activeMode.RunSpeedMultiplier;

            playerController?.ConfigureLaneControl(activeMode.InputSensitivity);
            infiniteRoadController?.Configure(runSpeed);
            orbSpawner?.Configure(runSpeed, playerController != null ? playerController.LaneWidth : 2.8f);
        }

        private void BindEvents()
        {
            if (playerController != null)
            {
                playerController.LaneChanged += OnLaneChanged;
                playerController.OrbCollected += OnOrbCollected;
            }

            if (orbSpawner != null)
            {
                orbSpawner.OrbMissed += OnOrbMissed;
            }
        }

        private void UnbindEvents()
        {
            if (playerController != null)
            {
                playerController.LaneChanged -= OnLaneChanged;
                playerController.OrbCollected -= OnOrbCollected;
            }

            if (orbSpawner != null)
            {
                orbSpawner.OrbMissed -= OnOrbMissed;
            }
        }

        private IEnumerator CalibrationRoutine()
        {
            SetState(GameState.Calibrating);
            playerController?.SetInputEnabled(false);
            infiniteRoadController?.SetRunning(false);
            orbSpawner?.SetRunning(false);

            // Simple staged calibration messaging before gameplay starts.
            uiManager?.SetCalibrationText("Calibration: hold neutral stance");
            yield return new WaitForSeconds(1f);
            uiManager?.SetCalibrationText("Calibration: keep shoulders level");
            yield return new WaitForSeconds(1f);
            uiManager?.SetCalibrationText("Calibration: locked");
            yield return new WaitForSeconds(0.8f);

            PersistentGameContext.Instance.SetCalibrationRequested(false);
            uiManager?.SetCalibrationText(string.Empty);

            BeginGameplay();
        }

        private void BeginGameplay()
        {
            SetState(GameState.Playing);
            playerController?.SetInputEnabled(true);
            infiniteRoadController?.SetRunning(true);
            orbSpawner?.SetRunning(true);
            uiManager?.SetHudVisible(true);
        }

        private void TickSession(float deltaTime)
        {
            activeSession.SessionSeconds += deltaTime;

            // Passive score is distance-based, with combo bonuses applied on orb collection.
            var distanceScorePerSecond = baseRunSpeed * activeMode.RunSpeedMultiplier * 7f;
            activeSession.Score += Mathf.RoundToInt(distanceScorePerSecond * deltaTime);

            activeSession.IntensityNormalized = Mathf.Clamp01(
                activeSession.IntensityNormalized - activeMode.IntensityDecayRate * deltaTime);

            var passiveCalories = 0.04f + (0.22f * activeSession.IntensityNormalized * activeMode.CalorieMultiplier);
            activeSession.Calories += passiveCalories * deltaTime;

            var progress01 = Mathf.Clamp01(activeSession.SessionSeconds / maxSessionDurationSeconds);
            uiManager?.RenderGameHud(activeSession, progress01);

            if (activeSession.SessionSeconds >= maxSessionDurationSeconds)
            {
                EndSession();
            }
        }

        private void OnLaneChanged(int laneIndex)
        {
            if (currentState != GameState.Playing)
            {
                return;
            }

            activeSession.IntensityNormalized = Mathf.Clamp01(
                activeSession.IntensityNormalized + (intensityFromLaneSwitch * activeMode.InputSensitivity));

            activeSession.Score += 8 + laneIndex * 3;
        }

        private void OnOrbCollected()
        {
            if (currentState != GameState.Playing)
            {
                return;
            }

            activeSession.CollectedOrbs++;
            activeSession.Combo = Mathf.Min(999, activeSession.Combo + 1);
            activeSession.Score += 45 + (activeSession.Combo * 12);
            activeSession.Calories += 0.24f * activeMode.CalorieMultiplier;

            activeSession.IntensityNormalized = Mathf.Clamp01(
                activeSession.IntensityNormalized + intensityFromOrb);
        }

        private void OnOrbMissed()
        {
            if (currentState != GameState.Playing)
            {
                return;
            }

            activeSession.Combo = 0;
        }

        private void SetState(GameState nextState)
        {
            currentState = nextState;
        }
    }
}
