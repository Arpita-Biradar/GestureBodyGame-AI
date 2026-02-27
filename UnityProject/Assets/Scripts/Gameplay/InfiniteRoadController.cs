using System.Collections.Generic;
using UnityEngine;

namespace GestureBodyGame
{
    public class InfiniteRoadController : MonoBehaviour
    {
        [SerializeField] private List<Transform> roadSegments = new List<Transform>();
        [SerializeField] private float segmentLength = 40f;
        [SerializeField] private float moveSpeed = 12f;

        private bool running;

        private void Reset()
        {
            roadSegments.Clear();
            foreach (Transform child in transform)
            {
                roadSegments.Add(child);
            }
        }

        private void Update()
        {
            if (!running || roadSegments.Count == 0)
            {
                return;
            }

            var travelDistance = moveSpeed * Time.deltaTime;
            var furthestZ = float.MinValue;

            for (var i = 0; i < roadSegments.Count; i++)
            {
                var segment = roadSegments[i];
                segment.position += Vector3.back * travelDistance;
                if (segment.position.z > furthestZ)
                {
                    furthestZ = segment.position.z;
                }
            }

            for (var i = 0; i < roadSegments.Count; i++)
            {
                var segment = roadSegments[i];
                if (segment.position.z < -segmentLength)
                {
                    segment.position = new Vector3(segment.position.x, segment.position.y, furthestZ + segmentLength);
                    furthestZ = segment.position.z;
                }
            }
        }

        public void Configure(float runSpeed)
        {
            moveSpeed = runSpeed;
        }

        public void SetRunning(bool isRunning)
        {
            running = isRunning;
        }
    }
}
