"""Shared settings and the feature pipeline for the Week 08 keyword-spotting labs.

Every script (collect, train, evaluate, live PC inference, C-array export) imports
this module, so the training features and the on-device features come from ONE
definition. The firmware file ``kws-inference/main/kws_features.c`` implements the
same steps in C; ``verify_c_features.py`` compiles that C file on your computer and
checks that both produce the same numbers.

Pipeline (1 s clip -> 49 x 40 log-mel matrix):
    int16 PCM, 16 kHz, mono, 16000 samples
    -> float32 in [-1, 1)          (x / 32768)
    -> remove DC                   (subtract the clip mean)
    -> 49 frames of 480 samples    (30 ms window, 20 ms hop, no padding)
    -> periodic Hann window
    -> 512-point FFT, power spectrum (257 bins)
    -> 40 triangular mel filters, 20-7600 Hz (HTK mel scale)
    -> natural log(energy + 1e-6)
"""
from __future__ import annotations

import os
import re
import wave
from dataclasses import dataclass
from pathlib import Path

import numpy as np

# ---------------------------------------------------------------- settings
SAMPLE_RATE = 16000
CLIP_SAMPLES = 16000          # 1.0 s
FRAME_LEN = 480               # 30 ms
FRAME_STEP = 320              # 20 ms
FFT_LEN = 512
NUM_MEL = 40
MEL_FMIN = 20.0
MEL_FMAX = 7600.0
LOG_EPS = 1e-6
NUM_FRAMES = 1 + (CLIP_SAMPLES - FRAME_LEN) // FRAME_STEP   # 49

# Class order is part of the model contract: the firmware uses the same order.
KEYWORDS = ["red", "green", "blue", "off"]
SILENCE = "_silence_"
UNKNOWN = "_unknown_"
LABELS = KEYWORDS + [SILENCE, UNKNOWN]

# File name convention used by every collector:
#   <label>/<session>_<speaker>_<device>_<index>.wav
#   e.g.  red/s01_spk03_board_0007.wav     green/s02_alice_pc_0012.wav
FILENAME_RE = re.compile(
    r"^(?P<session>s\d+)_(?P<speaker>[A-Za-z0-9-]+)_(?P<device>board|pc|synth)_(?P<index>\d+)\.wav$"
)


# ---------------------------------------------------------------- wav I/O
def read_wav(path: str | os.PathLike) -> np.ndarray:
    """Read a 16-bit mono 16 kHz wav file and return int16 samples."""
    with wave.open(str(path), "rb") as w:
        if w.getsampwidth() != 2 or w.getnchannels() != 1 or w.getframerate() != SAMPLE_RATE:
            raise ValueError(
                f"{path}: expected 16-bit mono {SAMPLE_RATE} Hz, got "
                f"{8 * w.getsampwidth()}-bit, {w.getnchannels()} ch, {w.getframerate()} Hz"
            )
        data = w.readframes(w.getnframes())
    return np.frombuffer(data, dtype="<i2").astype(np.int16)


def write_wav(path: str | os.PathLike, pcm: np.ndarray) -> None:
    """Write int16 samples as a 16-bit mono 16 kHz wav file."""
    pcm = np.asarray(pcm, dtype=np.int16)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        w.writeframes(pcm.astype("<i2").tobytes())


def float_to_int16(x: np.ndarray) -> np.ndarray:
    """Convert float audio in [-1, 1] to int16 with clipping."""
    return np.clip(np.round(np.asarray(x) * 32767.0), -32768, 32767).astype(np.int16)


def fit_length(pcm: np.ndarray, n: int = CLIP_SAMPLES) -> np.ndarray:
    """Zero-pad or crop (from the start) to exactly n samples."""
    pcm = np.asarray(pcm)
    if len(pcm) >= n:
        return pcm[:n]
    return np.pad(pcm, (0, n - len(pcm)))


def center_on_energy(pcm: np.ndarray, n: int = CLIP_SAMPLES) -> np.ndarray:
    """Pick the n-sample window with the most energy (used to trim 1.5 s recordings to 1 s).

    Both the board collector and the PC-mic collector call this, so clips from either
    source are aligned the same way.
    """
    pcm = np.asarray(pcm)
    if len(pcm) <= n:
        return fit_length(pcm, n)
    x = pcm.astype(np.float64)
    x -= x.mean()
    energy = np.concatenate([[0.0], np.cumsum(x * x)])
    window_energy = energy[n:] - energy[:-n]
    start = int(np.argmax(window_energy))
    return pcm[start:start + n]


def rms_dbfs(pcm: np.ndarray) -> float:
    x = np.asarray(pcm, dtype=np.float64) / 32768.0
    return float(20 * np.log10(np.sqrt(np.mean(x * x)) + 1e-6))


# ---------------------------------------------------------------- features
def _hz_to_mel(f):
    return 2595.0 * np.log10(1.0 + np.asarray(f, dtype=np.float64) / 700.0)


def _mel_to_hz(m):
    return 700.0 * (10.0 ** (np.asarray(m, dtype=np.float64) / 2595.0) - 1.0)


def hann_window() -> np.ndarray:
    """Periodic Hann window of FRAME_LEN samples (same formula as the C code)."""
    n = np.arange(FRAME_LEN, dtype=np.float64)
    return (0.5 - 0.5 * np.cos(2.0 * np.pi * n / FRAME_LEN)).astype(np.float32)


