"""FastAPI Edge AI Audio Service with robotos_kws.

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
from pathlib import Path
from typing import Dict, List, Optional

import uvicorn
from fastapi import FastAPI, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import robotos_kws as rk

app = FastAPI(
    title="RobotOS KWS Edge AI Microservice",
    description="Full-stack speech detection API and real-time WebSocket broadcaster powered by robotos_kws",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Active model path (looks for artifacts/model_int8.tflite locally or in nd1 labs)
MODEL_PATHS = [
    Path("artifacts/model_int8.tflite"),
    Path("../../../nd1/docs/week08/labs/python/artifacts/model_int8.tflite"),
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
    try:
        await websocket.send_json({
            "event": "connected",
            "message": "Connected to real-time KWS stream.",
            "labels": detector.labels if detector else [],
        })
        while True:
            # Keep socket alive
            await websocket.receive_text()
    except WebSocketDisconnect:
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
