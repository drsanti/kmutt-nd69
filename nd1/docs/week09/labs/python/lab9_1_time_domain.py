"""Lab 9.1 — Time domain: what does the IMU really send?

Records a few seconds of 6-axis IMU data (live from a ws28p, or --replay), then plots the
accelerometer, the magnitude |a| and the gyroscope, and prints basic signal statistics.

    python lab9_1_time_domain.py --replay            # no board
    python lab9_1_time_domain.py --seconds 10        # live ws28p, auto-detected port
"""
import numpy as np

import robotos_edge as rk
from lab_common import imu_source, intro, parse_args

G = 9.80665


def record(args):
    """Collect samples into arrays t, acc (N x 3), gyr (N x 3)."""
    want = int(args.seconds * 50)
    rows = []
    if args.replay is not None:
        src = imu_source(args)
        src.realtime = False                       # replay: no need to wait in real time
        for s in src:
            rows.append((s.t, *s.accel, *s.gyro))
            if len(rows) >= want:
                break
        lost = 0
    else:
        with rk.connect(args.port, need_cap=rk.wire.CAP_IMU) as session:
            stream = imu_source(args, session)
            print(f"Recording {args.seconds:.0f} s — move the board around, then hold it still.")
            for s in stream:
                rows.append((s.t, *s.accel, *s.gyro))
                if len(rows) >= want:
                    break
            lost = stream.lost
    a = np.array(rows)
    return a[:, 0], a[:, 1:4], a[:, 4:7], lost


def main():
    args = parse_args(__doc__, seconds=8)
    intro(__doc__, args,
          live='Move the board around for a few seconds, then hold it still until recording ends (8 s; change with --seconds). A plot window opens at the end.',
          replay='Nothing to do: the recorded idle, shake, circle and lift motions are used. A plot window opens at the end.',
          look='|a| stays near 9.81 m/s^2 when the board is still, whatever its tilt; during a lift it dips below, then rises above. The script prints the sample rate, lost samples and the axis along gravity.')
    t, acc, gyr, lost = record(args)

    # Step 1: compute |a| for every sample (N values) from the 3 accel axes
    a_mag = np.sqrt((acc ** 2).sum(axis=1))

    # Step 2: estimate the sample rate in Hz from the timestamps t
    rate_hz = 1.0 / np.median(np.diff(t))

    # Step 3: which axis (0=x, 1=y, 2=z) points along gravity? Use the mean of each accel axis
    up_axis = int(np.argmax(np.abs(acc.mean(axis=0))))

    still = slice(0, min(len(t), 50))                                     # first second
    print(f"samples: {len(t)}  duration: {t[-1] - t[0]:.2f} s  rate: {rate_hz:.1f} Hz  lost: {lost}")
    print(f"|a| mean {a_mag.mean():.2f} m/s^2 (gravity = {G:.2f})   min {a_mag.min():.2f}   max {a_mag.max():.2f}")
    print(f"axis along gravity: {'xyz'[up_axis]}   accel noise (std, first 1 s): "
          + "  ".join(f"{'xyz'[i]} {acc[still, i].std():.3f}" for i in range(3)))

    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(3, 1, sharex=True, figsize=(10, 7))
    for i, c in enumerate("rgb"):
        ax[0].plot(t, acc[:, i], c, label="xyz"[i])
    ax[0].set_ylabel("accel (m/s²)")
    ax[0].legend(loc="upper right")
    ax[1].plot(t, a_mag, "k")
    ax[1].axhline(G, color="gray", ls="--", label="1 g")
    ax[1].set_ylabel("|a| (m/s²)")
    ax[1].legend(loc="upper right")
    for i, c in enumerate("rgb"):
        ax[2].plot(t, gyr[:, i], c, label="xyz"[i])
    ax[2].set_ylabel("gyro (rad/s)")
    ax[2].set_xlabel("time (s)")
    fig.suptitle(f"Lab 9.1 — {len(t)} samples at {rate_hz:.1f} Hz, {lost} lost")
    fig.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
