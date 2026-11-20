"""Host side of the hardware-interface-workshop board protocol (Python port).

This is the same wire format the workshop's React demos and Web Serial labs use
(``demos/src/lib/wire/*.ts`` in https://github.com/drsanti/hardware-interface-workshop),
so the boards keep running the workshop's *prebuilt* firmware - nothing to flash.

One frame on the USB serial port:

    0x00 | COBS( msg_type u8 | seq u16 LE | len u16 LE | payload | crc16 LE ) | 0x00

* COBS removes every 0x00 from the body so 0x00 can mark frame boundaries.
* crc16 = CRC-16/XMODEM (poly 0x1021, init 0) over ``msg_type..payload``.
* ``payload`` is a protobuf message; which one depends on ``msg_type``.

Only the handful of messages Week 08 needs are implemented, with a ~60-line
protobuf reader/writer so there is no code generator and no extra dependency.
"""
from __future__ import annotations

import struct
import time
from collections import deque
from dataclasses import dataclass, field

# --------------------------------------------------------------------------- ids
MSG_IMU = 0x20          # board -> host  robotos.sensor.v1.Imu, ~50 Hz (ws28p)
MSG_AUDIO_LEVEL = 0x23  # board -> host  AudioLevel, ~10 Hz while the mic is on
MSG_MIC_PCM = 0x24      # board -> host  MicPcm chunks while MicCmd.stream is on (USB only)
MSG_CMD_ACK = 0x27      # board -> host  CmdAck, one per command
MSG_BOARD_INFO = 0x28   # board -> host  BoardInfo, at boot and about every 10 s
MSG_MIC_CMD = 0x86      # host -> board  MicCmd

CAP_LED, CAP_MIC, CAP_IMU, CAP_RTC, CAP_BATT, CAP_BTN = 0x01, 0x02, 0x04, 0x08, 0x10, 0x20
CAP_NAMES = {CAP_LED: "LED", CAP_MIC: "MIC", CAP_IMU: "IMU", CAP_RTC: "RTC", CAP_BATT: "BATT", CAP_BTN: "BTN"}
BOARD_CAPS = {"es3c28p": 0x33, "ws28p": 0x3C}   # firmware-prebuilt/README.md

MIC_RATE_HZ = 16_000    # board mic sample rate (MIC_FS_HZ in the demos)
IMU_RATE_HZ = 50        # board IMU publish rate
MAX_WIRE = 1038         # longest legal frame on the wire, both delimiters included
ACK_TIMEOUT_S = 2.5     # same as the demos' useAckedWrite
SETTLE_S = 2.5          # opening USB can reset the board; wait before trusting data


def caps_str(caps: int) -> str:
    names = [n for bit, n in CAP_NAMES.items() if caps & bit]
    return f"0x{caps:02x} ({'|'.join(names) or 'none'})"


# ------------------------------------------------------------------ CRC + COBS
def crc16_xmodem(data: bytes) -> int:
    crc = 0
    for b in data:
        crc ^= b << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return crc


def cobs_encode(src: bytes) -> bytes:
    out = bytearray([0])
    code_at, code = 0, 1
    for b in src:
        if b == 0:
            out[code_at] = code
            code_at, code = len(out), 1
            out.append(0)
        else:
            out.append(b)
            code += 1
            if code == 0xFF:
                out[code_at] = code
                code_at, code = len(out), 1
                out.append(0)
    out[code_at] = code
    return bytes(out)


def cobs_decode(src: bytes) -> bytes | None:
    out = bytearray()
    i = 0
    while i < len(src):
        code = src[i]
        i += 1
        if code == 0 or i + code - 1 > len(src):
            return None
        out += src[i:i + code - 1]
        i += code - 1
        if code < 0xFF and i < len(src):
            out.append(0)
    return bytes(out)


@dataclass
class Frame:
    msg_type: int
    seq: int
    payload: bytes


def frame_encode(msg_type: int, seq: int, payload: bytes = b"") -> bytes:
    body = struct.pack("<BHH", msg_type, seq & 0xFFFF, len(payload)) + bytes(payload)
    body += struct.pack("<H", crc16_xmodem(body))
    return b"\x00" + cobs_encode(body) + b"\x00"