def mel_filterbank() -> np.ndarray:
    """Return a (NUM_MEL, FFT_LEN//2+1) float32 matrix of triangular mel filters.

    Triangles are defined in continuous frequency (not rounded to FFT bins), which is
    easy to reproduce exactly in C.
    """
    n_bins = FFT_LEN // 2 + 1
    bin_hz = np.arange(n_bins, dtype=np.float64) * SAMPLE_RATE / FFT_LEN
    edges_hz = _mel_to_hz(np.linspace(_hz_to_mel(MEL_FMIN), _hz_to_mel(MEL_FMAX), NUM_MEL + 2))
    fb = np.zeros((NUM_MEL, n_bins), dtype=np.float64)
    for m in range(NUM_MEL):
        lo, center, hi = edges_hz[m], edges_hz[m + 1], edges_hz[m + 2]
        up = (bin_hz - lo) / (center - lo)
        down = (hi - bin_hz) / (hi - center)
        fb[m] = np.maximum(0.0, np.minimum(up, down))
    return fb.astype(np.float32)


_WINDOW = hann_window()
_MEL_FB = mel_filterbank()


def log_mel(pcm: np.ndarray) -> np.ndarray:
    """Compute the (NUM_FRAMES, NUM_MEL) float32 log-mel matrix of one 1 s int16 clip."""
    pcm = fit_length(np.asarray(pcm), CLIP_SAMPLES)
    x = pcm.astype(np.float32) / 32768.0
    x = x - x.mean(dtype=np.float32)
    idx = np.arange(FRAME_LEN)[None, :] + FRAME_STEP * np.arange(NUM_FRAMES)[:, None]
    frames = x[idx] * _WINDOW[None, :]
    spec = np.fft.rfft(frames, n=FFT_LEN, axis=1)
    power = (spec.real ** 2 + spec.imag ** 2).astype(np.float32)
    mel = power @ _MEL_FB.T
    return np.log(mel + LOG_EPS).astype(np.float32)


def batch_log_mel(clips) -> np.ndarray:
    """Features for many clips, shaped (N, NUM_FRAMES, NUM_MEL, 1) for the CNN."""
    return np.stack([log_mel(c) for c in clips])[..., None].astype(np.float32)


# ---------------------------------------------------------------- dataset
@dataclass
class Clip:
    path: Path
    label: str
    session: str
    speaker: str
    device: str


def scan_dataset(root: str | os.PathLike, strict: bool = True) -> list[Clip]:
    """List all clips under root/<label>/*.wav that follow the naming convention."""
    root = Path(root)
    clips: list[Clip] = []
    for label in LABELS:
        folder = root / label
        if not folder.is_dir():
            continue
        for p in sorted(folder.glob("*.wav")):
            m = FILENAME_RE.match(p.name)
            if not m:
                if strict:
                    print(f"[skip] {p} does not match <session>_<speaker>_<device>_<index>.wav")
                continue
            clips.append(Clip(p, label, m["session"], m["speaker"], m["device"]))
    return clips


def next_index(folder: Path, session: str, speaker: str, device: str) -> int:
    """Next free clip index for this session/speaker/device in a label folder."""
    prefix = f"{session}_{speaker}_{device}_"
    used = [int(p.stem[len(prefix):]) for p in folder.glob(prefix + "*.wav") if p.stem[len(prefix):].isdigit()]
    return max(used, default=-1) + 1


def clip_path(root: Path, label: str, session: str, speaker: str, device: str) -> Path:
    folder = Path(root) / label
    folder.mkdir(parents=True, exist_ok=True)
    i = next_index(folder, session, speaker, device)
    return folder / f"{session}_{speaker}_{device}_{i:04d}.wav"


def split_of(speaker: str, val_speakers: set[str], test_speakers: set[str]) -> str:
    """Speaker-disjoint split: a speaker's clips never appear in two splits."""
    if speaker in test_speakers:
        return "test"
    if speaker in val_speakers:
        return "val"
    return "train"


# ---------------------------------------------------------------- TFLite helpers
def make_interpreter(model_path: str | os.PathLike):
    """Create a TFLite interpreter (LiteRT if installed, otherwise tf.lite)."""
    try:
        from ai_edge_litert.interpreter import Interpreter  # pip install ai-edge-litert
    except ImportError:
        import tensorflow as tf
        Interpreter = tf.lite.Interpreter
    interp = Interpreter(model_path=str(model_path))
    interp.allocate_tensors()
    return interp


def run_tflite(interp, features: np.ndarray) -> np.ndarray:
    """Run one (NUM_FRAMES, NUM_MEL) feature matrix; return float class probabilities.

    For an int8 model this quantizes the input and dequantizes the output exactly the
    way the firmware does:  q = round(x / scale) + zero_point, clamped to [-128, 127].
    """
    inp = interp.get_input_details()[0]
    out = interp.get_output_details()[0]
    x = features.reshape(inp["shape"]).astype(np.float32)
    if inp["dtype"] == np.int8:
        scale, zp = inp["quantization"]
        x = np.clip(np.round(x / scale) + zp, -128, 127).astype(np.int8)
    interp.set_tensor(inp["index"], x)
    interp.invoke()
    y = interp.get_tensor(out["index"]).reshape(-1)
    if out["dtype"] == np.int8:
        scale, zp = out["quantization"]
        y = (y.astype(np.float32) - zp) * scale
    return y.astype(np.float32)
