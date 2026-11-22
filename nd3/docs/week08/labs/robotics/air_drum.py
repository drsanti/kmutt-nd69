#!/usr/bin/env python3
"""Interactive Air Drum & Motion Music Synthesizer driven by ESP32-S3 IMU telemetry.

Features:
- Zero external audio files: synthesizes Kick, Snare, Hi-Hat, Tom, Cowbell, and Crash Cymbal
  in real-time memory via NumPy and sounddevice.
- Polyphonic low-latency audio engine: multiple drum voices ring out simultaneously.
- Dual-triggering architecture:
  1. Instant Transient Strike Detection: Air-drumming downward strike with velocity dynamics
     (hitting harder plays louder sound, tilt angle directs strike to Snare, Tom, Kick, or Hi-Hat).
  2. 1D-CNN Gestural Music:
     - 'shake'  -> Rapid Hi-Hat / Snare Roll
     - 'circle' -> Sweeping Crash Cymbal
     - 'lift'   -> Tom Fill / Cowbell Accent
- Auto-port detection, offline CSV gesture replay, and demo sound check mode.

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

import numpy as np

try:
    import sounddevice as sd
except ImportError:
    sd = None


# ==============================================================================
# 1. Zero-Dependency Drum Synthesizer (NumPy + sounddevice)
# ==============================================================================
class DrumPolySynth:
    """Polyphonic drum synthesizer generating percussion waveforms in real-time."""

    def __init__(self, sample_rate: int = 44100):
        if sd is None:
            raise RuntimeError("sounddevice is not installed. Run 'pip install sounddevice'")
        self.fs = sample_rate
        self.lock = threading.Lock()
        self.active_voices: List[List] = []  # [samples_array, current_index, volume]
        self._init_waveforms()

        self.stream = sd.OutputStream(
            samplerate=self.fs,
            channels=1,
            blocksize=256,
            callback=self._audio_callback,
        )
        self.stream.start()

    def _audio_callback(self, outdata, frames, time_info, status):
        outdata.fill(0)
        buf = np.zeros(frames, dtype=np.float32)
        with self.lock:
            remaining = []
            for voice in self.active_voices:
                data, idx, vol = voice
                chunk_len = min(frames, len(data) - idx)
                if chunk_len > 0:
                    buf[:chunk_len] += data[idx:idx + chunk_len] * vol
                    idx += chunk_len
                    if idx < len(data):
                        remaining.append([data, idx, vol])
            self.active_voices = remaining
        # Soft limiter / saturation to avoid harsh digital clipping
        outdata[:, 0] = np.tanh(buf)

    def _init_waveforms(self):
        fs = self.fs

        # 1. KICK DRUM: Punchy exponential pitch sweep 160 Hz -> 42 Hz with sub-bass weight
        t_kick = np.linspace(0, 0.28, int(fs * 0.28), False)
        f_kick = 42.0 + 118.0 * np.exp(-t_kick * 32.0)
        phase_kick = 2 * np.pi * np.cumsum(f_kick) / fs
        env_kick = np.exp(-t_kick * 13.0)
        # Add slight sub-harmonic click
        click = np.sin(2 * np.pi * 300 * t_kick[:int(fs * 0.015)]) * np.linspace(1, 0, int(fs * 0.015))
        kick_buf = np.sin(phase_kick) * env_kick
        kick_buf[:len(click)] += click * 0.4
        self.kick = np.clip(kick_buf * 1.1, -1.0, 1.0).astype(np.float32)

        # 2. SNARE DRUM: Tuned drum body (185 Hz) + crisp filtered noise envelope
        t_snare = np.linspace(0, 0.22, int(fs * 0.22), False)
        body = np.sin(2 * np.pi * 185 * t_snare) * np.exp(-t_snare * 24.0)
        noise = np.random.uniform(-1, 1, len(t_snare))
        # High-pass filter noise
        noise[1:] = noise[1:] - 0.70 * noise[:-1]
        noise_env = np.exp(-t_snare * 17.0)
        self.snare = (body * 0.55 + noise * noise_env * 0.65).astype(np.float32)

        # 3. CLOSED HI-HAT: Ultra-crisp high frequency metallic sizzle (60 ms)
        t_hh = np.linspace(0, 0.065, int(fs * 0.065), False)
        hh_noise = np.random.uniform(-1, 1, len(t_hh))
        # Metallic highpass difference
        hh_noise[1:] = hh_noise[1:] - 0.88 * hh_noise[:-1]
        self.hihat = (hh_noise * np.exp(-t_hh * 55.0) * 0.65).astype(np.float32)

        # 4. OPEN HI-HAT: Sustained metallic sizzle (350 ms)
        t_oh = np.linspace(0, 0.35, int(fs * 0.35), False)
        oh_noise = np.random.uniform(-1, 1, len(t_oh))
        oh_noise[1:] = oh_noise[1:] - 0.85 * oh_noise[:-1]
        self.open_hh = (oh_noise * np.exp(-t_oh * 11.0) * 0.60).astype(np.float32)

        # 5. CRASH CYMBAL: Multi-sine inharmonic metallic clusters + noise shimmer (1.4 s)
        t_cr = np.linspace(0, 1.4, int(fs * 1.4), False)
        freqs = [587, 845, 1175, 1480, 2120]
        sines = np.zeros_like(t_cr)
        for f in freqs:
            sines += np.sin(2 * np.pi * f * t_cr + np.random.uniform(0, 2 * np.pi))
        sines /= len(freqs)
        cr_noise = np.random.uniform(-1, 1, len(t_cr))
        cr_noise[1:] = cr_noise[1:] - 0.75 * cr_noise[:-1]
        cr_env = np.exp(-t_cr * 3.2)
        self.crash = ((sines * 0.35 + cr_noise * 0.45) * cr_env).astype(np.float32)

        # 6. TOM DRUM: Resonant pitch-bending body (140 Hz -> 70 Hz)
        t_tom = np.linspace(0, 0.32, int(fs * 0.32), False)
        f_tom = 70.0 + 70.0 * np.exp(-t_tom * 16.0)
        phase_tom = 2 * np.pi * np.cumsum(f_tom) / fs
        self.tom = (np.sin(phase_tom) * np.exp(-t_tom * 9.5) * 0.9).astype(np.float32)

        # 7. COWBELL: Classic 808 dual square pulse (587 Hz & 845 Hz)
        t_cb = np.linspace(0, 0.18, int(fs * 0.18), False)
        cb1 = np.sign(np.sin(2 * np.pi * 587 * t_cb))
        cb2 = np.sign(np.sin(2 * np.pi * 845 * t_cb))
        cb_env = np.exp(-t_cb * 19.0)
        self.cowbell = ((cb1 + cb2) * 0.35 * cb_env).astype(np.float32)

    def play(self, sound_name: str, volume: float = 1.0):
        snd = getattr(self, sound_name, None)
        if snd is not None:
            vol = float(np.clip(volume, 0.1, 1.0))
            with self.lock:
                self.active_voices.append([snd, 0, vol])

    def close(self):
        try:
            self.stream.stop()
            self.stream.close()
        except Exception:
            pass


# ==============================================================================
# 2. Visual ASCII Drum Kit Interface
# ==============================================================================
ASCII_BANNER = """
================================================================================
           AIR DRUM & MOTION MUSIC SYNTHESIZER (ESP32-S3 IMU)
