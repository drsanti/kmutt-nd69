#!/usr/bin/env python3
"""Interactive Air Drum & Motion Music Synthesizer driven by ESP32-S3 IMU telemetry.

Usage:
    # 1. One-click Auto-Detection (Recommended):
    python air_drum.py

    # 2. Specify port manually:
    python air_drum.py --port COM17

    # 3. Built-in Demo Sound Check (No board needed):
    python air_drum.py --demo

    # 4. Offline Replay of pre-recorded gesture:
    python air_drum.py --replay samples/circle.csv --model imu_artifacts/model_int8.tflite
"""
from __future__ import annotations

import argparse
import math
import sys
import threading
import time
from pathlib import Path
from typing import List, Optional, Tuple

from robotos_edge.audio.drum_synth import DrumPolySynth, render_drum_kit, run_sound_check_demo, ASCII_BANNER


# ==============================================================================
# Air Drum Controller: Translates IMU strikes and 1D-CNN gestures into music
# ==============================================================================
class AirDrumController:
    def __init__(self, synth: DrumPolySynth, strike_thresh: float = 19.5, gesture_thresh: float = 0.70):
        self.synth = synth
        self.strike_cooldown = 0.11           # Minimum interval (seconds) between air strikes
        self.strike_threshold = strike_thresh # Acceleration peak threshold (~2.0g)
        self.gesture_threshold = gesture_thresh
        self.last_strike_time = 0.0
        self.last_gesture_time = 0.0
        self.gesture_cooldown = 0.50          # Cooldown between high-level CNN gestures
        self.stats = {"kick": 0, "snare": 0, "hihat": 0, "tom": 0, "crash": 0, "cowbell": 0}

    def print_summary(self):
        total = sum(self.stats.values())
        print("\n" + "=" * 50)
        print("          AIR DRUM SESSION SUMMARY")
        print("=" * 50)
        print(f"  Total Percussion Events : {total}")
        for inst, count in self.stats.items():
            print(f"  - {inst.upper():<10} : {count:3d} hits")
        print("=" * 50 + "\n")

    def handle_strike(self, t_s: float, accel: Tuple[float, float, float], gyro: Tuple[float, float, float]):
        """Detect instant transient acceleration peak (air drum strike)."""
        ax, ay, az = accel
        mag = math.sqrt(ax * ax + ay * ay + az * az)

        if mag > self.strike_threshold and (t_s - self.last_strike_time) > self.strike_cooldown:
            self.last_strike_time = t_s

            # Velocity dynamics: hitting harder plays louder sound (35% to 100% volume)
            velocity = min(1.0, max(0.35, (mag - self.strike_threshold) / 25.0 + 0.40))

            # Directional steering based on hand tilt:
            if ay < -3.5:
                instrument, symbol = "snare", "[SNARE DRUM]"
            elif ay > 3.5:
                instrument, symbol = "tom", "[TOM DRUM]"
            elif ax > 4.5:
                instrument, symbol = "cowbell", "[COWBELL]"
            elif mag > 30.0 or az < -12.0:
                instrument, symbol = "kick", "[BASS KICK]"
            else:
                instrument, symbol = "hihat", "[CLOSED HI-HAT]"

            self.stats[instrument] += 1
            self.synth.play(instrument, velocity)
            print(f"  >>> HIT: {symbol:<15} | Accel: {mag:5.1f} m/s² | Velocity: {velocity * 100:3.0f}%")

    def handle_gesture(self, gesture: str, confidence: float):
        """Dispatch high-level gestural musical effects from 1D-CNN."""
        now = time.monotonic()
        if (now - self.last_gesture_time) < self.gesture_cooldown:
            return

        if gesture == "circle":
            self.last_gesture_time = now
            self.stats["crash"] += 1
            print(f"\n  [CNN GESTURE] 'circle' ({confidence:.1%}) -> TRIGGER CRASH CYMBAL!")
            self.synth.play("crash", 0.95)
        elif gesture == "shake":
            self.last_gesture_time = now
            self.stats["hihat"] += 3
            self.stats["snare"] += 1
            print(f"\n  [CNN GESTURE] 'shake' ({confidence:.1%}) -> TRIGGER HI-HAT / SNARE ROLL!")
            threading.Thread(target=self._play_roll, daemon=True).start()
        elif gesture == "lift":
            self.last_gesture_time = now
            self.stats["tom"] += 2
            self.stats["crash"] += 1
            print(f"\n  [CNN GESTURE] 'lift' ({confidence:.1%}) -> TRIGGER TOM FILL!")
            threading.Thread(target=self._play_tom_fill, daemon=True).start()

    def _play_roll(self):
        for _ in range(4):
            self.synth.play("hihat", 0.85)
            time.sleep(0.065)
        self.synth.play("snare", 0.90)

    def _play_tom_fill(self):
        self.synth.play("tom", 0.80)
        time.sleep(0.12)
        self.synth.play("tom", 0.95)
        time.sleep(0.12)
        self.synth.play("crash", 0.90)


