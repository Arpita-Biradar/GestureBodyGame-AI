using System.Collections;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace GestureBodyGame
{
    public class SceneTransitionFader : MonoBehaviour
    {
        [SerializeField] private CanvasGroup fadeCanvasGroup;
        [SerializeField] private float fadeDuration = 0.4f;
        [SerializeField] private bool fadeInOnStart = true;

        public static SceneTransitionFader Instance { get; private set; }

        private bool transitionInProgress;

        private void Awake()
        {
            if (Instance != null && Instance != this)
            {
                Destroy(gameObject);
                return;
            }

            Instance = this;
            DontDestroyOnLoad(gameObject);

            if (fadeCanvasGroup == null)
            {
                fadeCanvasGroup = GetComponentInChildren<CanvasGroup>();
            }
        }

        private void Start()
        {
            if (fadeCanvasGroup == null)
            {
                return;
            }

            if (fadeInOnStart)
            {
                fadeCanvasGroup.alpha = 1f;
                StartCoroutine(FadeToRoutine(0f));
            }
            else
            {
                fadeCanvasGroup.alpha = 0f;
            }
        }

        public void LoadScene(string sceneName)
        {
            if (transitionInProgress || string.IsNullOrWhiteSpace(sceneName))
            {
                return;
            }

            StartCoroutine(LoadSceneRoutine(sceneName));
        }

        private IEnumerator LoadSceneRoutine(string sceneName)
        {
            transitionInProgress = true;
            yield return FadeToRoutine(1f);

            var loadOperation = SceneManager.LoadSceneAsync(sceneName);
            while (loadOperation != null && !loadOperation.isDone)
            {
                yield return null;
            }

            yield return FadeToRoutine(0f);
            transitionInProgress = false;
        }

        private IEnumerator FadeToRoutine(float targetAlpha)
        {
            if (fadeCanvasGroup == null)
            {
                yield break;
            }

            var initialAlpha = fadeCanvasGroup.alpha;
            var elapsed = 0f;
            var duration = Mathf.Max(0.01f, fadeDuration);

            fadeCanvasGroup.blocksRaycasts = true;
            fadeCanvasGroup.interactable = false;

            while (elapsed < duration)
            {
                elapsed += Time.unscaledDeltaTime;
                fadeCanvasGroup.alpha = Mathf.Lerp(initialAlpha, targetAlpha, elapsed / duration);
                yield return null;
            }

            fadeCanvasGroup.alpha = targetAlpha;
            fadeCanvasGroup.blocksRaycasts = targetAlpha > 0.01f;
        }
    }
}
