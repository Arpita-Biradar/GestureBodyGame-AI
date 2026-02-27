namespace GestureBodyGame
{
    [System.Serializable]
    public class SessionData
    {
        public int Score;
        public int BestScore;
        public int Combo;
        public float Calories;
        public float IntensityNormalized;
        public float SessionSeconds;
        public int CollectedOrbs;

        public void Reset()
        {
            Score = 0;
            BestScore = 0;
            Combo = 0;
            Calories = 0f;
            IntensityNormalized = 0f;
            SessionSeconds = 0f;
            CollectedOrbs = 0;
        }

        public SessionData Clone()
        {
            return new SessionData
            {
                Score = Score,
                BestScore = BestScore,
                Combo = Combo,
                Calories = Calories,
                IntensityNormalized = IntensityNormalized,
                SessionSeconds = SessionSeconds,
                CollectedOrbs = CollectedOrbs
            };
        }
    }
}
