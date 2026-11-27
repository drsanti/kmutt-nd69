"""Gesture service for Week 09 Lab 9.5 — your Week 08 IMU model behind a WebSocket.

The model runs here, in Python (TensorFlow Lite + robotos_edge). A Node.js client sends IMU
samples and gets the class probabilities back, the same split as a real product: an ML
service next to the device gateway.

    python gesture_service.py                      # ws://127.0.0.1:8765/ws
    python gesture_service.py --model path/to/model_int8.tflite --port 8765

Protocol (JSON text messages):
    client -> service  {"samples": [[t, ax, ay, az, gx, gy, gz], ...]}   t in s, accel m/s^2, gyro rad/s
                       {"threshold": 0.8}                                 change the detection threshold
    service -> client  {"gestures": [...], "threshold": 0.7}              once, on connect
                       {"probs": {"idle": 0.9, ...}, "detections": [[t, label, p], ...]}   after each batch
"""
import argparse
import asyncio
import json
from pathlib import Path

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

import robotos_edge as rk
from robotos_edge.imu import features as ic

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--model", default="imu_artifacts/model_int8.tflite", help="TFLite gesture model (Week 08)")
ap.add_argument("--host", default="127.0.0.1")
ap.add_argument("--port", type=int, default=8765)
ap.add_argument("--threshold", type=float, default=0.7)
args = ap.parse_args()

MODEL = Path(args.model)
if not MODEL.exists():
    raise SystemExit(f"{MODEL} not found — train one first:  robotos-kws train-imu --synthetic --out imu_artifacts")

rk.GestureDetector(str(MODEL), threshold=args.threshold, verbose=False)   # load TensorFlow once, at start
app = FastAPI(title="ND02 gesture service")


@app.get("/")
def info():
    return {"model": str(MODEL), "gestures": list(ic.GESTURES), "websocket": "/ws"}


@app.websocket("/ws")
async def ws(sock: WebSocket):
    await sock.accept()
    await sock.send_text(json.dumps({"gestures": list(ic.GESTURES), "threshold": args.threshold}))
    det = rk.GestureDetector(str(MODEL), threshold=args.threshold, verbose=False)   # one per client
    sent = 0
    print("client connected", flush=True)
    try:
        while True:
            msg = json.loads(await sock.receive_text())
            if "threshold" in msg:
                det.threshold = float(msg["threshold"])
                await sock.send_text(json.dumps({"threshold": det.threshold}))
            rows = msg.get("samples") or []
            for t, ax, ay, az, gx, gy, gz in rows:
                det.push(t, (ax, ay, az), (gx, gy, gz))
            if rows:
                new = [[t, label, round(p, 3)] for t, label, p in det.detections[sent:]]
                sent = len(det.detections)
                for t, label, p in new:
                    print(f"  {t:7.2f} s  {label:<6} p={p:.2f}", flush=True)
                await sock.send_text(json.dumps({"probs": {g: round(det.probs[g], 4) for g in ic.GESTURES},
                                                 "detections": new}))
            await asyncio.sleep(0)
    except WebSocketDisconnect:
        print("client left", flush=True)


if __name__ == "__main__":
    print(f"gesture service: model {MODEL}, ws://{args.host}:{args.port}/ws  (Ctrl+C to stop)", flush=True)
    uvicorn.run(app, host=args.host, port=args.port, log_level="warning")
