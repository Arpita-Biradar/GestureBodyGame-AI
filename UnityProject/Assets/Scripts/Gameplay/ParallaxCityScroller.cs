using System.Collections.Generic;
using UnityEngine;

namespace GestureBodyGame
{
    public class ParallaxCityScroller : MonoBehaviour
    {
        [SerializeField] private List<Transform> skylineLayers = new List<Transform>();
        [SerializeField] private float layerSpacing = 80f;
        [SerializeField] private float parallaxSpeed = 4f;

        private bool running = true;

        private void Update()
        {
            if (!running || skylineLayers.Count == 0)
            {
                return;
            }

            var moveDistance = parallaxSpeed * Time.deltaTime;
            var furthestZ = float.MinValue;

            for (var i = 0; i < skylineLayers.Count; i++)
            {
                var layer = skylineLayers[i];
                layer.position += Vector3.back * moveDistance;
                if (layer.position.z > furthestZ)
                {
                    furthestZ = layer.position.z;
                }
            }

            for (var i = 0; i < skylineLayers.Count; i++)
            {
                var layer = skylineLayers[i];
                if (layer.position.z < -layerSpacing)
                {
                    layer.position = new Vector3(layer.position.x, layer.position.y, furthestZ + layerSpacing);
                    furthestZ = layer.position.z;
                }
            }
        }

        public void Configure(float speedMultiplier)
        {
            parallaxSpeed = Mathf.Max(0.1f, speedMultiplier);
        }

        public void SetRunning(bool isRunning)
        {
            running = isRunning;
        }
    }
}
