"""Example 02: Voice control loop streamed directly from the ES3C28P board.

Connects to the microcontroller over USB, streams live MEMS mic PCM,
and recognizes spoken commands in real time.
"""
import sys
import robotos_kws as rk


def main():
    port = sys.argv[1] if len(sys.argv) > 1 else "COM5"
    model_path = "artifacts/model_int8.tflite"

    print(f"Connecting to board on {port} (gain=80%)...")
    detector = rk.Detector(model_path, threshold=0.80)

    print(f"[robotos_kws] Listening to board MEMS mic on {port}...")
    print("Press Ctrl+C to exit.\n")

    try:
        for keyword, confidence, timestamp in detector.stream_board(port=port, gain=80):
            print(f"[{timestamp:6.2f}s] Board Heard: '{keyword}' (confidence: {confidence:.1%})")
            if keyword == "red":
                print("  ==> Action: STOP")
            elif keyword == "green":
                print("  ==> Action: GO")
    except KeyboardInterrupt:
        print("\nExiting board stream.")
    except Exception as e:
        print(f"Error: {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
