"""Example 03: Classify an existing audio file or in-memory PCM array."""
import sys
from pathlib import Path
try:
    import robotos_edge as rk
except ImportError:
    import robotos_kws as rk


def main():
    default_candidates = [
        "sample_audio.wav",
        "../sample_audio.wav",
        "dataset/blue/s01_me_pc_0000.wav",
        "../../../nd1/docs/week08/labs/python/dataset/blue/s01_me_pc_0000.wav",
    ]
    wav_path = None
    if len(sys.argv) > 1:
        wav_path = Path(sys.argv[1])
    else:
        for c in default_candidates:
            p = Path(c)
            if p.exists():
                wav_path = p
                break
        if wav_path is None:
            wav_path = Path("sample_audio.wav")

    if not wav_path.exists():
        print(f"[error] Audio file not found: {wav_path}")
        print("        Provide a wav file: python examples/03_classify_audio_file.py <path_to.wav>")
        return 1

    print(f"Analyzing: {wav_path}")

    model_candidates = [
        Path("artifacts/model_int8.tflite"),
        Path("../artifacts/model_int8.tflite"),
        Path("../python/artifacts/model_int8.tflite"),
        Path("../../../../../nd1/docs/week08/labs/python/artifacts/model_int8.tflite"),
    ]
    model_path = next((p for p in model_candidates if p.exists()), Path("artifacts/model_int8.tflite"))
    if not model_path.exists():
        print(f"[error] Model file not found in: {[str(p) for p in model_candidates]}")
        print("        Train a model first: robotos-edge train")
        return 1

    detector = rk.Detector(str(model_path))

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
