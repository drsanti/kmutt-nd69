#!/usr/bin/env python3
"""Self-test for wire.py - no board needed.  Run:  python test_wire.py

Checks the codec against the golden frames published with the board firmware
(serial-bridge test vectors; the first one is also in the workshop's
demos/src/lib/wire/selfcheck.ts), then round-trips every message Week 08 uses.
"""
import struct

import wire as w

GOLDEN = [  # (msg_type, seq, payload, wire hex)
    (0x20, 0, b"", "00022001010103b40800"),
    (0x20, 1, bytes.fromhex("deadbeef"), "00032001020407deadbeefd92200"),
    (0x21, 2, b"\xff" * 64, "0003210202404" + "3" + "ff" * 64 + "47f500"),
]
TOUCH_FRAME = "00032a05020c0f08d2091a07100118a0012078548900"   # msg 0x2a, seq 5, 12-byte payload
BIG = [  # (msg_type, seq, payload, wire length, last 4 bytes)  - worst-case sizes
    (0x22, 3, bytes(255), 265, "03010d00"),
    (0x24, 4, bytes(i & 0xFF for i in range(1024)), 1038, "ff373e00"),
]


def main() -> int:
    for mt, seq, p, hx in GOLDEN:
        assert w.frame_encode(mt, seq, p).hex() == hx, (mt, seq)
        (f,) = w.FrameDecoder().feed(bytes.fromhex(hx))
        assert (f.msg_type, f.seq, f.payload) == (mt, seq, p)
    (f,) = w.FrameDecoder().feed(bytes.fromhex(TOUCH_FRAME))
    assert (f.msg_type, f.seq, len(f.payload)) == (0x2A, 5, 12)
    for mt, seq, p, n, tail in BIG:
        enc = w.frame_encode(mt, seq, p)
        assert len(enc) == n and enc.hex().endswith(tail), (mt, len(enc))
        (f,) = w.FrameDecoder().feed(enc)
        assert f.payload == p
    print("golden frames: OK")

    # noise, a corrupted frame and a split stream
    good = w.frame_encode(w.MSG_MIC_PCM, 7, w.encode_mic_pcm(255, [0, 1, -1, 32767, -32768]))
    bad = bytearray(w.frame_encode(w.MSG_IMU, 8, b"\x01\x02")); bad[3] ^= 1
    stream = b"boot log\r\n" + bytes(bad) + good + b"junk" + good
    dec = w.FrameDecoder()
    frames = [f for i in range(0, len(stream), 5) for f in dec.feed(stream[i:i + 5])]
    assert len(frames) == 2 and dec.bad_frames >= 1
    m = w.decode_mic_pcm(frames[0].payload)
    assert m.seq == 255 and m.samples == [0, 1, -1, 32767, -32768]
    print("noise / CRC / split stream: OK")

    info = w.BoardInfo(uuid="ternion-esp32s3-abc", mac="aa:bb", hw_model="ws28p", fw_version="1.2", caps=0x3C)
    back = w.decode_board_info(w.encode_board_info(info))
    assert back.caps == 0x3C and back.has(w.CAP_IMU) and not back.has(w.CAP_MIC) and back.hw_model == "ws28p"
    s = w.decode_imu(w.encode_imu(123456789, (0.1, -0.2, 9.81), (0.0, 0.5, -1.0)))
    assert s.timestamp_ns == 123456789 and s.accel == (0.1, -0.2, 9.81) and s.gyro == (0.0, 0.5, -1.0)
    a = w.decode_cmd_ack(w.encode_cmd_ack(0x86, 70000, -3))
    assert (a.msg_type, a.req_seq & 0xFFFF, a.rc) == (0x86, 70000 & 0xFFFF, -3)
    assert w.encode_mic_cmd(enable=True, gain_pct=60) == bytes([0x08, 1, 0x10, 60])
    assert w.encode_mic_cmd(stream=True, enable=True) == bytes([0x08, 1, 0x18, 1])
    assert w.encode_mic_cmd(gain_pct=250) == bytes([0x10, 100])
    unpacked = b"".join(bytes([0x10]) + w._varint(w.zigzag_encode(v)) for v in (5, -5))  # non-packed form
    assert w.decode_mic_pcm(unpacked).samples == [5, -5]
    print("BoardInfo / Imu / CmdAck / MicCmd / MicPcm: OK")

    asm = w.PcmAssembler()
    out = asm.push(w.MicPcm(254, [1] * 240)) + asm.push(w.MicPcm(255, [2] * 240)) + asm.push(w.MicPcm(1, [3] * 240))
    assert asm.lost_chunks == 1 and len(out) == 4 * 240 and out[480:720] == [0] * 240   # 255 -> 1 wraps, 0 lost
    print("MicPcm.seq gap detection (8-bit wrap): OK")
    assert struct.pack("<H", w.crc16_xmodem(b"123456789")) == struct.pack("<H", 0x31C3)   # XMODEM check value
    print("ALL OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
