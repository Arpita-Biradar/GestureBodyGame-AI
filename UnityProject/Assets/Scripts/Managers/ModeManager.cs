using TMPro;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace GestureBodyGame
{
    public class ModeManager : MonoBehaviour
    {
        [Header("Scene References")]
        [SerializeField] private ModeCardView[] modeCards;
        [SerializeField] private TMP_Text selectedModeText;
        [SerializeField] private TMP_Text footerHintText;
        [SerializeField] private SceneTransitionFader sceneTransitionFader;

        [Header("Scene Routing")]
        [SerializeField] private string gameplaySceneName = SceneNames.Gameplay;

        [Header("Selection")]
        [SerializeField] private int defaultSelectionIndex = 1;

        private int selectedIndex = -1;

        private SceneTransitionFader ActiveFader => sceneTransitionFader != null ? sceneTransitionFader : SceneTransitionFader.Instance;

        private void Start()
        {
            if (modeCards == null || modeCards.Length == 0)
            {
                return;
            }

            for (var i = 0; i < modeCards.Length; i++)
            {
                if (i >= ModeCatalog.Profiles.Count || modeCards[i] == null)
                {
                    continue;
                }

                modeCards[i].Initialize(ModeCatalog.Profiles[i], i, OnCardSelected);
            }

            SelectCard(Mathf.Clamp(defaultSelectionIndex, 0, ModeCatalog.Profiles.Count - 1));

            if (footerHintText != null)
            {
                footerHintText.text = "Press 1-4 or Click to choose. ENTER for calibration.";
            }
        }

        private void Update()
        {
            if (Input.GetKeyDown(KeyCode.Alpha1) || Input.GetKeyDown(KeyCode.Keypad1))
            {
                SelectCard(0);
            }
            else if (Input.GetKeyDown(KeyCode.Alpha2) || Input.GetKeyDown(KeyCode.Keypad2))
            {
                SelectCard(1);
            }
            else if (Input.GetKeyDown(KeyCode.Alpha3) || Input.GetKeyDown(KeyCode.Keypad3))
            {
                SelectCard(2);
            }
            else if (Input.GetKeyDown(KeyCode.Alpha4) || Input.GetKeyDown(KeyCode.Keypad4))
            {
                SelectCard(3);
            }

            if (Input.GetKeyDown(KeyCode.Return) || Input.GetKeyDown(KeyCode.KeypadEnter))
            {
                StartCalibration();
            }
        }

        private void OnCardSelected(int cardIndex)
        {
            SelectCard(cardIndex);
        }

        private void SelectCard(int cardIndex)
        {
            if (modeCards == null || modeCards.Length == 0)
            {
                return;
            }

            cardIndex = Mathf.Clamp(cardIndex, 0, Mathf.Min(modeCards.Length, ModeCatalog.Profiles.Count) - 1);
            selectedIndex = cardIndex;

            for (var i = 0; i < modeCards.Length; i++)
            {
                if (modeCards[i] == null)
                {
                    continue;
                }

                modeCards[i].SetSelected(i == selectedIndex);
            }

            var selectedProfile = ModeCatalog.Profiles[selectedIndex];
            PersistentGameContext.Instance.SelectMode(selectedProfile.Mode);

            if (selectedModeText != null)
            {
                selectedModeText.color = selectedProfile.ThemeColor;
                selectedModeText.text = $"Selected: {selectedProfile.DisplayName} Mode";
            }
        }

        private void StartCalibration()
        {
            if (selectedIndex < 0 || selectedIndex >= ModeCatalog.Profiles.Count)
            {
                return;
            }

            var selectedProfile = ModeCatalog.Profiles[selectedIndex];
            PersistentGameContext.Instance.SelectMode(selectedProfile.Mode);
            PersistentGameContext.Instance.SetCalibrationRequested(true);

            if (ActiveFader != null)
            {
                ActiveFader.LoadScene(gameplaySceneName);
            }
            else
            {
                SceneManager.LoadScene(gameplaySceneName);
            }
        }
    }
}
