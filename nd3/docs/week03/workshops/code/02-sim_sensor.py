#!/usr/bin/env python3
"""Workshop 02 — simulated sensor publishing Imu at 10 Hz."""
import random
import time

import robotos
from robotos.messages.robotos.sensor.v1.imu_pb2 import Imu

TOPIC = "/machine/01/sensor/imu"

with robotos.Node("sim_sensor") as node:
    pub = node.create_publisher(TOPIC, Imu)
    print(f"publishing on {TOPIC} — Ctrl-C to stop")
    while True:
        pub.publish(Imu(
            timestamp_ns=time.time_ns(),
            frame_id="imu_01",
            acceleration={"x": 0.0, "y": 0.0, "z": 9.81},
            angular_velocity={"x": random.uniform(-1, 1)},
        ))
        time.sleep(0.1)          # 10 Hz
