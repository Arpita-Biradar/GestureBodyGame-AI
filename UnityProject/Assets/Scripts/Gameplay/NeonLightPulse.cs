using System.Collections.Generic;
using UnityEngine;

namespace GestureBodyGame
{
    public class NeonLightPulse : MonoBehaviour
    {
        [SerializeField] private Light targetLight;
        [SerializeField] private Renderer emissiveRenderer;
        [SerializeField] private Color neonColor = new Color(0.2f, 0.95f, 1f, 1f);
        [SerializeField] private float minIntensity = 2f;
        [SerializeField] private float maxIntensity = 4.5f;
        [SerializeField] private float pulseSpeed = 2.2f;

        private readonly List<Material> emissiveMaterials = new List<Material>();

        private void Awake()
        {
            if (targetLight == null)
            {
                targetLight = GetComponent<Light>();
            }

            if (emissiveRenderer != null)
            {
                var materials = emissiveRenderer.materials;
                for (var i = 0; i < materials.Length; i++)
                {
                    emissiveMaterials.Add(materials[i]);
                }
            }
        }

        private void OnDestroy()
        {
            for (var i = 0; i < emissiveMaterials.Count; i++)
            {
                Destroy(emissiveMaterials[i]);
            }
        }

        private void Update()
        {
            var t = (Mathf.Sin(Time.time * pulseSpeed + transform.position.z * 0.06f) + 1f) * 0.5f;
            var intensity = Mathf.Lerp(minIntensity, maxIntensity, t);

            if (targetLight != null)
            {
                targetLight.color = neonColor;
                targetLight.intensity = intensity;
            }

            for (var i = 0; i < emissiveMaterials.Count; i++)
            {
                var material = emissiveMaterials[i];
                if (material == null || !material.HasProperty("_EmissionColor"))
                {
                    continue;
                }

                material.EnableKeyword("_EMISSION");
                material.SetColor("_EmissionColor", neonColor * Mathf.LinearToGammaSpace(intensity));
            }
        }
    }
}