class FrameDecoder:
    """Streaming splitter: feed raw serial bytes, get complete valid frames.

    Bytes outside 0x00 ... 0x00 (boot log text, half frames) are skipped and counted.
    """

    def __init__(self):
        self.buf = bytearray()
        self.in_frame = False
        self.frames_ok = 0
        self.bad_frames = 0      # COBS / length / CRC failures
        self.skipped_bytes = 0   # bytes before the first delimiter, or in oversize junk

    def feed(self, data: bytes) -> list[Frame]:
        frames = []
        for b in data:
            if b == 0:
                if self.in_frame and self.buf:
                    f = self._decode(bytes(self.buf))
                    if f:
                        frames.append(f)
                        self.frames_ok += 1
                    else:
                        self.bad_frames += 1
                self.in_frame = True
                self.buf.clear()
            elif not self.in_frame:
                self.skipped_bytes += 1
            elif len(self.buf) >= MAX_WIRE:
                self.skipped_bytes += len(self.buf) + 1
                self.in_frame = False
                self.buf.clear()
            else:
                self.buf.append(b)
        return frames

    @staticmethod
    def _decode(raw: bytes) -> Frame | None:
        body = cobs_decode(raw)
        if body is None or len(body) < 7:
            return None
        msg_type, seq, plen = struct.unpack_from("<BHH", body)
        if len(body) != 7 + plen:
            return None
        (want,) = struct.unpack_from("<H", body, 5 + plen)
        if crc16_xmodem(body[:5 + plen]) != want:
            return None
        return Frame(msg_type, seq, body[5:5 + plen])


# ------------------------------------------------------------ tiny protobuf
def _varint(v: int) -> bytes:
    v &= (1 << 64) - 1          # negative int32/64 -> 10-byte two's complement, like protobuf
    out = bytearray()
    while True:
        b = v & 0x7F
        v >>= 7
        out.append(b | (0x80 if v else 0))
        if not v:
            return bytes(out)


def _read_varint(buf: bytes, i: int) -> tuple[int, int]:
    shift = v = 0
    while True:
        if i >= len(buf) or shift > 63:
            raise ValueError("truncated varint")
        b = buf[i]
        i += 1
        v |= (b & 0x7F) << shift
        shift += 7
        if not b & 0x80:
            return v, i


def zigzag_encode(n: int) -> int:
    return (n << 1) ^ (n >> 63)


def zigzag_decode(n: int) -> int:
    return (n >> 1) ^ -(n & 1)


def pb_fields(buf: bytes) -> dict[int, list]:
    """Parse a protobuf message into {field_number: [raw values]}.

    varint -> int, fixed64 -> 8 bytes, length-delimited -> bytes, fixed32 -> 4 bytes.
    Unknown fields are kept (and ignored by the decoders), so newer firmware still works.
    """
    out: dict[int, list] = {}
    i = 0
    while i < len(buf):
        key, i = _read_varint(buf, i)
        num, wt = key >> 3, key & 7
        if wt == 0:
            val, i = _read_varint(buf, i)
        elif wt == 1:
            val, i = buf[i:i + 8], i + 8
        elif wt == 2:
            n, i = _read_varint(buf, i)
            val, i = buf[i:i + n], i + n
        elif wt == 5:
            val, i = buf[i:i + 4], i + 4
        else:
            raise ValueError(f"unsupported wire type {wt}")
        if i > len(buf):
            raise ValueError("truncated field")
        out.setdefault(num, []).append(val)
    return out


def _last(f, num, default=0):
    return f[num][-1] if num in f else default


def _str(f, num) -> str:
    return bytes(_last(f, num, b"")).decode("utf-8", "replace")


def _double(f, num) -> float:
    return struct.unpack("<d", _last(f, num, b"\x00" * 8))[0]


def _key(num: int, wt: int) -> bytes:
    return _varint((num << 3) | wt)


def _pb_varint(num: int, v: int) -> bytes:
    return _key(num, 0) + _varint(int(v))


def _pb_bytes(num: int, b: bytes) -> bytes:
    return _key(num, 2) + _varint(len(b)) + b


def _pb_double(num: int, v: float) -> bytes:
    return _key(num, 1) + struct.pack("<d", v)


# ----------------------------------------------------------- messages (host)
@dataclass
class BoardInfo:
    uuid: str = ""
    mac: str = ""
    ip: str = ""
    uptime_ns: int = 0
    fw_version: str = ""
    proto_version: int = 0
    hw_model: str = ""
    caps: int = 0

    def has(self, cap: int) -> bool:
        return bool(self.caps & cap)

    def describe(self) -> str:
        model = self.hw_model or "?"
        return f"{model} fw={self.fw_version or '?'} caps={caps_str(self.caps)} uuid={self.uuid or '?'}"


def decode_board_info(p: bytes) -> BoardInfo:
    f = pb_fields(p)
    return BoardInfo(uuid=_str(f, 1), mac=_str(f, 2), ip=_str(f, 3), uptime_ns=_last(f, 4),
                     fw_version=_str(f, 7), proto_version=_last(f, 8), hw_model=_str(f, 9),
                     caps=_last(f, 10))


