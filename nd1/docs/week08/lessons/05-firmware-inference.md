# Lesson 05 — Firmware: TFLite Micro on FreeRTOS

> Week 08 · ES3C28P / ESP32-S3 · 10:55–11:35 · instructor demo / advanced lab

[Lesson index](README.md) · [Previous: Lesson 04](04-testing-and-quantization.md) · [Next: Lesson 06](06-secure-edge-ai.md)

## Learning objectives

Put the int8 model into firmware as a C array, run it with TensorFlow Lite Micro from a static tensor arena, split the work into a FreeRTOS capture task and a lower-priority inference task connected by a queue, and measure the latency of every stage with `esp_timer`.

> [!IMPORTANT]
> Until now the board ran the **workshop prebuilt firmware** and the model ran on your computer. In this lesson the model moves **onto the ESP32-S3**. That means flashing a different program, `kws-inference`, built with ESP-IDF v6.1:
>
> - While `kws-inference` is on the board, the workshop protocol is gone: `collect.py`, `live_infer_board.py`, and the workshop browser demos will not connect.
> - When you are done, **reflash the prebuilt firmware**: `cd hardware-interface-workshop/firmware-prebuilt/es3c28p` → `python -m esptool -p <PORT> write-flash "@flash_args"`.
> - In class the instructor demonstrates this step; students with ESP-IDF set up can follow along. It is also the starting point for **Mini-Project 2** (5 December).

## Host inference vs device inference

| | Host inference (Lesson 04) | Device inference (this lesson) |
|---|---|---|
| Board firmware | Workshop prebuilt (unchanged) | `kws-inference` (ESP-IDF build) |
| Where features + model run | Your computer, Python | ESP32-S3, C / C++ with TFLite Micro |
| Audio leaves the board? | Yes, over USB | No — only the result is used |
| Iteration speed | Seconds (change a flag, rerun) | Minutes (export, build, flash) |
| What it proves | The model works with the real microphone | The model fits the memory, time, and power budget |

## Project layout

```text
labs/firmware/
├── components/es3c28p_audio/      shared: I2C bus + I2S RX + ES8311 via esp_codec_dev
└── kws-inference/
    ├── CMakeLists.txt             adds ../components with EXTRA_COMPONENT_DIRS
    ├── sdkconfig.defaults         esp32s3, USB Serial/JTAG console, 240 MHz, -O2, large app partition
    └── main/
        ├── idf_component.yml      espressif/esp-tflite-micro ~1.4.3, espressif/led_strip ~3.1.1
        ├── kws_main.cc            tasks, queue, TFLM interpreter, decision logic, LED
        ├── kws_config.h           gain, mic slot, hop, threshold, arena size, priorities
        ├── kws_features.c/.h      log-mel in C (twin of kws_common.py)
        ├── model_data.cc          the model as a C array (generated)
        └── kws_labels.h           label order (generated)
```

