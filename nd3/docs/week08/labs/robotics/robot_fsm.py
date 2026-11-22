#!/usr/bin/env python3
"""Robotic Finite State Machine (FSM) driven by real-time IMU motion recognition.

States:
- STANDBY        : Normal idle state, waiting for commands.
- ACTIVE_PATROL  : Autonomous navigation routine (triggered by 'circle').
- EMERGENCY_STOP : High-priority safety shutdown (triggered by 'shake' / collision).
- TRANSPORT_MODE : Robot lifted off the ground (triggered by 'lift').

Usage:
    python robot_fsm.py --port COM17 --model imu_artifacts/model_int8.tflite
    python robot_fsm.py --replay sample_gesture.csv
"""
from __future__ import annotations

import argparse
import sys
import time
from enum import Enum
from pathlib import Path


class RobotState(Enum):
    STANDBY = "STANDBY"
    ACTIVE_PATROL = "ACTIVE_PATROL"
    EMERGENCY_STOP = "EMERGENCY_STOP"
    TRANSPORT_MODE = "TRANSPORT_MODE"


class RobotController:
    def __init__(self):
        self.state = RobotState.STANDBY
        print(f"\n[ROBOT FSM] Initialized. Current State: {self.state.value}")

    def transition(self, new_state: RobotState, reason: str):
        if self.state == new_state:
            return
        old = self.state.value
        self.state = new_state
        print("\n" + "=" * 50)
        print(f" [FSM TRANSITION] {old}  ==>  {self.state.value}")
        print(f" Reason: {reason}")
        print("=" * 50 + "\n")

        # Execute robotic actuator actions
        if self.state == RobotState.EMERGENCY_STOP:
            self._actuator_emergency_stop()
        elif self.state == RobotState.ACTIVE_PATROL:
            self._actuator_start_patrol()
        elif self.state == RobotState.TRANSPORT_MODE:
            self._actuator_transport_mode()
        elif self.state == RobotState.STANDBY:
            self._actuator_standby()

    def handle_gesture(self, gesture: str, confidence: float):
        print(f"  [IMU Event] Detected '{gesture}' (confidence: {confidence:.1%})")

        # Emergency Stop takes absolute precedence
        if gesture == "shake":
            self.transition(RobotState.EMERGENCY_STOP, f"Violent vibration / collision detected ({confidence:.1%})")
        elif gesture == "lift":
            self.transition(RobotState.TRANSPORT_MODE, f"Robot chassis lifted off floor ({confidence:.1%})")
        elif gesture == "circle":
            if self.state in (RobotState.STANDBY, RobotState.TRANSPORT_MODE):
                self.transition(RobotState.ACTIVE_PATROL, f"User circle gesture dispatched ({confidence:.1%})")
            elif self.state == RobotState.EMERGENCY_STOP:
                print("  [FSM Alert] Cannot start patrol: Emergency Stop must be reset first!")
        elif gesture == "idle":
            if self.state == RobotState.TRANSPORT_MODE:
                self.transition(RobotState.STANDBY, "Robot placed back onto surface.")
            elif self.state == RobotState.EMERGENCY_STOP:
                self.transition(RobotState.STANDBY, "Motion stabilized: Emergency Stop cleared, returning to STANDBY.")

    def _actuator_emergency_stop(self):
        print("  >> [ACTUATOR] Motors: IMMEDIATE BRAKE | Relay: OPEN | LED: RED PULSE")

    def _actuator_start_patrol(self):
        print("  >> [ACTUATOR] Motors: SPEED=80 RPM | Navigation: LIDAR ACTIVE | LED: GREEN")

    def _actuator_transport_mode(self):
        print("  >> [ACTUATOR] Motors: DISENGAGED (COAST) | Wheel Encoders: PAUSED | LED: BLUE")

    def _actuator_standby(self):
        print("  >> [ACTUATOR] Motors: OFF | Low-Power Mode | LED: OFF")


