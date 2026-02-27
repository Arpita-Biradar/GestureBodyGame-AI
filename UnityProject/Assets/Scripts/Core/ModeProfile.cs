using System.Collections.Generic;
using UnityEngine;

namespace GestureBodyGame
{
    [System.Serializable]
    public struct ModeProfile
    {
        public GameMode Mode;
        public string DisplayName;
        public string CardSubtitle;
        public string CardDetail;
        public Color ThemeColor;
        public float RunSpeedMultiplier;
        public float InputSensitivity;
        public float IntensityDecayRate;
        public float CalorieMultiplier;
        public float Difficulty;
    }

    public static class ModeCatalog
    {
        private static readonly List<ModeProfile> OrderedProfiles = new List<ModeProfile>
        {
            new ModeProfile
            {
                Mode = GameMode.Kids,
                DisplayName = "Kids",
                CardSubtitle = "Fun energetic pose icon",
                CardDetail = "High engagement rating",
                ThemeColor = new Color(0.20f, 0.95f, 0.40f, 1f),
                RunSpeedMultiplier = 1.15f,
                InputSensitivity = 1.20f,
                IntensityDecayRate = 0.11f,
                CalorieMultiplier = 1.08f,
                Difficulty = 0.72f
            },
            new ModeProfile
            {
                Mode = GameMode.Elderly,
                DisplayName = "Elderly",
                CardSubtitle = "Yoga pose icon",
                CardDetail = "Medium intensity",
                ThemeColor = new Color(0.20f, 0.70f, 1.00f, 1f),
                RunSpeedMultiplier = 0.92f,
                InputSensitivity = 0.88f,
                IntensityDecayRate = 0.15f,
                CalorieMultiplier = 0.82f,
                Difficulty = 0.42f
            },
            new ModeProfile
            {
                Mode = GameMode.LegFree,
                DisplayName = "Leg-Free",
                CardSubtitle = "Wheelchair icon",
                CardDetail = "Upper-body control | Moderate difficulty",
                ThemeColor = new Color(0.15f, 0.90f, 1.00f, 1f),
                RunSpeedMultiplier = 1.00f,
                InputSensitivity = 1.02f,
                IntensityDecayRate = 0.13f,
                CalorieMultiplier = 0.96f,
                Difficulty = 0.55f
            },
            new ModeProfile
            {
                Mode = GameMode.HandFree,
                DisplayName = "Hand-Free",
                CardSubtitle = "Pose-only control",
                CardDetail = "Red theme | Low sensitivity",
                ThemeColor = new Color(1.00f, 0.28f, 0.42f, 1f),
                RunSpeedMultiplier = 0.96f,
                InputSensitivity = 0.74f,
                IntensityDecayRate = 0.16f,
                CalorieMultiplier = 0.90f,
                Difficulty = 0.48f
            }
        };

        private static readonly Dictionary<GameMode, ModeProfile> ByMode = BuildLookup();

        public static IReadOnlyList<ModeProfile> Profiles => OrderedProfiles;

        public static ModeProfile Get(GameMode mode)
        {
            if (ByMode.TryGetValue(mode, out var profile))
            {
                return profile;
            }

            return OrderedProfiles[0];
        }

        private static Dictionary<GameMode, ModeProfile> BuildLookup()
        {
            var lookup = new Dictionary<GameMode, ModeProfile>(OrderedProfiles.Count);
            for (var i = 0; i < OrderedProfiles.Count; i++)
            {
                lookup[OrderedProfiles[i].Mode] = OrderedProfiles[i];
            }

            return lookup;
        }
    }
}
