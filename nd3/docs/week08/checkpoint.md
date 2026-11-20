# Week 08 Checkpoint Quiz: IMU Perception & Robotic Control

![track](https://img.shields.io/badge/track-ND03-6d28d9?style=flat-square)
![kind](https://img.shields.io/badge/kind-checkpoint-2e8b57?style=flat-square)

Test your understanding of IMU physics, sensor telemetry, temporal windowing, and robotic safety interlocks.

---

### Question 1: Stationary Accelerometer Physics
When a 6-axis IMU board rests flat on a stationary table with its +Z axis pointing up toward the ceiling, what acceleration values should the sensor ideally report?
- A) $a_x = 0, a_y = 0, a_z = 0\text{ m/s}^2$
- B) $a_x = 0, a_y = 0, a_z \approx +9.81\text{ m/s}^2$ (measuring the normal force opposing gravity)
- C) $a_x = 9.81, a_y = 9.81, a_z = 9.81\text{ m/s}^2$
- D) $a_x = 0, a_y = -9.81, a_z = 0\text{ m/s}^2$

*(Answer: B)*

---

### Question 2: Lost Telemetry Detection
Why does `robotos-kws collect-imu` calculate timestamp delta ($dt = t_k - t_{k-1}$) and count gaps greater than $1.5 \times 20\text{ ms}$?
- A) To increase the baud rate of the serial port.
- B) To detect dropped USB packets or MCU buffer overruns; any motion window missing multiple samples would distort the temporal pattern seen by the 1D-CNN.
- C) To measure the battery voltage.
- D) To calibrate the gyroscope zero-rate offset.

*(Answer: B)*

---

### Question 3: Fixed Physical Scaling vs Per-Window Z-Score Normalization
In `imu_common.normalise()`, acceleration is divided by $9.80665\text{ m/s}^2$ and gyro by $4.0\text{ rad/s}$. Why do we use **fixed physical scaling** rather than standard per-window z-score normalization ($\frac{x - \mu}{\sigma}$)?
- A) Fixed scaling is faster to compute on microcontrollers.
- B) Z-score normalization removes the absolute magnitude ("how hard") of the movement, making a tiny subtle vibration look mathematically identical to a violent collision shake.
- C) Z-score normalization causes division by zero when the board is held still.
- D) Both B and C are correct.

*(Answer: D)*

---

### Question 4: Person-Disjoint Validation
Why must training and testing datasets for robotic gesture recognition be partitioned by **person** or **robot platform** rather than randomly shuffling all recorded CSV takes?
- A) Random shuffling is not supported by NumPy.
- B) Two takes recorded by the same individual in the same session share identical movement speed, hand tilt, and biomechanics; random shuffling inflates test accuracy while the model fails completely on an unseen user.
- C) Person-disjoint splitting reduces model training time.
- D) To comply with GDPR privacy laws.

*(Answer: B)*
