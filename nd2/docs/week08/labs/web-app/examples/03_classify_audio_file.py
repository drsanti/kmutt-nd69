"""Example 03: Classify an existing audio file or in-memory PCM array."""
import sys
from pathlib import Path
import robotos_kws as rk


def main():
    wav_path = sys.argv[1] if len(sys.argv) > 1 else "dataset/blue/s01_me_pc_0000.wav"
    if not Path(wav_path).exists():
        print(f"[error] Audio file not found: {wav_path}")
        return 1

    detector = rk.Detector("artifacts/model_int8.tflite")

    # 1. Top predicted class
    top_label, confidence = detector.predict(wav_path)
    print(f"Top Class:       {top_label} ({confidence:.1%})")

    # 2. Full probability distribution
    probs = detector.predict_proba(wav_path)
    print("\nFull Probabilities:")
    for label, prob in probs.items():
        bar = "#" * int(prob * 30)
        print(f"  {label:<10}: {prob:5.1%} {bar}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
