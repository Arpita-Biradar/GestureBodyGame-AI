using System;
using System.Collections.Generic;
using UnityEngine;

namespace GestureBodyGame
{
    public class OrbSpawner : MonoBehaviour
    {
        [SerializeField] private CollectibleOrb orbPrefab;
        [SerializeField] private Transform orbPoolRoot;
        [SerializeField] private int poolSize = 30;
        [SerializeField] private float spawnAheadDistance = 62f;
        [SerializeField] private float despawnBehindDistance = 10f;
        [SerializeField] private float minSpawnSpacing = 5f;
        [SerializeField] private float maxSpawnSpacing = 10f;
        [SerializeField] private float moveSpeed = 12f;

        private readonly List<CollectibleOrb> orbPool = new List<CollectibleOrb>();

        private bool running;
        private float laneWidth = 2.8f;
        private float distanceUntilNextSpawn;

        public event Action OrbMissed;

        private void Awake()
        {
            if (orbPoolRoot == null)
            {
                var root = new GameObject("OrbPoolRoot");
                root.transform.SetParent(transform, false);
                orbPoolRoot = root.transform;
            }

            EnsurePool();
            ResetSpawner();
        }

        private void Update()
        {
            if (!running)
            {
                return;
            }

            var travelDistance = moveSpeed * Time.deltaTime;
            MoveOrbsBackward(travelDistance);

            // Spawns are distance-driven so pacing stays stable regardless of frame rate.
            distanceUntilNextSpawn -= travelDistance;
            while (distanceUntilNextSpawn <= 0f)
            {
                SpawnOrb();
                distanceUntilNextSpawn += UnityEngine.Random.Range(minSpawnSpacing, maxSpawnSpacing);
            }
        }

        public void Configure(float runSpeed, float laneWidthUnits)
        {
            moveSpeed = runSpeed;
            laneWidth = Mathf.Max(1f, laneWidthUnits);
        }

        public void SetRunning(bool shouldRun)
        {
            running = shouldRun;
        }

        public void ResetSpawner()
        {
            distanceUntilNextSpawn = 0f;
            for (var i = 0; i < orbPool.Count; i++)
            {
                orbPool[i].Despawn();
            }
        }

        internal void NotifyOrbCollected(CollectibleOrb orb)
        {
            if (orb == null)
            {
                return;
            }

            orb.Despawn();
        }

        private void EnsurePool()
        {
            if (orbPrefab == null)
            {
                return;
            }

            while (orbPool.Count < poolSize)
            {
                var orb = Instantiate(orbPrefab, orbPoolRoot);
                orb.Despawn();
                orbPool.Add(orb);
            }
        }

        private void MoveOrbsBackward(float travelDistance)
        {
            for (var i = 0; i < orbPool.Count; i++)
            {
                var orb = orbPool[i];
                if (!orb.IsSpawned)
                {
                    continue;
                }

                orb.transform.position += Vector3.back * travelDistance;

                if (orb.transform.position.z < -despawnBehindDistance)
                {
                    orb.Despawn();
                    OrbMissed?.Invoke();
                }
            }
        }

        private void SpawnOrb()
        {
            var orb = GetAvailableOrb();
            if (orb == null)
            {
                return;
            }

            var lane = UnityEngine.Random.Range(0, 3);
            var xPosition = (lane - 1) * laneWidth;
            var yPosition = UnityEngine.Random.Range(1.05f, 1.95f);
            var spawnPosition = new Vector3(xPosition, yPosition, spawnAheadDistance);

            orb.Spawn(this, spawnPosition);
        }

        private CollectibleOrb GetAvailableOrb()
        {
            for (var i = 0; i < orbPool.Count; i++)
            {
                if (!orbPool[i].IsSpawned)
                {
                    return orbPool[i];
                }
            }

            return null;
        }
    }
}