@dataclass
class MicPcm:
    seq: int
    samples: "list[int]"


def decode_mic_pcm(p: bytes) -> MicPcm:
    f = pb_fields(p)
    samples: list[int] = []
    for v in f.get(2, []):
        if isinstance(v, int):              # unpacked element
            samples.append(zigzag_decode(v))
        else:                               # packed (proto3 default)
            i = 0
            while i < len(v):
                z, i = _read_varint(v, i)
                samples.append(zigzag_decode(z))
    samples = [max(-32768, min(32767, s)) for s in samples]
    return MicPcm(seq=_last(f, 1), samples=samples)


@dataclass
class AudioLevel:
    rms: int
    peak: int
    frames: int
    clipped: bool


def decode_audio_level(p: bytes) -> AudioLevel:
    f = pb_fields(p)
    return AudioLevel(_last(f, 1), _last(f, 2), _last(f, 3), bool(_last(f, 4)))


@dataclass
class ImuSample:
    timestamp_ns: int
    accel: tuple   # m/s^2 (about 9.8 on the axis that points up when still)
    gyro: tuple    # rad/s


def decode_imu(p: bytes) -> ImuSample:
    f = pb_fields(p)

    def vec(num):
        if num not in f:
            return (0.0, 0.0, 0.0)
        v = pb_fields(bytes(f[num][-1]))
        return (_double(v, 1), _double(v, 2), _double(v, 3))

    return ImuSample(_last(f, 1), vec(3), vec(4))


@dataclass
class CmdAck:
    msg_type: int
    req_seq: int
    rc: int
    detail: str = ""


def decode_cmd_ack(p: bytes) -> CmdAck:
    f = pb_fields(p)
    rc = _last(f, 3)
    if rc >= 1 << 63:
        rc -= 1 << 64
    return CmdAck(_last(f, 1), _last(f, 2), rc, _str(f, 4))


def encode_mic_cmd(enable=None, gain_pct=None, stream=None, stage_mask=None, mute=None) -> bytes:
    """MicCmd: every field optional - leave a field as None to keep the board's setting."""
    out = b""
    if enable is not None:
        out += _pb_varint(1, bool(enable))
    if gain_pct is not None:
        out += _pb_varint(2, max(0, min(100, round(gain_pct))))
    if stream is not None:
        out += _pb_varint(3, bool(stream))
    if stage_mask is not None:
        out += _pb_varint(4, stage_mask)
    if mute is not None:
        out += _pb_varint(5, bool(mute))
    return out


# --------------------------------------- encoders the board side uses (for tests)
def encode_board_info(info: BoardInfo) -> bytes:
    out = b""
    for num, s in ((1, info.uuid), (2, info.mac), (3, info.ip)):
        if s:
            out += _pb_bytes(num, s.encode())
    if info.uptime_ns:
        out += _pb_varint(4, info.uptime_ns)
    if info.fw_version:
        out += _pb_bytes(7, info.fw_version.encode())
    if info.proto_version:
        out += _pb_varint(8, info.proto_version)
    if info.hw_model:
        out += _pb_bytes(9, info.hw_model.encode())
    if info.caps:
        out += _pb_varint(10, info.caps)
    return out


def encode_mic_pcm(seq: int, samples) -> bytes:
    packed = b"".join(_varint(zigzag_encode(int(s))) for s in samples)
    return (_pb_varint(1, seq) if seq else b"") + (_pb_bytes(2, packed) if packed else b"")


def encode_imu(timestamp_ns: int, accel, gyro) -> bytes:
    def vec(v):
        return b"".join(_pb_double(i + 1, float(x)) for i, x in enumerate(v) if x != 0.0)
    return _pb_varint(1, timestamp_ns) + _pb_bytes(3, vec(accel)) + _pb_bytes(4, vec(gyro))


def encode_cmd_ack(msg_type: int, req_seq: int, rc: int = 0) -> bytes:
    out = _pb_varint(1, msg_type) + _pb_varint(2, req_seq)
    return out + (_pb_varint(3, rc) if rc else b"")


# ----------------------------------------------------------------- session
class WireError(RuntimeError):
    pass


class WrongBoard(WireError):
    pass