Dependencies come from the [ESP Component Registry](https://components.espressif.com/) the first time you build; you need internet access for that build.

## Step 1 — export your model

```bash
cd nd1/docs/week08/labs/python
python export_c_array.py --model artifacts/model_int8.tflite --out-dir ../firmware/kws-inference/main
```

```c
// model_data.cc (generated)
extern const unsigned char g_kws_model[];
extern const unsigned int g_kws_model_len;
alignas(16) const unsigned char g_kws_model[] = { 0x20, 0x00, 0x00, 0x00, 0x54, 0x46, 0x4c, 0x33, ... };
const unsigned int g_kws_model_len = 19240;
```

- `const` keeps the array in **flash**; TFLite Micro reads the FlatBuffer in place, with no copy to RAM.
- `alignas(16)` keeps tensor data aligned for the kernels.
- The checked-in `model_data.cc` is a **placeholder trained on synthetic tones**. It lets the project build and run, but it will not recognise words until you export your own model.

## Step 2 — build and flash

Close the workshop browser tab first (it holds the port).

```bash
cd ../firmware/kws-inference
idf.py set-target esp32s3
idf.py build flash monitor          # add -p COM5 / -p /dev/ttyACM0 if needed; Ctrl+] leaves the monitor
```

## Step 3 — put the workshop firmware back

```bash
cd hardware-interface-workshop/firmware-prebuilt/es3c28p
python -m esptool --chip esp32s3 -p <PORT> write-flash "@flash_args"
# Windows: py -m esptool --chip esp32s3 -p COMx write-flash "@flash_args"
```

Then `python collect.py --port <PORT> --info` should print the `BoardInfo` line again.

> [!NOTE]
> These projects were written against ESP-IDF v6.1 and the component versions above, and their API use was checked against those sources. They have **not** been built with `idf.py` or flashed for this course yet. Record your build result and your hardware result separately, as in Week 03.

## The firmware architecture

```text
  core 0                                   core 1
┌────────────────────────┐   queue    ┌──────────────────────────────────────────┐
│ capture_task  prio 6   │  16 × 20ms │ inference_task  prio 4                   │
│ es3c28p_audio_read_mono│ ─────────► │ append block to 1 s ring buffer          │
│ 320 samples / 20 ms    │  (640 B    │ every 25 blocks (500 ms):                │
│ xQueueSend(..., 0)     │   each)    │   linearise ring → kws_features_compute  │
│ if full: dropped++     │            │   quantize → interpreter.Invoke()        │
└────────────────────────┘            │   average 3 results → threshold → LED    │
                                      │   printf scores + latency + queue state  │
                                      └──────────────────────────────────────────┘
```

### Why two tasks and a queue?

- **Audio never waits.** The I2S DMA buffers hold only a few tens of milliseconds. If the CPU is busy with an FFT when they fill, samples are lost. The capture task has the higher priority and does almost no work, so it always runs on time.
- **Inference may be late, not lost.** The queue holds 16 blocks (320 ms). If one inference takes longer than usual, blocks wait in the queue and the inference task catches up.
- **Never block the producer.** `xQueueSend(..., 0)` returns immediately when the queue is full and increments `s_dropped_blocks`. A growing drop count means inference is too slow for the hop length.

This is the producer/consumer pattern from [Week 02, Lesson 15](../../week02/lessons/EN/15-embedded-c-freertos-review.md), applied to a real-time signal.

### The interpreter and the static arena

```cpp
alignas(16) static uint8_t s_arena[KWS_ARENA_BYTES];          // 64 KB, internal RAM, no malloc

const tflite::Model *model = tflite::GetModel(g_kws_model);
static tflite::MicroMutableOpResolver<6> resolver;           // only the ops we use
resolver.AddConv2D();
resolver.AddDepthwiseConv2D();
resolver.AddFullyConnected();
resolver.AddMean();
resolver.AddSoftmax();
resolver.AddReshape();
static tflite::MicroInterpreter interpreter(model, resolver, s_arena, KWS_ARENA_BYTES);
interpreter.AllocateTensors();                                // plans all tensors inside the arena
ESP_LOGI(TAG, "arena used %u", (unsigned)interpreter.arena_used_bytes());
```

- **Static arena:** all activations live in one array sized at compile time. No heap fragmentation, and the memory cost is visible in the map file.
- **Op resolver:** registers only the ops `train.py` printed. A missing op makes `AllocateTensors()` fail with a clear log message; unused ops waste flash.
- **Arena size:** the TFLite Micro reference interpreter on a PC needed about 37 KB for the course model. The firmware reserves 64 KB and prints the real usage at boot. Shrink `KWS_ARENA_BYTES` to the printed value plus a margin.

### On-device features must match training

`kws_features.c` implements the same steps as `kws_common.log_mel()`, with the same constants (`KWS_FRAME_LEN 480`, `KWS_FRAME_STEP 320`, `KWS_FFT_LEN 512`, `KWS_NUM_MEL 40`, 20–7600 Hz, `ln(x + 1e-6)`). It is plain C99 and builds on a PC, so `verify_c_features.py` can compare it with Python on your own clips.

The **audio** feeding those features is a different story. Your training clips came through the workshop firmware's capture chain; `kws-inference` has its own, simpler one:

| | Workshop prebuilt firmware (training clips) | `kws-inference` (on-device) |
|---|---|---|
| Channel | louder of the two I2S slots | `KWS_MIC_SLOT -1` does the same (or pick 0 / 1) |
| Gain | `MicCmd.gain_pct` (`collect.py --gain`, default 60 %) spread over PGA + ADC scale + digital volume | `KWS_MIC_GAIN_DB` through `esp_codec_dev` |
| Filters | 40 Hz high-pass, 6.5 kHz low-pass, soft limiter | none (the feature code removes the mean of each frame) |

So the board may hear the same word **louder or quieter, and slightly brighter**, than the clips the model learned from. Log-mel features turn a level difference into a constant offset, and the training augmentation only covers about ±6 dB. To match:

1. Each log line ends with the **dBFS level** of the newest 500 ms.
2. Say a keyword at the same distance you used for collection and compare with the `rms` that `collect.py` printed for your clips.
3. Change `KWS_MIC_GAIN_DB` until the two are within a few dB, rebuild, and test again.
4. Better still (Mini-Project 2): record a few clips **through `kws-inference`** itself, or add the same 40 Hz / 6.5 kHz filters to the capture task, and check the confusion matrix again.

```c
#define KWS_MIC_GAIN_DB  30.0f   // (!) match the level of your training clips (see the dBFS column)
#define KWS_MIC_SLOT     (-1)    // (!) louder slot, like the workshop firmware
```

### Measuring latency with `esp_timer`

```cpp
const int64_t t0 = esp_timer_get_time();     // microseconds since boot
kws_features_compute(s_window, s_features);
const int64_t t1 = esp_timer_get_time();
/* quantize input */
const int64_t t2 = esp_timer_get_time();
interpreter.Invoke();
const int64_t t3 = esp_timer_get_time();
```

Each inference prints one line:

```text
red        0.86 DETECTED | features  xx.x ms  quant  x.x ms  invoke  xx.x ms | queue 0/16 dropped 0 |  -xx.x dBFS
```

Fill in this table from your board's log (no hardware numbers are given here because the course build has not been run on a board yet):

| Stage | Your time (ms) | Budget |
|---|---|---|
| Features (49 FFTs + mel) | | |
| Input quantization (1,960 values) | | |
| `Invoke()` | | |
| **Total per hop** | | must stay well below the 500 ms hop |
| Detection delay (end of word → LED) | | hop + smoothing ≈ 0.5–1.5 s |

### Output: WS2812 and the log

`show_label()` sets the WS2812 on GPIO42 with the `led_strip` RMT driver ([Week 02, Lesson 11](../../week02/lessons/EN/11-ws2812-rmt-led.md)): red, green, or blue for those words, LED off for `off`. Every result is also printed, so the serial log is your on-device test report.

**Display (stretch goal):** show the top label and score on the ILI9341 using `esp_lcd` with the `espressif/esp_lcd_ili9341` component (see [Week 02, Lesson 08](../../week02/lessons/EN/08-ili9341-display.md) and the 14 November touch-screen UI session). Keep drawing in its own low-priority task fed by a small queue, so a slow SPI transfer never delays capture.

## Exercises

1. Flash, open the monitor, and fill in the latency table.
2. Set `KWS_HOP_BLOCKS` to 5 (100 ms). Do `queue` and `dropped` grow? What is the smallest safe hop?
3. Temporarily give the inference task a **higher** priority than capture, on the same core. What happens to `dropped`, and why?
4. Print `interpreter.arena_used_bytes()` and reduce `KWS_ARENA_BYTES` to fit.
5. Use `vTaskGetRunTimeStats()` (enabled in `sdkconfig.defaults`) to print CPU use per task every 10 s.
6. Collect 20 board clips of a keyword the board misses (reflash the workshop firmware, `collect.py`), retrain, export, and flash `kws-inference` again. Did the confusion matrix and the board behaviour both improve?
7. Match levels: compare the dBFS column with your `collect.py` clips and tune `KWS_MIC_GAIN_DB`.

## Check your understanding

1. Why does the capture task use a zero timeout in `xQueueSend`?
2. What happens if you register `AddConv2D` but forget `AddMean`?
3. Where do the model weights live at run time, and where do the activations live?
4. After this lesson, `collect.py` reports "No BoardInfo frame received". Why, and what is the fix?
