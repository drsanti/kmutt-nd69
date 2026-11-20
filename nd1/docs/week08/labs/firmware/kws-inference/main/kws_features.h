/*
 * Log-mel features for keyword spotting - the C twin of labs/python/kws_common.py.
 *
 * MUST match training exactly. Any change here (or there) needs the same change on the
 * other side and a re-run of labs/python/verify_c_features.py.
 *
 *   int16 PCM 16 kHz, 16000 samples -> /32768 -> subtract clip mean
 *   -> 49 frames x 480 samples (hop 320) -> periodic Hann -> 512-point FFT -> power
 *   -> 40 mel filters (HTK, 20-7600 Hz, continuous triangles) -> ln(x + 1e-6)
 *
 * Plain C99 + libm, no ESP-IDF headers, so it also compiles on a PC for testing.
 */
#pragma once

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define KWS_SAMPLE_RATE   16000
#define KWS_CLIP_SAMPLES  16000
#define KWS_FRAME_LEN     480
#define KWS_FRAME_STEP    320
#define KWS_FFT_LEN       512
#define KWS_NUM_MEL       40
#define KWS_MEL_FMIN      20.0
#define KWS_MEL_FMAX      7600.0
#define KWS_LOG_EPS       1e-6f
#define KWS_NUM_FRAMES    (1 + (KWS_CLIP_SAMPLES - KWS_FRAME_LEN) / KWS_FRAME_STEP)   /* 49 */
#define KWS_NUM_FEATURES  (KWS_NUM_FRAMES * KWS_NUM_MEL)                              /* 1960 */

/* Build the window, FFT tables and mel filterbank. Call once before compute. */
void kws_features_init(void);

/* pcm: KWS_CLIP_SAMPLES samples. out: KWS_NUM_FEATURES floats, row-major [frame][mel]. */
void kws_features_compute(const int16_t *pcm, float *out);

#ifdef __cplusplus
}
#endif
