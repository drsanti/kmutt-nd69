#pragma once
// Week 08 kws-inference settings. Values marked (!) must match data collection.

#define KWS_MIC_GAIN_DB        30.0f   // (!) same as audio-logger MIC_GAIN_DB
#define KWS_MIC_SLOT           0       // (!) same as audio-logger MIC_SLOT

#define KWS_BLOCK_SAMPLES      320     // 20 ms per capture block
#define KWS_QUEUE_DEPTH        16      // 320 ms of buffering between capture and inference
#define KWS_HOP_BLOCKS         25      // run the model every 25 blocks = 500 ms
#define KWS_SMOOTH_WINDOW      3       // average the last 3 probability vectors
#define KWS_THRESHOLD          0.70f   // averaged score needed to accept a keyword
#define KWS_REFRACTORY_HOPS    2       // ignore new detections for 2 hops (1 s) after one

#define KWS_ARENA_BYTES        (64 * 1024)   // TFLM tensor arena; the log prints the real usage

#define KWS_LED_GPIO           42      // WS2812 (Week 02, Lesson 11)

#define KWS_CAPTURE_PRIO       6       // higher: must never miss audio
#define KWS_INFER_PRIO         4       // lower: may be late, must not block capture
#define KWS_CAPTURE_STACK      4096
#define KWS_INFER_STACK        (12 * 1024)
