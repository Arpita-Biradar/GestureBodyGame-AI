using UnityEngine;
using UnityEngine.UI;

namespace GestureBodyGame
{
    public class GlassPanelAnimator : MonoBehaviour
    {
        [SerializeField] private CanvasGroup canvasGroup;
        [SerializeField] private Graphic glowBorder;
        [SerializeField] private float fadeSpeed = 6f;
        [SerializeField] private float pulseSpeed = 2.4f;
        [SerializeField] private float pulseAmount = 0.18f;

        private float targetAlpha = 1f;
        private Color baseBorderColor = new Color(0.2f, 0.95f, 1f, 0.85f);

        private void Awake()
        {
            if (canvasGroup == null)
            {
                canvasGroup = GetComponent<CanvasGroup>();
            }

            if (glowBorder != null)
            {
                baseBorderColor = glowBorder.color;
            }
        }

        private void Update()
        {
            if (canvasGroup != null)
            {
                canvasGroup.alpha = Mathf.Lerp(
                    canvasGroup.alpha,
                    targetAlpha,
                    1f - Mathf.Exp(-fadeSpeed * Time.deltaTime));
            }

            if (glowBorder != null)
            {
                var pulse = 1f + Mathf.Sin(Time.time * pulseSpeed) * pulseAmount;
                var rgb = baseBorderColor * pulse;
                glowBorder.color = new Color(rgb.r, rgb.g, rgb.b, baseBorderColor.a);
            }
        }

        public void SetVisible(bool visible)
        {
            targetAlpha = visible ? 1f : 0f;
        }
    }
}
