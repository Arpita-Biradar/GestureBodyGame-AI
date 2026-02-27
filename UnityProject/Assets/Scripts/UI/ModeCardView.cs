using System;
using System.Collections.Generic;
using TMPro;
using UnityEngine;
using UnityEngine.EventSystems;

namespace GestureBodyGame
{
    public class ModeCardView : MonoBehaviour, IPointerEnterHandler, IPointerExitHandler, IPointerClickHandler
    {
        [SerializeField] private Transform animatedRoot;
        [SerializeField] private Renderer[] glowRenderers;
        [SerializeField] private TMP_Text titleText;
        [SerializeField] private TMP_Text subtitleText;
        [SerializeField] private TMP_Text detailText;
        [SerializeField] private float floatAmplitude = 0.12f;
        [SerializeField] private float floatFrequency = 1.6f;
        [SerializeField] private float hoverScaleMultiplier = 1.05f;
        [SerializeField] private float selectedScaleMultiplier = 1.12f;
        [SerializeField] private float animationLerp = 10f;

        private readonly List<Material> runtimeMaterials = new List<Material>();

        private Action<int> onCardClicked;
        private Color modeColor = Color.cyan;
        private Vector3 startLocalPosition;
        private Vector3 startScale = Vector3.one;
        private int cardIndex;
        private bool isHovered;
        private bool isSelected;

        private void Awake()
        {
            if (animatedRoot == null)
            {
                animatedRoot = transform;
            }

            startLocalPosition = animatedRoot.localPosition;
            startScale = animatedRoot.localScale;
            CacheMaterials();
        }

        private void Update()
        {
            var floatOffset = Mathf.Sin(Time.time * floatFrequency + cardIndex * 0.4f) * floatAmplitude;
            var targetPosition = startLocalPosition + Vector3.up * floatOffset;
            animatedRoot.localPosition = Vector3.Lerp(
                animatedRoot.localPosition,
                targetPosition,
                1f - Mathf.Exp(-animationLerp * Time.deltaTime));

            var multiplier = isSelected ? selectedScaleMultiplier : (isHovered ? hoverScaleMultiplier : 1f);
            var targetScale = startScale * multiplier;
            animatedRoot.localScale = Vector3.Lerp(
                animatedRoot.localScale,
                targetScale,
                1f - Mathf.Exp(-animationLerp * Time.deltaTime));

            UpdateGlow();
        }

        private void OnDestroy()
        {
            for (var i = 0; i < runtimeMaterials.Count; i++)
            {
                Destroy(runtimeMaterials[i]);
            }
        }

        public void Initialize(ModeProfile profile, int index, Action<int> clickHandler)
        {
            cardIndex = index;
            onCardClicked = clickHandler;
            modeColor = profile.ThemeColor;

            if (titleText != null)
            {
                titleText.text = $"{profile.DisplayName} Mode";
            }

            if (subtitleText != null)
            {
                subtitleText.text = profile.CardSubtitle;
            }

            if (detailText != null)
            {
                detailText.text = profile.CardDetail;
            }
        }

        public void SetSelected(bool selected)
        {
            isSelected = selected;
        }

        public void OnPointerEnter(PointerEventData eventData)
        {
            isHovered = true;
        }

        public void OnPointerExit(PointerEventData eventData)
        {
            isHovered = false;
        }

        public void OnPointerClick(PointerEventData eventData)
        {
            onCardClicked?.Invoke(cardIndex);
        }

        private void OnMouseEnter()
        {
            isHovered = true;
        }

        private void OnMouseExit()
        {
            isHovered = false;
        }

        private void OnMouseDown()
        {
            onCardClicked?.Invoke(cardIndex);
        }

        private void CacheMaterials()
        {
            runtimeMaterials.Clear();

            for (var i = 0; i < glowRenderers.Length; i++)
            {
                if (glowRenderers[i] == null)
                {
                    continue;
                }

                var materials = glowRenderers[i].materials;
                for (var m = 0; m < materials.Length; m++)
                {
                    runtimeMaterials.Add(materials[m]);
                }
            }
        }

        private void UpdateGlow()
        {
            var highlight = isSelected ? 1f : (isHovered ? 0.65f : 0.30f);
            var pulse = 0.82f + Mathf.Sin(Time.time * 2.8f + cardIndex * 0.3f) * 0.18f;
            var intensity = highlight * pulse;

            var emissionColor = modeColor * Mathf.LinearToGammaSpace(2.5f * intensity);
            var baseTint = Color.Lerp(modeColor * 0.25f, modeColor * 0.55f, intensity);

            for (var i = 0; i < runtimeMaterials.Count; i++)
            {
                var material = runtimeMaterials[i];
                if (material == null)
                {
                    continue;
                }

                if (material.HasProperty("_BaseColor"))
                {
                    material.SetColor("_BaseColor", baseTint);
                }

                if (material.HasProperty("_EmissionColor"))
                {
                    material.EnableKeyword("_EMISSION");
                    material.SetColor("_EmissionColor", emissionColor);
                }
            }
        }
    }
}
