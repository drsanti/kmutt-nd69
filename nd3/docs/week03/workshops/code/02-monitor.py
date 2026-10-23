#!/usr/bin/env python3
"""Workshop 02 — subscriber printing Imu values as they arrive."""
import robotos
from robotos.messages.robotos.sensor.v1.imu_pb2 import Imu

TOPIC = "/machine/01/sensor/imu"

with robotos.Node("monitor") as node:
    sub = node.create_subscriber(TOPIC, Imu)
    sub.on_message(lambda msg, meta: print(
        f"acc.z={msg.acceleration.z:.2f}  gyro.x={msg.angular_velocity.x:+.3f}"))
    input("subscribed — press Enter to stop")
