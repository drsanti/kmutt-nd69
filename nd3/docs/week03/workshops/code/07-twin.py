#!/usr/bin/env python3
"""Workshop 07 — mini digital twin: mirrors machine state, sends commands."""
import time

import robotos
from robotos.messages.robotos.sensor.v1.imu_pb2 import Imu

STATE, CMD = "/machine/01/state", "/machine/01/cmd"
mirror = {"speed": None, "stamp": None}

with robotos.Node("twin") as node:
    def on_state(msg, meta):
        mirror["speed"] = msg.acceleration.x
        mirror["stamp"] = msg.timestamp_ns
    node.create_subscriber(STATE, Imu).on_message(on_state)
    cmd = node.create_publisher(CMD, Imu)

    for _ in range(10):
        if mirror["speed"] is not None:
            print(f"  twin sees speed={mirror['speed']:.2f}")
        time.sleep(1)

    print("twin sends START")
    cmd.publish(Imu(frame_id="START"))
    time.sleep(5)

    print("twin sends STOP")
    cmd.publish(Imu(frame_id="STOP"))
    time.sleep(3)
