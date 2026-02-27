using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

namespace GestureBodyGame
{
    public class NeonButtonAnimator : MonoBehaviour, IPointerEnterHandler, IPointerExitHandler, IPointerDownHandler, IPointerUpHandler
    {
        [SerializeField] private RectTransform animatedTransform;
        [SerializeField] private Graphic[] glowTargets;
        [SerializeField] private float hoverScale = 1.06f;
        [SerializeField] private float pressedScale = 0.97f;
        [SerializeField] private float animationSpeed = 14f;
        [SerializeField] private Color idleColor = new Color(0.2f, 0.85f, 1f, 0.75f);
        [SerializeField] private Color hoverColor = new Color(0.55f, 0.95f, 1f, 1f);
        [SerializeField] private Color pressedColor = new Color(0.35f, 1f, 0.65f, 1f);

        private Vector3 baseScale = Vector3.one;
        private bool isHovered;
        private bool isPressed;

        private void Awake()
        {
            if (animatedTransform == null)
            {
                animatedTransform = transform as RectTransform;
            }

            if (animatedTransform != null)
            {
                baseScale = animatedTransform.localScale;
            }
        }

        private void Update()
        {
            if (animatedTransform == null)
            {
                return;
            }

            var targetMultiplier = 1f;
            if (isPressed)
            {
                targetMultiplier = pressedScale;
            }
            else if (isHovered)
            {
                targetMultiplier = hoverScale;
            }

            var targetScale = baseScale * targetMultiplier;
            animatedTransform.localScale = Vector3.Lerp(
                animatedTransform.localScale,
                targetScale,
                1f - Mathf.Exp(-animationSpeed * Time.deltaTime));

            var targetColor = idleColor;
            if (isPressed)
            {
                targetColor = pressedColor;
            }
            else if (isHovered)
            {
                targetColor = hoverColor;
            }

            for (var i = 0; i < glowTargets.Length; i++)
            {
                if (glowTargets[i] == null)
                {
                    continue;
                }

                glowTargets[i].color = Color.Lerp(
                    glowTargets[i].color,
                    targetColor,
                    1f - Mathf.Exp(-animationSpeed * Time.deltaTime));
            }
        }

        public void OnPointerEnter(PointerEventData eventData)
        {
            isHovered = true;
        }

        public void OnPointerExit(PointerEventData eventData)
        {
            isHovered = false;
            isPressed = false;
        }

        public void OnPointerDown(PointerEventData eventData)
        {
            isPressed = true;
        }

        public void OnPointerUp(PointerEventData eventData)
        {
            isPressed = false;
        }
    }
}