class BoardSession:
    """A serial connection to a board running the workshop prebuilt firmware.

    Single-threaded: call :meth:`poll` (or helpers that call it) often enough that
    the operating system's receive buffer does not overflow.
    """

    def __init__(self, ser, settle_s: float = SETTLE_S, log=print):
        self.ser = ser
        self.dec = FrameDecoder()
        self.pending: deque[Frame] = deque()
        self.tx_seq = 0
        self.info: BoardInfo | None = None
        self.log = log
        if settle_s > 0:
            self._settle(settle_s)

    @classmethod
    def open(cls, port: str, settle_s: float = SETTLE_S, log=print) -> "BoardSession":
        import serial  # pyserial

        try:
            ser = serial.Serial(port, 921600, timeout=0.05)   # baud is ignored by USB Serial/JTAG
        except serial.SerialException as e:
            raise WireError(f"cannot open {port}: {e}\n  Check the port name, then close the browser tab that uses Web Serial "
                            "(workshop demos), any serial monitor, and rbdev, then retry.") from e
        return cls(ser, settle_s, log)

    def close(self):
        try:
            self.ser.close()
        except Exception:
            pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    # -- low level
    def _read_frames(self, timeout: float) -> list[Frame]:
        self.ser.timeout = max(0.0, timeout)
        data = self.ser.read(max(1, getattr(self.ser, "in_waiting", 0) or 1))
        n = getattr(self.ser, "in_waiting", 0) or 0
        if n:
            data += self.ser.read(n)
        frames = self.dec.feed(data) if data else []
        for f in frames:
            if f.msg_type == MSG_BOARD_INFO:
                try:
                    self.info = decode_board_info(f.payload)
                except ValueError:
                    pass
        return frames

    def _settle(self, seconds: float):
        """Drain whatever arrives while the board (maybe) reboots; keep BoardInfo."""
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            self._read_frames(0.05)
        self.pending.clear()

    def poll(self, timeout: float = 0.05) -> list[Frame]:
        """Return frames received so far (waits up to ``timeout`` if none are queued)."""
        if not self.pending:
            self.pending.extend(self._read_frames(timeout))
        else:
            self.pending.extend(self._read_frames(0))
        out = list(self.pending)
        self.pending.clear()
        return out

    def drain(self):
        """Throw away everything already buffered (e.g. stale samples)."""
        try:
            self.ser.reset_input_buffer()
        except Exception:
            pass
        self.pending.clear()
        self.dec = FrameDecoder()

    def write_frame(self, msg_type: int, payload: bytes) -> int:
        seq = self.tx_seq & 0xFFFF
        self.tx_seq += 1
        self.ser.write(frame_encode(msg_type, seq, payload))
        self.ser.flush()
        return seq

    def write_acked(self, msg_type: int, payload: bytes, timeout: float = ACK_TIMEOUT_S) -> int:
        """Send a command and wait for its CmdAck. Returns rc (0 = ok)."""
        seq = self.write_frame(msg_type, payload)
        end = time.monotonic() + timeout
        keep = []
        try:
            while time.monotonic() < end:
                for f in self._read_frames(0.05):
                    if f.msg_type == MSG_CMD_ACK:
                        ack = decode_cmd_ack(f.payload)
                        if ack.msg_type == msg_type and (ack.req_seq & 0xFFFF) == seq:
                            return ack.rc
                    keep.append(f)
        finally:
            self.pending.extend(keep)
        raise WireError("No reply from board - is the workshop prebuilt firmware on the board?")

    # -- helpers
    def wait_board_info(self, timeout: float = 12.0, need_cap: int = 0, need_name: str = "") -> BoardInfo:
        """Wait for BoardInfo (sent at boot and about every 10 s) and check capabilities.

        Raises :class:`WrongBoard` if the board lacks ``need_cap``.
        Streaming sensor frames that prove the capability are accepted while waiting.
        """
        end = time.monotonic() + timeout
        seen_imu = 0
        told = False
        while self.info is None and time.monotonic() < end:
            for f in self.poll(0.1):
                if f.msg_type == MSG_IMU:
                    seen_imu += 1
            if need_cap == CAP_MIC and seen_imu >= 10:
                raise WrongBoard(_wrong_board_text(None, need_cap, need_name, "it streams IMU frames (ws28p)"))
            if need_cap == CAP_IMU and seen_imu >= 25:
                self.log("  (IMU frames are arriving; BoardInfo not seen yet - continuing)")
                return BoardInfo(caps=CAP_IMU)
            if not told and time.monotonic() > end - timeout + 1.0:
                self.log(f"  waiting up to {timeout:.0f} s for BoardInfo (the board sends it about every 10 s)...")
                told = True
        if self.info is None:
            raise WireError("No BoardInfo frame received. Check: right port? workshop prebuilt firmware "
                            "flashed (rbdev flash-bin)? port not held by a browser tab / serial monitor?")
        if need_cap and not self.info.has(need_cap):
            raise WrongBoard(_wrong_board_text(self.info, need_cap, need_name, ""))
        return self.info


