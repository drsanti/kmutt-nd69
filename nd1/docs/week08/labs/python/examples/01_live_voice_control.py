"""Example 01: Live voice control loop using robotos_kws.

Listens to your computer microphone and triggers actions when target keywords
('red', 'green', 'blue', 'off') are detected.
"""
import sys
import robotos_kws as rk


def main():
    model_path = "artifacts/model_int8.tflite"
    print(f"Loading KWS model from {model_path}...")
    try:
        detector = rk.Detector(model_path, threshold=0.80)
    except FileNotFoundError:
        print(f"[error] {model_path} not found. Run training first: robotos-kws train")
        return 1

    print("\n[robotos_kws] Detector active! Speak keywords into your microphone:")
    print("  'red'   -> STOP")
    print("  'green' -> FORWARD")
    print("  'blue'  -> TURN LEFT")
    print("  'off'   -> SHUTDOWN")
    print("Press Ctrl+C to exit.\n")

    try:
        for keyword, confidence, timestamp in detector.stream_pc():
            print(f"[{timestamp:6.2f}s] Heard: '{keyword}' (confidence: {confidence:.1%})")

            # Example: Wire to robot behavior
            if keyword == "red":
                print("  ==> [ROBOT ACTION] Emergency Stop!")
            elif keyword == "green":
                print("  ==> [ROBOT ACTION] Driving Forward (speed=100)")
            elif keyword == "blue":
                print("  ==> [ROBOT ACTION] Turning Left 90 deg")
            elif keyword == "off":
                print("  ==> [ROBOT ACTION] Shutting down motors.")
    except KeyboardInterrupt:
        print("\nExiting voice control loop.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
