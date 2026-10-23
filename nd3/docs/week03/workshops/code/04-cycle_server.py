#!/usr/bin/env python3
"""Workshop 04 — action server running a 5-step machine cycle."""
import time

import robotos
from robotos.messages.robotos.test.v1.echo_pb2 import (
    EchoRequest, EchoResponse)

ACT = "/machine/01/cycle"

with robotos.Node("cycle_server") as node:
    def handler(goal, ctx):
        for i in range(1, 6):
            if ctx.cancel_requested():            # client cancelled?
                return EchoResponse(text="aborted",
                                    sequence=goal.sequence)
            ctx.send_feedback(                    # progress update
                EchoRequest(text=f"step {i}/5"))
            time.sleep(1.0)                     # work takes time
        return EchoResponse(text="cycle complete",
                            sequence=goal.sequence)

    node.create_action(ACT, EchoRequest, EchoRequest,
                       EchoResponse, handler)
    print(f"serving {ACT} — Ctrl-C to stop")
    while True:
        time.sleep(1)
