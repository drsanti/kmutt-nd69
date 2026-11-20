/*
 * Week 08 - kws-inference
 *
 *   capture_task (prio 6) --[queue of 20 ms blocks]--> inference_task (prio 4)
 *        ES8311 mic via I2S                               1 s ring buffer
 *                                                         every 500 ms: log-mel -> int8 -> TFLM
 *                                                         smoothing + threshold -> WS2812 + log
 *
 * Latency of each stage is measured with esp_timer_get_time() and printed.
 */
#include <atomic>
#include <cmath>
#include <cstdio>
#include <cstring>

#include "esp_log.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/queue.h"
#include "freertos/task.h"
#include "led_strip.h"

#include "tensorflow/lite/micro/micro_interpreter.h"
#include "tensorflow/lite/micro/micro_mutable_op_resolver.h"
#include "tensorflow/lite/micro/schema/schema_generated.h"

#include "es3c28p_audio.h"
#include "kws_config.h"
#include "kws_features.h"
#include "kws_labels.h"
#include "model_data.h"

static const char *TAG = "kws";

typedef struct {
    int16_t samples[KWS_BLOCK_SAMPLES];
} audio_block_t;

static QueueHandle_t s_audio_q;
static std::atomic<uint32_t> s_dropped_blocks{0};   // written by capture, read by inference
static led_strip_handle_t s_led;

alignas(16) static uint8_t s_arena[KWS_ARENA_BYTES];
static int16_t s_ring[KWS_CLIP_SAMPLES];
static int16_t s_window[KWS_CLIP_SAMPLES];
static float s_features[KWS_NUM_FEATURES];
static float s_history[KWS_SMOOTH_WINDOW][KWS_NUM_LABELS];

// ------------------------------------------------------------------ capture (producer)
static void capture_task(void *arg)
{
    audio_block_t block;
    for (;;) {
        if (es3c28p_audio_read_mono(block.samples, KWS_BLOCK_SAMPLES) != ESP_OK) {
            ESP_LOGE(TAG, "audio read failed");
            vTaskDelay(pdMS_TO_TICKS(10));
            continue;
        }
        // Never block the producer: if inference is late, count the loss and move on.
        if (xQueueSend(s_audio_q, &block, 0) != pdTRUE) {
            s_dropped_blocks++;
        }
    }
}

// ------------------------------------------------------------------ output
static void show_label(int label)
{
    const char *name = kKwsLabels[label];
    uint32_t r = 0, g = 0, b = 0;
    if (strcmp(name, "red") == 0) r = 40;
    else if (strcmp(name, "green") == 0) g = 40;
    else if (strcmp(name, "blue") == 0) b = 40;
    if (strcmp(name, "off") == 0) {
        led_strip_clear(s_led);
    } else {
        led_strip_set_pixel(s_led, 0, r, g, b);
        led_strip_refresh(s_led);
    }
}

static void init_led(void)
{
    led_strip_config_t strip_cfg = {};
    strip_cfg.strip_gpio_num = KWS_LED_GPIO;
    strip_cfg.max_leds = 1;
    strip_cfg.led_model = LED_MODEL_WS2812;
    // color_component_format left zero: led_strip falls back to GRB, the WS2812 order.
    led_strip_rmt_config_t rmt_cfg = {};
    rmt_cfg.clk_src = RMT_CLK_SRC_DEFAULT;
    rmt_cfg.resolution_hz = 10 * 1000 * 1000;
    ESP_ERROR_CHECK(led_strip_new_rmt_device(&strip_cfg, &rmt_cfg, &s_led));
    led_strip_clear(s_led);
}

