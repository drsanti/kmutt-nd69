#!/usr/bin/env python3
"""Workshop 07 — mini digital twin: mirrors machine state, sends commands."""
import time

import robotos
from robotos.messages.robotos.sensor.v1.imu_pb2 import Imu

STATE, CMD = "/machine/01/state", "/machine/01/cmd"
mirror = {"speed": None, "stamp": None}


def watch(seconds):
    """Print the mirrored speed once a second."""
    for _ in range(seconds):
        if mirror["speed"] is not None:
            print(f"  twin sees speed={mirror['speed']:.2f}")
        time.sleep(1)


with robotos.Node("twin") as node:
    def on_state(msg, meta):
        mirror["speed"] = msg.acceleration.x
        mirror["stamp"] = msg.timestamp_ns
    node.create_subscriber(STATE, Imu).on_message(on_state)
    cmd = node.create_publisher(CMD, Imu)

    watch(5)                      # idle — speed sits at 0.0

    print("twin sends START")
    cmd.publish(Imu(frame_id="START"))
    watch(8)                      # speed ramps 0.1 -> 1.0

    print("twin sends STOP")
    cmd.publish(Imu(frame_id="STOP"))
    watch(6)                      # speed decays back to 0.0
