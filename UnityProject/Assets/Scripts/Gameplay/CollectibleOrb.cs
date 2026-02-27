using UnityEngine;

namespace GestureBodyGame
{
    public class CollectibleOrb : MonoBehaviour
    {
        [SerializeField] private float rotationSpeed = 120f;
        [SerializeField] private float bobAmplitude = 0.14f;
        [SerializeField] private float bobFrequency = 2.5f;

        private OrbSpawner ownerSpawner;
        private float baseY;

        public bool IsSpawned { get; private set; }

        private void Update()
        {
            if (!IsSpawned)
            {
                return;
            }

            transform.Rotate(Vector3.up, rotationSpeed * Time.deltaTime, Space.World);

            var position = transform.position;
            position.y = baseY + Mathf.Sin(Time.time * bobFrequency + GetInstanceID() * 0.01f) * bobAmplitude;
            transform.position = position;
        }

        private void OnTriggerEnter(Collider other)
        {
            if (!IsSpawned)
            {
                return;
            }

            var playerController = other.GetComponentInParent<PlayerController>();
            if (playerController == null)
            {
                return;
            }

            playerController.NotifyOrbCollected();
            ownerSpawner?.NotifyOrbCollected(this);
        }

        public void Spawn(OrbSpawner owner, Vector3 worldPosition)
        {
            ownerSpawner = owner;
            transform.position = worldPosition;
            baseY = worldPosition.y;
            IsSpawned = true;
            gameObject.SetActive(true);
        }

        public void Despawn()
        {
            IsSpawned = false;
            gameObject.SetActive(false);
        }
    }
}
