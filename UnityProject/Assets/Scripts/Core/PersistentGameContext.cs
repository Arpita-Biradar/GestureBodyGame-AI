using System.Collections.Generic;
using UnityEngine;

namespace GestureBodyGame
{
    public class PersistentGameContext : MonoBehaviour
    {
        private static PersistentGameContext instance;

        [SerializeField] private GameMode defaultMode = GameMode.Elderly;

        private readonly Dictionary<GameMode, int> bestScoresByMode = new Dictionary<GameMode, int>();

        public static PersistentGameContext Instance
        {
            get
            {
                if (instance == null)
                {
                    var contextObject = new GameObject(nameof(PersistentGameContext));
                    instance = contextObject.AddComponent<PersistentGameContext>();
                }

                return instance;
            }
        }

        public GameMode SelectedMode { get; private set; }

        public bool CalibrationRequested { get; private set; }

        public SessionData LastSession { get; private set; } = new SessionData();

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        private static void Bootstrap()
        {
            _ = Instance;
        }

        private void Awake()
        {
            if (instance != null && instance != this)
            {
                Destroy(gameObject);
                return;
            }

            instance = this;
            DontDestroyOnLoad(gameObject);
            SelectedMode = defaultMode;
        }

        public void SelectMode(GameMode mode)
        {
            SelectedMode = mode;
        }

        public ModeProfile GetSelectedModeProfile()
        {
            return ModeCatalog.Get(SelectedMode);
        }

        public void SetCalibrationRequested(bool requested)
        {
            CalibrationRequested = requested;
        }

        public int GetBestScore(GameMode mode)
        {
            return bestScoresByMode.TryGetValue(mode, out var bestScore) ? bestScore : 0;
        }

        public void CommitSession(SessionData session)
        {
            if (session == null)
            {
                return;
            }

            var bestScore = Mathf.Max(GetBestScore(SelectedMode), session.Score);
            bestScoresByMode[SelectedMode] = bestScore;

            LastSession = session.Clone();
            LastSession.BestScore = bestScore;
        }
    }
}
