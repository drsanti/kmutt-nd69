# Week 08 Pre-Flight Readiness Quiz: Computer & Developer Skills

![course](https://img.shields.io/badge/course-KMUTT%20ND69-1a2f5a?style=flat-square)
![track](https://img.shields.io/badge/track-ND03-6d28d9?style=flat-square)
![week](https://img.shields.io/badge/week-08-334155?style=flat-square)
![lang](https://img.shields.io/badge/lang-EN-2563eb?style=flat-square)
![kind](https://img.shields.io/badge/kind-quiz-2e8b57?style=flat-square)

[Week 08 index](README.md) · [Labs Guide](labs/README.md)

This 10-question pre-flight self-check verifies your practical developer literacy — covering virtual environments, command-line syntax, file navigation, hardware serial ports, and debugging — before you begin the hands-on Edge AI labs.

Try answering each question on your own first, then expand the **Answer & Explanation** section to check your understanding.

---

### Question 1: Python Version & TensorFlow Binary Compatibility
**Q:** Why does this lab explicitly require **Python 3.10 to 3.13** (with **Python 3.11 strongly recommended**), and what error occurs if you try running `pip install -r requirements.txt` under Python 3.14?

<details>
<summary>Answer & Explanation</summary>

**Answer:**  
TensorFlow and its compiled C-extension kernels publish pre-built binary wheels only for Python 3.10, 3.11, and 3.12 (and early 3.13 builds). There are currently **no pre-compiled wheels for Python 3.14** on Windows or macOS.

If you run `pip install -r requirements.txt` under Python 3.14, `pip` will fail with:
```text
ERROR: Could not find a version that satisfies the requirement tensorflow>=2.16
ERROR: No matching distribution found for tensorflow>=2.16
```
Always verify with `python --version` inside your active virtual environment.
</details>

---

### Question 2: Virtual Environment State
**Q:** How do you verify whether a virtual environment is currently active in your terminal, and what happens if you run `pip install` without an active virtual environment?

<details>
<summary>Answer & Explanation</summary>

**Answer:**  
Your terminal prompt must show the prefix **`(.venv)`** (or the name of your environment).

If you run `pip install` without an active virtual environment:
1. Packages install into your **global system Python**, risking dependency conflicts across different classes and projects.
2. If your global Python is Python 3.14, installation will fail immediately.
3. System permission errors can occur (e.g. `externally-managed-environment` on macOS or Linux).
</details>

---

### Question 3: Recovering from an Incompatible Virtual Environment
**Q:** If you accidentally created `.venv` using the wrong Python version (such as Python 3.14), what is the correct 4-step sequence to clean it up and recreate it with Python 3.11?

<details>
<summary>Answer & Explanation</summary>

**Answer:**  
You must deactivate and delete the old `.venv` directory first, because simply re-running the command does not replace existing pip wrappers:

* **macOS / Linux:**
  ```bash
  deactivate
  rm -rf .venv
  python3.11 -m venv .venv
  source .venv/bin/activate
  ```
* **Windows (PowerShell):**
  ```powershell
  deactivate
  Remove-Item -Recurse -Force .venv
  py -3.11 -m venv .venv
  .\.venv\Scripts\Activate.ps1
  ```
* **Verification:** Always run `python --version` immediately after activating; it must output `Python 3.11.x`.
</details>

---

### Question 4: Windows PowerShell Script Execution Policy
**Q:** On Windows PowerShell, if activating your virtual environment fails with:  
`PSSecurityException: File ... Activate.ps1 cannot be loaded because running scripts is disabled on this system`  
What command temporarily resolves this for your current terminal window?

<details>
<summary>Answer & Explanation</summary>

**Answer:**  
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```
This grants permission **only to the current PowerShell process**, leaving your system-wide Windows security settings intact while allowing `.venv\Scripts\Activate.ps1` to execute.
</details>

---

### Question 5: File System Paths (`.` vs `..`)
**Q:** If your terminal is located in `nd3/docs/week08/labs/robotics` and you run:  
```bash
python robot_fsm.py --model ../../../nd1/docs/week08/labs/python/artifacts/model_int8.tflite
```
What do the three sets of `../` represent, and how does path navigation work here?

<details>
<summary>Answer & Explanation</summary>

**Answer:**  
Each `../` moves one directory up:
1. `../` moves up to `nd3/docs/week08/labs`.
2. `../../` moves up to `nd3/docs/week08`.
3. `../../../` moves up to `nd3/docs`.

From there, it traverses down into `nd1/docs/week08/labs/python/artifacts/model_int8.tflite`. Understanding relative paths allows you to share trained artifacts across tracks without making duplicate copies.
</details>

---

### Question 6: Anatomy of a CLI Command
**Q:** In the following command:  
```bash
robotos-kws train-imu --data imu_dataset --out imu_artifacts --epochs 60
```
Identify:
1. The **executable program**
2. The **subcommand**
3. The **option flags and their arguments**

<details>
<summary>Answer & Explanation</summary>

**Answer:**  
1. **Executable:** `robotos-kws` (the binary tool registered by the wheel in your virtual environment).
2. **Subcommand:** `train-imu` (the specific task requested from the CLI to train a 1D-CNN on 6-DOF IMU gestures).
3. **Options & Arguments:**
   * `--data` with argument `imu_dataset` (path to input gesture CSV takes).
   * `--out` with argument `imu_artifacts` (destination directory for the trained `.tflite` model and metadata).
   * `--epochs` with argument `60` (training iterations).
</details>

---

### Question 7: Identifying Hardware Serial Ports (Windows vs. macOS)
**Q:** When connecting your ws28p ESP32-S3 board via USB-C, how does the serial port identifier appear on Windows versus macOS, and which prefix must you use on macOS?

<details>
<summary>Answer & Explanation</summary>

**Answer:**  
* **Windows:** Serial ports appear as `COM` numbers, e.g. `COM3`, `COM7`, `COM17`.
* **macOS:** Serial devices appear under `/dev/cu.usbmodem*` (e.g. `/dev/cu.usbmodem1101` or `/dev/cu.usbserial-*`).
* **Critical macOS distinction:** Always connect using the **`/dev/cu.*`** (Call-Up device) device path, **never** `/dev/tty.*`. The `tty.*` device waits for hardware carrier detect (DCD) asserting and can cause your script to hang indefinitely.
* You can find your port on macOS by running: `ls /dev/cu.usb*`.
* **Automated Flashing:** The `robotos flash-firmware` command automatically detects your ESP32-S3 serial port across both Windows and macOS by inspecting USB VID:PID (`0x303A:0x1001`), so you typically do not even need to type the port manually!
</details>

---

### Question 8: Detecting Dropped Telemetry Frames
**Q:** During live 50 Hz IMU streaming (`dt = 20 ms`), why does the script count delta gaps where $dt > 1.5 \times 20\text{ ms}$ ($> 30\text{ ms}$), and what does a high lost frame count indicate?

<details>
<summary>Answer & Explanation</summary>

**Answer:**  
* The ws28p board transmits inertial readings at an exact 50 Hz cadence ($20\text{ ms}$).
* If $dt > 30\text{ ms}$, one or more frames were dropped in transit (due to USB packet loss, host serial buffer overrun, or CPU thread starvation).
* A high lost frame count means the temporal sampling grid is distorted, which can cause the 1D-CNN model to misclassify dynamic gestures.
</details>

---

### Question 9: Reading Python Error Tracebacks
**Q:** When running a lab script, your terminal prints a 25-line red traceback. Which line should you read first, and what is the difference between `ModuleNotFoundError` and `FileNotFoundError`?

<details>
<summary>Answer & Explanation</summary>

**Answer:**  
* **Always read the very last line first.** Python tracebacks are ordered chronologically; the top shows where execution started, but the **bottom line states the actual exception**.
* **`ModuleNotFoundError: No module named '...'`:** A required Python library is not installed in your active environment (run `pip install` inside your `.venv`).
* **`FileNotFoundError: [Errno 2] No such file or directory: '...'`:** The script attempted to open a file that does not exist at that path. Check your current directory (`pwd`), verify file names, and confirm you completed the preceding generation/training step.
</details>

---

### Question 10: Softmax Output Probabilities & Confidence Thresholding
**Q:** After classifying an audio or gesture sample, the model outputs:  
`probabilities = {"idle": 0.02, "shake": 0.94, "circle": 0.03, "lift": 0.01}`  
Why do all probabilities sum to $1.0$, and why must a production robotic controller apply a threshold (e.g. `threshold = 0.70`) rather than simply choosing whichever class has the highest probability?

<details>
<summary>Answer & Explanation</summary>

**Answer:**  
* The final **Softmax activation function** converts raw model output logits into a normalized probability distribution where $\sum_{i} P(C_i) = 1.0$ ($100\%$).
* **Why thresholding is essential in robotics:** In subtle ambient vibration or ambiguous motion, a model without a threshold would still pick whichever random class scored highest (even if it only scored $0.35$ or $0.40$). Setting a threshold like $0.70$ or $0.80$ ensures the robot triggers an action (like Emergency Stop or Autonomous Patrol) only when the neural network is statistically confident.
</details>

---

## What to Do Next

If you scored:
* **9–10 / 10:** You are fully equipped to move smoothly through the Week 08 hands-on Edge AI blocks!
* **< 9 / 10:** Review the questions you missed and consult with an instructor before starting your lab exercises.