def _wrong_board_text(info, need_cap, need_name, why) -> str:
    want = {CAP_MIC: "es3c28p (RGB LED + mic)", CAP_IMU: "ws28p (IMU + RTC)"}.get(need_cap, f"cap 0x{need_cap:02x}")
    got = info.describe() if info else why
    alt = {CAP_MIC: "Use the es3c28p board, or record with your computer mic: python collect_pc_mic.py",
           CAP_IMU: "Use the ws28p board (firmware-prebuilt/ws28p)."}.get(need_cap, "")
    return (f"Wrong board for {need_name or 'this tool'}: needs {CAP_NAMES.get(need_cap, '?')} "
            f"-> {want}.\n  Attached board: {got}\n  {alt}")


# ------------------------------------------------------- stream bookkeeping
@dataclass
class PcmAssembler:
    """Join MicPcm chunks, detect lost chunks from MicPcm.seq and fill them with silence.

    The prebuilt firmware counts MicPcm.seq with an 8-bit counter (0..255, then wraps),
    one step per chunk of up to 240 samples, so gaps are computed modulo 256.
    """
    seq_mod: int = 256
    last_seq: int | None = None
    last_len: int = 240
    chunks: int = 0
    lost_chunks: int = 0
    samples: list = field(default_factory=list)

    def push(self, m: MicPcm) -> list[int]:
        """Add one chunk; returns the samples to append (silence first if chunks were lost)."""
        out: list[int] = []
        if self.last_seq is not None:
            gap = (m.seq - self.last_seq - 1) % self.seq_mod
            if 0 < gap < self.seq_mod // 2:
                self.lost_chunks += gap
                out = [0] * (gap * self.last_len)
        self.last_seq = m.seq
        if m.samples:
            self.last_len = len(m.samples)
        self.chunks += 1
        out += m.samples
        return out


class MicStream:
    """Turn the es3c28p microphone stream on/off and read PCM from it.

    Uses the same two acked commands as the workshop's ex28 recorder:
    ``MicCmd{enable, gain_pct}`` then ``MicCmd{stream: true, enable: true}``.
    """

    def __init__(self, sess: BoardSession, rate_hz: int = MIC_RATE_HZ):
        self.sess = sess
        self.rate = rate_hz
        self.asm = PcmAssembler()
        self.level: AudioLevel | None = None
        self.buf: list[int] = []

    def _cmd(self, **kw):
        rc = self.sess.write_acked(MSG_MIC_CMD, encode_mic_cmd(**kw))
        if rc != 0:
            raise WireError(f"board rejected MicCmd {kw} (rc={rc})")

    def enable(self, gain_pct: int | None = 60):
        self._cmd(enable=True, gain_pct=gain_pct)

    def start(self, warmup_s: float = 0.1):
        """Start streaming; the first ``warmup_s`` (filter settling) is thrown away."""
        self._cmd(stream=True, enable=True)
        self.asm = PcmAssembler()
        self.buf = []
        if warmup_s > 0:
            self.read(int(warmup_s * self.rate), timeout=2.0)
        self.asm.lost_chunks = 0

    def stop(self, disable: bool = False):
        try:
            self._cmd(stream=False, **({"enable": False} if disable else {}))
        except WireError:
            pass

    def pump(self, timeout: float = 0.05) -> int:
        """Read whatever has arrived; returns the number of new samples."""
        n0 = len(self.buf)
        for f in self.sess.poll(timeout):
            if f.msg_type == MSG_MIC_PCM:
                self.buf += self.asm.push(decode_mic_pcm(f.payload))
            elif f.msg_type == MSG_AUDIO_LEVEL:
                self.level = decode_audio_level(f.payload)
        return len(self.buf) - n0

    def read(self, n: int, timeout: float = 5.0):
        """Block until ``n`` samples are available; returns (int16 numpy array, chunks lost)."""
        import numpy as np

        lost0 = self.asm.lost_chunks
        end = time.monotonic() + timeout
        last_data = time.monotonic()
        while len(self.buf) < n:
            if self.pump(0.05):
                last_data = time.monotonic()
            now = time.monotonic()
            if now > end or now - last_data > 1.0:
                raise WireError(f"mic stream stalled: got {len(self.buf)} of {n} samples "
                                "(stream not started, USB busy, or a browser tab holds the port?)")
        out, self.buf = self.buf[:n], self.buf[n:]
        return np.asarray(out, dtype=np.int16), self.asm.lost_chunks - lost0
