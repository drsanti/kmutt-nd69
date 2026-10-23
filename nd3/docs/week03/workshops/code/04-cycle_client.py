#!/usr/bin/env python3
"""Workshop 04 — action client: send goal, watch feedback, get result."""
import time

import robotos
from robotos.messages.robotos.test.v1.echo_pb2 import (
    EchoRequest, EchoResponse)

ACT = "/machine/01/cycle"

with robotos.Node("cycle_client") as node:
    cli = node.action_client(ACT, EchoRequest, EchoRequest,
                             EchoResponse)

    goal_id = None
    for _ in range(30):                       # wait for server
        try:
            goal_id = cli.send_goal(
                EchoRequest(text="start cycle", sequence=1),
                timeout_ms=500)
            break
        except robotos.RobotosError as e:
            if e.status != 10:                # UNAVAILABLE → retry
                raise
            time.sleep(0.3)
    print(f"goal accepted: {goal_id}")

    deadline = time.time() + 15
    while time.time() < deadline:
        fb = cli.feedback_recv(goal_id, 300)
        if fb is not None:
            print(f"  feedback: {fb.text}")
        try:
            state, res = cli.result(goal_id, 10)
            print(f"result: {state.name} — '{res.text}'")
            break
        except robotos.RobotosError:
            continue                          # still running
    cli.close()
