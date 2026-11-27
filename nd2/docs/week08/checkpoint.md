# Week 08 Checkpoint Quiz: Edge AI Software Architecture

![track](https://img.shields.io/badge/track-ND02-1d4ed8?style=flat-square)
![kind](https://img.shields.io/badge/kind-checkpoint-2e8b57?style=flat-square)

Test your understanding of consuming Edge AI models, designing real-time audio microservices, and reactive full-stack integration.

---

### Question 1: Programmatic Model Inference
When using `robotos_edge.Detector`, what is the primary difference between `.predict(wav_path)` and `.predict_proba(wav_path)`?
- A) `.predict()` works on PC microphone only; `.predict_proba()` works on serial hardware boards.
- B) `.predict()` returns the top predicted label and its confidence scalar; `.predict_proba()` returns a full dictionary mapping every class to its softmax probability.
- C) `.predict()` requires float32 models; `.predict_proba()` requires int8 quantized models.
- D) `.predict()` is asynchronous; `.predict_proba()` is blocking.

*(Answer: B)*

---

### Question 2: Real-Time Audio Streaming vs HTTP Polling
Why is a WebSocket connection preferred over periodic HTTP `GET` polling for real-time speech detection events?
- A) HTTP cannot transmit JSON data.
- B) WebSockets maintain a persistent full-duplex TCP socket, avoiding HTTP handshake overhead and allowing the server to push detected keyword events with sub-50 ms latency.
- C) WebSockets automatically run TensorFlow models on the client GPU.
- D) HTTP requests cannot read computer microphones.

*(Answer: B)*

---

### Question 3: Refractory Period in Speech Detection
In a continuous sliding-window detector (e.g. $200\text{ ms}$ hop, $1.0\text{ s}$ window), what is the purpose of a **refractory period** (e.g. $1000\text{ ms}$)?
- A) To cool down the computer CPU.
- B) To discard silent audio clips.
- C) To prevent a single spoken word from triggering multiple consecutive detections across overlapping sliding windows.
- D) To reset the model weights to random values.

*(Answer: C)*

---

### Question 4: Hot-Reloading in Production MLOps
When a background training worker (`robotos_edge.Trainer`) finishes training an updated int8 model, how should the backend service apply the update?
- A) Restart the entire operating system.
- B) Delete the database and clear all client browser cookies.
- C) Atomically instantiate a new `Detector("artifacts/model_int8.tflite")` instance and replace the server's global reference without terminating active WebSocket connections.
- D) Recompile Python from source code.

*(Answer: C)*