# ==============================================================================
# Main Entrypoint
# ==============================================================================
def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Air Drum & Motion Music Synthesizer (ESP32-S3 IMU).")
    parser.add_argument("--port", default=None, help="Serial port, e.g. COM17 (auto-detects if omitted)")
    parser.add_argument("--model", type=Path, default=Path("imu_artifacts/model_int8.tflite"), help="Path to int8 model")
    parser.add_argument("--replay", type=Path, help="Replay pre-recorded gesture CSV take")
    parser.add_argument("--demo", action="store_true", help="Run sound check demo pattern")
    parser.add_argument("--strike-thresh", type=float, default=19.5, help="Acceleration peak threshold (m/s^2) for strikes")
    parser.add_argument("--threshold", type=float, default=0.70, help="Confidence threshold for CNN gestures")
    parser.add_argument("--seconds", type=float, default=None, help="Stop after this many seconds")
    args = parser.parse_args(argv)

    try:
        synth = DrumPolySynth()
    except Exception as e:
        print(f"[error] Failed to initialize audio engine: {e}")
        return 1

    controller = AirDrumController(synth, strike_thresh=args.strike_thresh, gesture_thresh=args.threshold)

    # 1. Built-in Demo Sound Check
    if args.demo:
        run_sound_check_demo(synth)
        synth.close()
        return 0

    # 2. Offline CSV Gesture Replay Mode
    if args.replay:
        print(ASCII_BANNER)
        print(f"Replaying gesture take: {args.replay}")
        print(render_drum_kit())

        detector = None
        if args.model.exists():
            try:
                try:
                    from robotos_edge.ml import live_infer_imu as lii
                except ImportError:
                    import live_infer_imu as lii
                detector = lii.GestureDetector(str(args.model), threshold=args.threshold)
                print(f"Loaded 1D-CNN Model: {args.model}")
            except Exception as e:
                print(f"[warning] Could not load model: {e}")

        try:
            try:
                from robotos_edge.imu import features as ic
            except ImportError:
                import imu_common as ic
            rows = ic.load_window(args.replay)
            t = 0.0
            dt = 1.0 / ic.RATE_HZ

            for row in rows:
                accel = (row[0], row[1], row[2])
                gyro = (row[3], row[4], row[5])
                controller.handle_strike(t, accel, gyro)

                if detector:
                    detector.push(t, accel, gyro)
                    if detector.detections:
                        _, label, score = detector.detections.pop()
                        controller.handle_gesture(label, score)
                t += dt
                time.sleep(dt * 0.4)

            # Flush trailing samples
            if detector:
                for _ in range(ic.WINDOW):
                    detector.push(t, (0, 0, ic.G), (0, 0, 0))
                    t += dt
                    if detector.detections:
                        _, label, score = detector.detections.pop()
                        controller.handle_gesture(label, score)
                    time.sleep(dt * 0.2)

            time.sleep(0.5)
            print("\n[Replay Complete]")
            controller.print_summary()
            return 0
        except Exception as e:
            print(f"[error] Replay failed: {e}")
            return 1
        finally:
            synth.close()

    # 3. Live ESP32-S3 Board Mode
    if not args.port:
        try:
            from robotos_edge.hardware import detect as detect_board
            from robotos_edge.hardware import wire
        except ImportError:
            import detect_board
            import wire
        try:
            args.port = detect_board.auto_detect_port(need_cap=wire.CAP_IMU, preferred_model="ws28p")
        except Exception as e:
            print(f"[error] Could not auto-detect ws28p board: {e}")
            print("        Please specify --port <PORT>, --demo, or --replay <FILE.csv>")
            synth.close()
            return 1

    try:
        from robotos_edge.ml import live_infer_imu as lii
        from robotos_edge.hardware import wire
    except ImportError:
        try:
            import live_infer_imu as lii
            import wire
        except ImportError:
            print("[error] robotos_edge package not found. Please install the wheel from dist/")
            synth.close()
            return 1

    detector = None
    if args.model.exists():
        try:
            detector = lii.GestureDetector(str(args.model), threshold=args.threshold)
            print(f"Loaded 1D-CNN Model: {args.model}")
        except Exception as e:
            print(f"[warning] Could not initialize model {args.model}: {e}")

    print(ASCII_BANNER)
    print(f"Connecting to ws28p board on {args.port}...")
    try:
        sess = wire.BoardSession.open(args.port)
    except wire.WireError as e:
        print(f"[error] {e}")
        synth.close()
        return 2

    start_time = time.monotonic()
    try:
        sess.wait_board_info(need_cap=wire.CAP_IMU, need_name="air_drum.py")
        print(render_drum_kit())
        print("Ready! Hold the board like a drumstick.")
        print("  - Strike downward hard   -> Bass Kick Drum")
        print("  - Strike tilted Left     -> Snare Drum")
        print("  - Strike tilted Right    -> Tom Drum")
        print("  - Strike flat / light    -> Closed Hi-Hat")
        print("  - Circular motion        -> Crash Cymbal (CNN)")
        print("  - Shake stick            -> Hi-Hat/Snare Roll (CNN)")
        print("\nPress Ctrl+C to stop drumming.\n")

        while True:
            if args.seconds and (time.monotonic() - start_time) >= args.seconds:
                print(f"\n[Timer] Reached {args.seconds:.1f}s limit.")
                break

            for f in sess.poll(0.04):
                if f.msg_type == wire.MSG_IMU:
                    s = wire.decode_imu(f.payload)
                    t_s = s.timestamp_ns * 1e-9 if s.timestamp_ns else time.monotonic()
                    controller.handle_strike(t_s, s.accel, s.gyro)

                    if detector:
                        detector.push(t_s, s.accel, s.gyro)
                        if detector.detections:
                            _, label, score = detector.detections.pop()
                            controller.handle_gesture(label, score)
    except KeyboardInterrupt:
        print("\nDrumming session finished.")
    except Exception as e:
        print(f"[error] {e}")
        return 1
    finally:
        controller.print_summary()
        sess.close()
        synth.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