// ------------------------------------------------------------------ inference (consumer)
static void inference_task(void *arg)
{
    const tflite::Model *model = tflite::GetModel(g_kws_model);
    if (model->version() != TFLITE_SCHEMA_VERSION) {
        ESP_LOGE(TAG, "model schema %lu != supported %d", (unsigned long)model->version(), TFLITE_SCHEMA_VERSION);
        vTaskDelete(nullptr);
    }

    // Register exactly the ops reported by train.py ("int8 ops ...").
    static tflite::MicroMutableOpResolver<6> resolver;
    resolver.AddConv2D();
    resolver.AddDepthwiseConv2D();
    resolver.AddFullyConnected();
    resolver.AddMean();
    resolver.AddSoftmax();
    resolver.AddReshape();

    static tflite::MicroInterpreter interpreter(model, resolver, s_arena, KWS_ARENA_BYTES);
    if (interpreter.AllocateTensors() != kTfLiteOk) {
        ESP_LOGE(TAG, "AllocateTensors failed: increase KWS_ARENA_BYTES");
        vTaskDelete(nullptr);
    }
    TfLiteTensor *input = interpreter.input(0);
    TfLiteTensor *output = interpreter.output(0);
    if (input->type != kTfLiteInt8 || input->dims->data[1] != KWS_NUM_FRAMES ||
        input->dims->data[2] != KWS_NUM_MEL || output->dims->data[1] != KWS_NUM_LABELS) {
        ESP_LOGE(TAG, "model shape/type does not match kws_features.h / kws_labels.h");
        vTaskDelete(nullptr);
    }
    const float in_scale = input->params.scale;
    const int in_zp = input->params.zero_point;
    const float out_scale = output->params.scale;
    const int out_zp = output->params.zero_point;
    ESP_LOGI(TAG, "model %u bytes, arena used %u of %u bytes, input scale %.6f zp %d",
             g_kws_model_len, (unsigned)interpreter.arena_used_bytes(), (unsigned)KWS_ARENA_BYTES, in_scale, in_zp);

    audio_block_t block;
    size_t write_pos = 0, filled = 0;
    int blocks_since_run = 0, hist_count = 0, refractory = 0;

    for (;;) {
        xQueueReceive(s_audio_q, &block, portMAX_DELAY);
        memcpy(&s_ring[write_pos], block.samples, sizeof(block.samples));
        write_pos = (write_pos + KWS_BLOCK_SAMPLES) % KWS_CLIP_SAMPLES;   // 16000 is a multiple of 320
        filled = filled + KWS_BLOCK_SAMPLES > KWS_CLIP_SAMPLES ? KWS_CLIP_SAMPLES : filled + KWS_BLOCK_SAMPLES;
        if (++blocks_since_run < KWS_HOP_BLOCKS || filled < KWS_CLIP_SAMPLES) {
            continue;
        }
        blocks_since_run = 0;

        // Oldest sample first: [write_pos .. end) then [0 .. write_pos)
        const size_t tail = KWS_CLIP_SAMPLES - write_pos;
        memcpy(s_window, &s_ring[write_pos], tail * sizeof(int16_t));
        memcpy(&s_window[tail], s_ring, write_pos * sizeof(int16_t));

        const int64_t t0 = esp_timer_get_time();
        kws_features_compute(s_window, s_features);
        const int64_t t1 = esp_timer_get_time();
        for (int i = 0; i < KWS_NUM_FEATURES; i++) {   // same rule as kws_common.run_tflite()
            int q = (int)lroundf(s_features[i] / in_scale) + in_zp;
            input->data.int8[i] = (int8_t)(q < -128 ? -128 : (q > 127 ? 127 : q));
        }
        const int64_t t2 = esp_timer_get_time();
        if (interpreter.Invoke() != kTfLiteOk) {
            ESP_LOGE(TAG, "Invoke failed");
            continue;
        }
        const int64_t t3 = esp_timer_get_time();

        float *probs = s_history[hist_count % KWS_SMOOTH_WINDOW];
        for (int c = 0; c < KWS_NUM_LABELS; c++) {
            probs[c] = (output->data.int8[c] - out_zp) * out_scale;
        }
        hist_count++;
        const int n = hist_count < KWS_SMOOTH_WINDOW ? hist_count : KWS_SMOOTH_WINDOW;
        int top = 0;
        float avg[KWS_NUM_LABELS] = {0};
        for (int c = 0; c < KWS_NUM_LABELS; c++) {
            for (int h = 0; h < n; h++) avg[c] += s_history[h][c];
            avg[c] /= n;
            if (avg[c] > avg[top]) top = c;
        }

        bool detected = false;
        if (refractory > 0) {
            refractory--;
        } else if (top != KWS_LABEL_SILENCE && top != KWS_LABEL_UNKNOWN && avg[top] >= KWS_THRESHOLD) {
            detected = true;
            refractory = KWS_REFRACTORY_HOPS;
            show_label(top);
        }
        printf("%-10s %.2f %s| features %5.1f ms  quant %4.1f ms  invoke %5.1f ms | queue %u/%d dropped %lu\n",
               kKwsLabels[top], avg[top], detected ? "DETECTED " : "         ",
               (t1 - t0) / 1000.0, (t2 - t1) / 1000.0, (t3 - t2) / 1000.0,
               (unsigned)uxQueueMessagesWaiting(s_audio_q), KWS_QUEUE_DEPTH, (unsigned long)s_dropped_blocks.load());
    }
}

extern "C" void app_main(void)
{
    init_led();
    kws_features_init();

    es3c28p_audio_config_t audio_cfg = { .gain_db = KWS_MIC_GAIN_DB, .mic_slot = KWS_MIC_SLOT };
    ESP_ERROR_CHECK(es3c28p_audio_init(&audio_cfg));

    s_audio_q = xQueueCreate(KWS_QUEUE_DEPTH, sizeof(audio_block_t));
    configASSERT(s_audio_q);

    // Pinning keeps the two stages on different cores; priorities still matter on each core.
    xTaskCreatePinnedToCore(inference_task, "kws_infer", KWS_INFER_STACK, nullptr, KWS_INFER_PRIO, nullptr, 1);
    xTaskCreatePinnedToCore(capture_task, "kws_capture", KWS_CAPTURE_STACK, nullptr, KWS_CAPTURE_PRIO, nullptr, 0);
    ESP_LOGI(TAG, "listening for: red, green, blue, off");
}
