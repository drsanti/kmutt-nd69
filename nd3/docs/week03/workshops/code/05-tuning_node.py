#!/usr/bin/env python3
"""Workshop 05 — node with parameters, editable live via CLI."""
import time

import robotos

with robotos.Node("tuning_node") as node:
    node.declare_parameter("setpoint", 42)        # i64/f64/bool/string
    node.declare_parameter("mode", "auto")
    node.set_allow_remote_params(True)            # let CLI write them

    print("running — change params from the CLI")
    while True:
        sp = node.param_get("setpoint")
        mode = node.param_get("mode")
        print(f"  setpoint={sp}  mode={mode}")
        time.sleep(2)
