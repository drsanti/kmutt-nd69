#!/usr/bin/env python3
"""Workshop 03 — service client calling /test/echo."""
import time

import robotos
from robotos.messages.robotos.test.v1.echo_pb2 import (
    EchoRequest, EchoResponse)

SVC = "/test/echo"

with robotos.Node("client") as node:
    for attempt in range(30):
        try:
            resp = node.call(
                SVC, EchoRequest, EchoResponse,
                EchoRequest(text="hello robotos", sequence=1),
                timeout_ms=2000)
            print(f"reply: '{resp.text}' (seq {resp.sequence})")
            break
        except robotos.RobotosError as e:
            if e.status != 10:     # UNAVAILABLE — server not up yet
                raise
            time.sleep(0.3)
    else:
        print("no responder")
