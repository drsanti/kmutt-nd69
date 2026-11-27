"""FastAPI Edge AI Audio Service with robotos_edge.

Exposes:
- GET  /api/v1/model/info   : Model metadata and labels
- POST /api/v1/classify     : Multipart WAV upload classification
- WS   /ws/kws              : Real-time speech detection WebSocket broadcast
- GET  /                    : Serves interactive Voice Dashboard
"""
from __future__ import annotations

import asyncio
import io
import os
import tempfile
import threading
from collections import deque
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import uvicorn
from fastapi import FastAPI, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from robotos_edge.audio import features as kc
import robotos_edge as rk

app = FastAPI(
    title="RobotOS KWS Edge AI Microservice",
    description="Full-stack speech detection API and real-time WebSocket broadcaster powered by robotos_edge",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app_dir = Path(__file__).resolve().parent
repo_root = app_dir.parents[4]

# Active model path (looks for artifacts locally or in nd1 labs)
MODEL_PATHS = [
    app_dir / "artifacts" / "model_int8.tflite",
    repo_root / "nd1" / "docs" / "week08" / "labs" / "python" / "artifacts" / "model_int8.tflite",
]
active_model_path = next((p for p in MODEL_PATHS if p.exists()), None)

detector: Optional[rk.Detector] = None
if active_model_path:
    try:
        detector = rk.Detector(str(active_model_path), threshold=0.80)
        print(f"[app] Loaded KWS Detector from {active_model_path}")
    except Exception as e:
        print(f"[app] Warning: Failed to load model: {e}")
else:
    print("[app] Warning: model_int8.tflite not found. Run training or copy artifacts.")


class ModelInfoResponse(BaseModel):
    model_path: str
    labels: List[str]
    threshold: float
    status: str


class ClassificationResponse(BaseModel):
    top_class: str
    confidence: float
    probabilities: Dict[str, float]


class ThresholdUpdateRequest(BaseModel):
    threshold: float


class SimulateRequest(BaseModel):
    keyword: str
    confidence: float = 0.95


# Connected WebSocket clients
connected_clients: List[WebSocket] = []
loop: Optional[asyncio.AbstractEventLoop] = None


@app.on_event("startup")
async def startup_event():
    global loop
    loop = asyncio.get_running_loop()
    # Start background listener thread if detector is available
    if detector:
        t = threading.Thread(target=background_audio_listener, daemon=True)
        t.start()


def background_audio_listener():
    """Background thread reading continuous mic stream and notifying WebSocket clients."""
    global detector, loop
    if not detector:
        return
    print("[stream] Background mic stream listener started.")
    try:
        for keyword, confidence, timestamp in detector.stream_pc():
            payload = {
                "event": "keyword_detected",
                "keyword": keyword,
                "confidence": round(float(confidence), 3),
                "timestamp": round(float(timestamp), 2),
            }
            if loop and connected_clients:
                asyncio.run_coroutine_threadsafe(broadcast_event(payload), loop)
    except Exception as e:
        print(f"[stream] Audio stream stopped: {e}")


async def broadcast_event(data: dict):
    """Broadcast JSON payload to all connected WebSocket clients."""
    for ws in list(connected_clients):
        try:
            await ws.send_json(data)
        except Exception:
            if ws in connected_clients:
                connected_clients.remove(ws)


@app.get("/api/v1/model/info", response_model=ModelInfoResponse)
def get_model_info():
    if not detector:
        raise HTTPException(status_code=503, detail="Detector model not loaded.")
    return ModelInfoResponse(
        model_path=str(detector.model_path),
        labels=detector.labels,
        threshold=detector.threshold,
        status="ready",
    )


@app.post("/api/v1/model/threshold")
async def update_threshold(req: ThresholdUpdateRequest):
    """Dynamically set the detection confidence threshold."""
    if not detector:
        raise HTTPException(status_code=503, detail="Detector model not loaded.")
    if not (0.01 <= req.threshold <= 1.0):
        raise HTTPException(status_code=400, detail="Threshold must be between 0.01 and 1.0")
    detector.threshold = round(float(req.threshold), 3)
    payload = {
        "event": "threshold_updated",
        "threshold": detector.threshold,
    }
    if loop and connected_clients:
        await broadcast_event(payload)
    return {"status": "ok", "threshold": detector.threshold}


@app.post("/api/v1/simulate")
async def simulate_keyword(req: SimulateRequest):
    """Simulate a keyword trigger to test SCADA interlocks without mic hardware."""
    kw = req.keyword.lower().strip()
    valid_kws = ["red", "green", "blue", "off", "_silence_", "_unknown_"]
    if kw not in valid_kws:
        raise HTTPException(status_code=400, detail=f"Invalid keyword. Must be one of: {valid_kws}")
    payload = {
        "event": "keyword_detected",
        "keyword": kw,
        "confidence": round(float(req.confidence), 3),
        "timestamp": 0.0,
        "source": "simulated",
    }
    if loop and connected_clients:
        await broadcast_event(payload)
    return {"status": "ok", "payload": payload}


@app.get("/api/v1/sample-audio")
def get_sample_audio():
    """Serves the built-in sample WAV clip for quick one-click REST testing."""
    candidates = [
        Path(__file__).parent / "sample_audio.wav",
        Path("sample_audio.wav"),
        Path(__file__).parent.parent.parent.parent / "nd1" / "docs" / "week08" / "labs" / "python" / "sample_audio.wav",
    ]
    p = next((c for c in candidates if c.exists()), None)
    if p:
        return FileResponse(p, media_type="audio/wav", filename="sample_audio.wav")
    raise HTTPException(status_code=404, detail="sample_audio.wav not found.")


@app.post("/api/v1/classify", response_model=ClassificationResponse)
async def classify_audio(file: UploadFile = File(...)):
    if not detector:
        raise HTTPException(status_code=503, detail="Detector model not loaded.")

    # Save uploaded file to temp file
    suffix = Path(file.filename).suffix or ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        top_label, confidence = detector.predict(tmp_path)
        probs = detector.predict_proba(tmp_path)
        return ClassificationResponse(
            top_class=top_label,
            confidence=float(confidence),
            probabilities={k: float(v) for k, v in probs.items()},
        )
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@app.websocket("/ws/kws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)

    # Per-client sliding window ring buffer for live browser mic streaming
    client_ring = np.zeros(kc.CLIP_SAMPLES, dtype=np.int16)
    client_history = deque(maxlen=3)
    client_since_detection = kc.SAMPLE_RATE  # allow immediate detection
    samples_seen = 0

    try:
        await websocket.send_json({
            "event": "connected",
            "message": "Connected to real-time KWS stream.",
            "labels": detector.labels if detector else [],
            "threshold": detector.threshold if detector else 0.80,
        })
        while True:
            msg = await websocket.receive()
            if msg["type"] == "websocket.disconnect":
                break

            if "bytes" in msg and msg["bytes"]:
                raw_bytes = msg["bytes"]
                chunk = np.frombuffer(raw_bytes, dtype="<i2")
                if len(chunk) == 0:
                    continue

                # Slide ring buffer (16000 samples = 1 second)
                if len(chunk) >= kc.CLIP_SAMPLES:
                    client_ring = chunk[-kc.CLIP_SAMPLES:].copy()
                else:
                    client_ring = np.concatenate([client_ring[len(chunk):], chunk])

                samples_seen += len(chunk)
                client_since_detection += len(chunk)

                if detector:
                    # Feature extraction & inference
                    feats = kc.log_mel(client_ring)
                    probs = kc.run_tflite(detector.interpreter, feats)
                    client_history.append(probs)
                    avg_probs = np.mean(client_history, axis=0)

                    top_idx = int(np.argmax(avg_probs))
                    top_label = detector.labels[top_idx]
                    top_score = float(avg_probs[top_idx])
                    rms_db = float(kc.rms_dbfs(chunk))

                    probs_dict = {lb: float(avg_probs[i]) for i, lb in enumerate(detector.labels)}

                    # Trigger state transition if above threshold and keyword
                    triggered = False
                    if (top_label in detector.keywords and 
                        top_score >= detector.threshold and 
                        client_since_detection >= detector.refractory_samples):
                        client_since_detection = 0
                        triggered = True

                    resp = {
                        "event": "live_stream_update",
                        "probabilities": probs_dict,
                        "top_class": top_label,
                        "confidence": round(top_score, 3),
                        "rms_dbfs": round(rms_db, 1),
                        "triggered": triggered,
                        "keyword": top_label if triggered else None,
                        "timestamp": round(samples_seen / kc.SAMPLE_RATE, 2),
                    }
                    await websocket.send_json(resp)
                    if triggered:
                        # Also broadcast to any other monitoring dashboards
                        await broadcast_event({
                            "event": "keyword_detected",
                            "keyword": top_label,
                            "confidence": round(top_score, 3),
                            "timestamp": round(samples_seen / kc.SAMPLE_RATE, 2),
                            "source": "browser_stream",
                        })
            elif "text" in msg and msg["text"]:
                # Keep alive or text command
                pass
    except WebSocketDisconnect:
        pass
    finally:
        if websocket in connected_clients:
            connected_clients.remove(websocket)


# Serve Static UI
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.get("/")
    def serve_index():
        return FileResponse(static_dir / "index.html")


if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
