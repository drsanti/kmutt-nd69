#!/usr/bin/env python3
"""Workshop 07 — simulated machine: publishes state, obeys commands."""
import threading
import time

import robotos
from robotos.messages.robotos.sensor.v1.imu_pb2 import Imu

STATE, CMD = "/machine/01/state", "/machine/01/cmd"
state = {"speed": 0.0, "running": False}
lock = threading.Lock()

with robotos.Node("machine") as node:
    pub = node.create_publisher(STATE, Imu)

    def on_cmd(msg, meta):
        with lock:
            if "START" in msg.frame_id:
                state["running"] = True
            elif "STOP" in msg.frame_id:
                state["running"] = False
    node.create_subscriber(CMD, Imu).on_message(on_cmd)

    while True:
        with lock:
            if state["running"]:
                state["speed"] = min(1.0, state["speed"] + 0.1)
            else:
                state["speed"] = max(0.0, state["speed"] - 0.2)
            v = state["speed"]
        pub.publish(Imu(timestamp_ns=time.time_ns(),
                        frame_id="machine_01",
                        acceleration={"x": v}))   # speed → acc.x
        time.sleep(0.2)