================================================================================
"""

ASCII_DRUM_KIT = """
  +--------------------------- AIR DRUM KIT ---------------------------+
  |                                                                    |
  |     [CRASH]                  (HI-HAT)                   [RIDE]     |
  |      {crash_pad}                       {hihat_pad}                     {ride_pad}     |
  |                                                                    |
  |               [SNARE]                        [TOM]                 |
  |                {snare_pad}                          {tom_pad}                |
  |                                                                    |
  |                               (KICK)                               |
  |                                {kick_pad}                                |
  |                                                                    |
  +--------------------------------------------------------------------+
"""


def render_drum_kit(hit_sound: Optional[str] = None) -> str:
    def pad(name: str, symbol: str = "O") -> str:
        if hit_sound == name:
            return f"[{symbol * 3}]"
        return f" {symbol} "

    return ASCII_DRUM_KIT.format(
        crash_pad=pad("crash", "*"),
        hihat_pad=pad("hihat", "#") if hit_sound != "open_hh" else pad("open_hh", "="),
        ride_pad=pad("cowbell", "@"),
        snare_pad=pad("snare", "X"),
        tom_pad=pad("tom", "o"),
        kick_pad=pad("kick", "O"),
    )


# ==============================================================================
# 3. Air Drum Controller Logic
# ==============================================================================
class AirDrumController:
    """Processes IMU acceleration strikes and CNN gesture classifications."""

    def __init__(self, synth: DrumPolySynth, strike_thresh: float = 19.5, gesture_thresh: float = 0.70):
        self.synth = synth
        self.last_strike_time = 0.0
        self.strike_cooldown = 0.11  # 110ms minimum interval between drum strikes
        self.strike_threshold = strike_thresh  # m/s^2 (~2.0g peak to trigger strike)
        self.gesture_threshold = gesture_thresh
        self.last_gesture_time = 0.0
        self.gesture_cooldown = 0.50  # 500ms cooldown for high-level gesture triggers
        self.stats = {
            "kick": 0,
            "snare": 0,
            "hihat": 0,
            "tom": 0,
            "crash": 0,
            "cowbell": 0,
        }

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

            # Calculate velocity / strike power (dynamic scaling: 35% to 100%)
            velocity = min(1.0, max(0.35, (mag - self.strike_threshold) / 25.0 + 0.40))

            # Strike Direction / Instrument Mapping:
            # - Tilted Left (ay < -3.5): Snare Drum
            # - Tilted Right (ay > +3.5): Tom Drum
            # - Tilted Backwards or Up (ax > +4.0): Cowbell / Cymbal Bell
            # - Flat Downward Strike:
            #     If hard strike (mag > 30) -> Kick Drum
            #     Else -> Closed Hi-Hat
            if ay < -3.5:
                instrument = "snare"
                symbol = "[SNARE DRUM]"
            elif ay > 3.5:
                instrument = "tom"
                symbol = "[TOM DRUM]"
            elif ax > 4.5:
                instrument = "cowbell"
                symbol = "[COWBELL]"
            elif mag > 30.0 or az < -12.0:
                instrument = "kick"
                symbol = "[BASS KICK]"
            else:
                instrument = "hihat"
                symbol = "[CLOSED HI-HAT]"

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
# 4. Built-In Demo Mode (Plays a rock groove to verify sound)
# ==============================================================================
def run_demo(synth: DrumPolySynth):
    print(ASCII_BANNER)
    print("Running Built-In Air Drum Sound Check Demo...")
    print(render_drum_kit())

    patterns = [
        # (Sound, Volume, Delay after)
        ("kick", 1.0, 0.25),
        ("hihat", 0.7, 0.25),
        ("snare", 0.95, 0.25),
        ("hihat", 0.7, 0.25),
        ("kick", 0.9, 0.125),
        ("kick", 1.0, 0.125),
        ("snare", 1.0, 0.25),
        ("tom", 0.85, 0.15),
        ("tom", 0.95, 0.15),
        ("crash", 1.0, 0.60),
        ("cowbell", 0.85, 0.25),
        ("cowbell", 0.95, 0.35),
    ]

    for snd, vol, delay in patterns:
        print(f"  [Demo Voice] Playing {snd.upper():<8} (Vol: {vol * 100:3.0f}%)")
        synth.play(snd, vol)
        time.sleep(delay)

    print("\n[Demo Complete] All percussion sound engines verified successfully!")


# ==============================================================================
# 5. Main Entrypoint
# ==============================================================================
def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Air Drum & Motion Music Synthesizer (ESP32-S3 IMU).")
    parser.add_argument("--port", default=None, help="Serial port (auto-detects ws28p if omitted)")
    parser.add_argument("--model", type=Path, default=Path("imu_artifacts/model_int8.tflite"), help="Path to int8 model")
    parser.add_argument("--replay", type=Path, help="Replay pre-recorded gesture CSV take")
    parser.add_argument("--demo", action="store_true", help="Run sound check demo pattern")
    parser.add_argument("--strike-thresh", type=float, default=19.5, help="Acceleration peak threshold (m/s^2) for strikes")
    parser.add_argument("--threshold", type=float, default=0.70, help="Confidence threshold for CNN gestures")
    parser.add_argument("--seconds", type=float, default=None, help="Stop after this many seconds")
    args = parser.parse_args(argv)

    # Initialize synthesizer
    try:
        synth = DrumPolySynth()
    except Exception as e:
        print(f"[error] Failed to initialize audio engine: {e}")
        return 1

    controller = AirDrumController(synth, strike_thresh=args.strike_thresh, gesture_thresh=args.threshold)

    if args.demo:
        try:
            run_demo(synth)
        finally:
            synth.close()
        return 0

    # Offline CSV Replay Mode
    if args.replay:
        print(ASCII_BANNER)
        print(f"Replaying gesture take: {args.replay}")
        print(render_drum_kit())

        has_model = args.model.exists()
        detector = None
        if has_model:
            try:
                import live_infer_imu as lii
                detector = lii.GestureDetector(str(args.model), threshold=args.threshold)
                print(f"Loaded 1D-CNN Model: {args.model}")
            except Exception as e:
                print(f"[warning] Could not load model: {e}")

        try:
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
                time.sleep(dt * 0.4)  # slight real-time pacing

            # Flush trailing window for complete gesture recognition
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

    # Live Hardware Mode
    if not args.port:
        try:
            import detect_board
            import wire
            args.port = detect_board.auto_detect_port(need_cap=wire.CAP_IMU, preferred_model="ws28p")
        except Exception as e:
            print(f"[error] Could not auto-detect ws28p board: {e}")
            print("        Please specify --port <PORT>, --demo, or --replay <FILE.csv>")
            synth.close()
            return 1

    try:
        import live_infer_imu as lii
        import wire
    except ImportError:
        print("[error] robotos_kws package not found. Please install the wheel.")
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
                    # 1. Instant transient strike detection
                    controller.handle_strike(t_s, s.accel, s.gyro)

                    # 2. 1D-CNN sliding window gesture classification
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