def main():
    parser = argparse.ArgumentParser(description="Robotic FSM controller driven by IMU telemetry.")
    parser.add_argument("--port", default=None, help="Serial port, e.g. COM17 or /dev/ttyACM0 (auto-detects if omitted)")
    parser.add_argument("--model", type=Path, default=Path("imu_artifacts/model_int8.tflite"), help="Path to int8 model")
    parser.add_argument("--replay", type=Path, help="Replay CSV take instead of connecting to real board")
    args = parser.parse_args()

    controller = RobotController()

    if args.replay:
        print(f"Replaying sample gesture file: {args.replay}")
        if args.model.exists():
            try:
                import imu_common as ic
                import live_infer_imu as lii

                print(f"Using trained model: {args.model}")
                detector = lii.GestureDetector(str(args.model), threshold=0.70)
                rows = ic.load_window(args.replay)
                t = 0.0
                detected_any = False
                for row in rows:
                    detector.push(t, row[:3], row[3:])
                    t += 1 / ic.RATE_HZ
                    if detector.detections:
                        detected_any = True
                        _, label, score = detector.detections.pop()
                        controller.handle_gesture(label, score)
                # Flush trailing window
                for _ in range(ic.WINDOW):
                    detector.push(t, (0, 0, ic.G), (0, 0, 0))
                    t += 1 / ic.RATE_HZ
                    if detector.detections:
                        detected_any = True
                        _, label, score = detector.detections.pop()
                        controller.handle_gesture(label, score)
                if not detected_any:
                    print("  [Notice] No gesture exceeded 70% threshold in replay file.")
                return 0
            except Exception as e:
                print(f"[warning] Error running model replay: {e}. Falling back to demo sequence.")

        print("[info] Running FSM demonstration sequence...")
        time.sleep(1.0)
        controller.handle_gesture("circle", 0.94)
        time.sleep(1.5)
        controller.handle_gesture("shake", 0.98)
        time.sleep(1.5)
        controller.handle_gesture("lift", 0.92)
        time.sleep(1.5)
        controller.handle_gesture("idle", 0.88)
        return 0

    if not args.port:
        try:
            import detect_board
            import wire
            args.port = detect_board.auto_detect_port(need_cap=wire.CAP_IMU, preferred_model="ws28p")
        except Exception as e:
            print(f"[error] Could not auto-detect ws28p board: {e}")
            print("        Please specify --port <PORT> or --replay <FILE.csv>")
            return 1

    try:
        import live_infer_imu as lii
        import wire
    except ImportError:
        print("[error] robotos_kws package not found. Please install the wheel from ../dist/")
        return 1

    if not args.model.exists():
        print(f"[warning] Model {args.model} not found. Running with simulated detections...")
        controller.handle_gesture("circle", 0.92)
        time.sleep(2.0)
        controller.handle_gesture("shake", 0.96)
        time.sleep(2.0)
        controller.handle_gesture("idle", 0.90)
        return 0

    print(f"Connecting to ws28p board on {args.port}...")
    try:
        sess = wire.BoardSession.open(args.port)
    except wire.WireError as e:
        print(f"[error] {e}")
        return 2

    detector = lii.GestureDetector(str(args.model), threshold=0.70)

    try:
        sess.wait_board_info(need_cap=wire.CAP_IMU, need_name="robot_fsm.py")
        print("Connected! Listening to 50 Hz IMU stream. Move the board (Ctrl+C to exit)...")
        while True:
            for f in sess.poll(0.05):
                if f.msg_type == wire.MSG_IMU:
                    s = wire.decode_imu(f.payload)
                    t_s = s.timestamp_ns * 1e-9 if s.timestamp_ns else time.monotonic()
                    detector.push(t_s, s.accel, s.gyro)

                    if detector.detections:
                        _, label, score = detector.detections.pop()
                        controller.handle_gesture(label, score)
    except KeyboardInterrupt:
        print("\nStopping controller.")
    except Exception as e:
        print(f"[error] {e}")
        return 1
    finally:
        sess.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
