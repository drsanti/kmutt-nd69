#!/usr/bin/env python3
"""Workshop 03 — echo service server."""
import time

import robotos
from robotos.messages.robotos.test.v1.echo_pb2 import (
    EchoRequest, EchoResponse)

SVC = "/test/echo"

with robotos.Node("echo_server") as node:
    def echo(req: EchoRequest) -> EchoResponse:
        print(f"request: '{req.text}' (seq {req.sequence})")
        return EchoResponse(text=req.text, sequence=req.sequence)

    node.create_service(SVC, EchoRequest, EchoResponse, echo)
    print(f"serving {SVC} — Ctrl-C to stop")
    while True:
        time.sleep(1)
