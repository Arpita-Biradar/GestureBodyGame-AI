using UnityEngine;

namespace GestureBodyGame
{
    public class AmbientParticleDrift : MonoBehaviour
    {
        [SerializeField] private ParticleSystem particleSystemToDrive;
        [SerializeField] private float driftSpeed = 1.8f;
        [SerializeField] private float noiseAmplitude = 0.25f;

        private Vector3 startPosition;

        private void Awake()
        {
            if (particleSystemToDrive == null)
            {
                particleSystemToDrive = GetComponent<ParticleSystem>();
            }

            startPosition = transform.position;
        }

        private void Update()
        {
            var t = Time.time;
            var offset = new Vector3(
                Mathf.Sin(t * 0.75f) * noiseAmplitude,
                Mathf.Sin(t * 0.45f + 1.1f) * noiseAmplitude,
                -driftSpeed * Mathf.PingPong(t * 0.2f, 1f));

            transform.position = startPosition + offset;
        }
    }
}
