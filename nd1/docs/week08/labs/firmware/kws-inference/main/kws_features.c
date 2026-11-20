#include "kws_features.h"

#include <math.h>
#include <string.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

#define NUM_BINS (KWS_FFT_LEN / 2 + 1)
#define MAX_FB_WEIGHTS 1024

static float s_window[KWS_FRAME_LEN];
static float s_cos[KWS_FFT_LEN / 2];
static float s_sin[KWS_FFT_LEN / 2];
static uint16_t s_bitrev[KWS_FFT_LEN];

/* Sparse mel filterbank: filter m uses bins [s_fb_start[m], s_fb_start[m] + s_fb_len[m]). */
static uint16_t s_fb_start[KWS_NUM_MEL];
static uint16_t s_fb_len[KWS_NUM_MEL];
static uint16_t s_fb_offset[KWS_NUM_MEL];
static float s_fb_weight[MAX_FB_WEIGHTS];

static float s_re[KWS_FFT_LEN];
static float s_im[KWS_FFT_LEN];
static float s_power[NUM_BINS];

static double hz_to_mel(double f) { return 2595.0 * log10(1.0 + f / 700.0); }
static double mel_to_hz(double m) { return 700.0 * (pow(10.0, m / 2595.0) - 1.0); }

void kws_features_init(void)
{
    for (int n = 0; n < KWS_FRAME_LEN; n++) {   /* periodic Hann */
        s_window[n] = (float)(0.5 - 0.5 * cos(2.0 * M_PI * n / KWS_FRAME_LEN));
    }
    for (int k = 0; k < KWS_FFT_LEN / 2; k++) {
        s_cos[k] = (float)cos(2.0 * M_PI * k / KWS_FFT_LEN);
        s_sin[k] = (float)-sin(2.0 * M_PI * k / KWS_FFT_LEN);
    }
    int bits = 0;
    while ((1 << bits) < KWS_FFT_LEN) {
        bits++;
    }
    for (int i = 0; i < KWS_FFT_LEN; i++) {
        int r = 0;
        for (int b = 0; b < bits; b++) {
            r |= ((i >> b) & 1) << (bits - 1 - b);
        }
        s_bitrev[i] = (uint16_t)r;
    }

    double mel_lo = hz_to_mel(KWS_MEL_FMIN), mel_hi = hz_to_mel(KWS_MEL_FMAX);
    double edges[KWS_NUM_MEL + 2];
    for (int i = 0; i < KWS_NUM_MEL + 2; i++) {
        edges[i] = mel_to_hz(mel_lo + (mel_hi - mel_lo) * i / (KWS_NUM_MEL + 1));
    }
    int offset = 0;
    for (int m = 0; m < KWS_NUM_MEL; m++) {
        double lo = edges[m], center = edges[m + 1], hi = edges[m + 2];
        int first = -1, count = 0;
        for (int k = 0; k < NUM_BINS; k++) {
            double f = (double)k * KWS_SAMPLE_RATE / KWS_FFT_LEN;
            double up = (f - lo) / (center - lo);
            double down = (hi - f) / (hi - center);
            double w = up < down ? up : down;
            if (w > 0.0) {
                if (first < 0) {
                    first = k;
                }
                if (offset + count < MAX_FB_WEIGHTS) {
                    s_fb_weight[offset + count] = (float)w;
                }
                count++;
            }
        }
        s_fb_start[m] = (uint16_t)(first < 0 ? 0 : first);
        s_fb_len[m] = (uint16_t)count;
        s_fb_offset[m] = (uint16_t)offset;
        offset += count;
    }
}

/* In-place iterative radix-2 complex FFT of KWS_FFT_LEN points. */
static void fft(float *re, float *im)
{
    for (int i = 0; i < KWS_FFT_LEN; i++) {
        int j = s_bitrev[i];
        if (j > i) {
            float t = re[i]; re[i] = re[j]; re[j] = t;
            t = im[i]; im[i] = im[j]; im[j] = t;
        }
    }
    for (int size = 2; size <= KWS_FFT_LEN; size <<= 1) {
        int half = size >> 1, step = KWS_FFT_LEN / size;
        for (int start = 0; start < KWS_FFT_LEN; start += size) {
            for (int k = 0; k < half; k++) {
                float wr = s_cos[k * step], wi = s_sin[k * step];
                int a = start + k, b = a + half;
                float tr = re[b] * wr - im[b] * wi;
                float ti = re[b] * wi + im[b] * wr;
                re[b] = re[a] - tr; im[b] = im[a] - ti;
                re[a] += tr;        im[a] += ti;
            }
        }
    }
}

void kws_features_compute(const int16_t *pcm, float *out)
{
    double sum = 0.0;
    for (int i = 0; i < KWS_CLIP_SAMPLES; i++) {
        sum += pcm[i] / 32768.0;
    }
    const float mean = (float)(sum / KWS_CLIP_SAMPLES);

    for (int fr = 0; fr < KWS_NUM_FRAMES; fr++) {
        const int16_t *x = pcm + fr * KWS_FRAME_STEP;
        for (int i = 0; i < KWS_FRAME_LEN; i++) {
            s_re[i] = (x[i] / 32768.0f - mean) * s_window[i];
        }
        memset(&s_re[KWS_FRAME_LEN], 0, sizeof(float) * (KWS_FFT_LEN - KWS_FRAME_LEN));
        memset(s_im, 0, sizeof(s_im));
        fft(s_re, s_im);
        for (int k = 0; k < NUM_BINS; k++) {
            s_power[k] = s_re[k] * s_re[k] + s_im[k] * s_im[k];
        }
        float *row = out + fr * KWS_NUM_MEL;
        for (int m = 0; m < KWS_NUM_MEL; m++) {
            const float *w = &s_fb_weight[s_fb_offset[m]];
            const float *p = &s_power[s_fb_start[m]];
            float e = 0.0f;
            for (int j = 0; j < s_fb_len[m]; j++) {
                e += w[j] * p[j];
            }
            row[m] = logf(e + KWS_LOG_EPS);
        }
    }
}
