/*
 * Week 08 - touch-logger (gesture track)
 *
 * Polls the FT6336G capacitive touch controller every 10 ms and prints one text line
 * per event on the USB Serial/JTAG console. labs/python/collect_touch.py turns the
 * lines into labelled stroke files.
 *
 *   D <x> <y> <t_ms>    finger down
 *   M <x> <y> <t_ms>    finger moved (only when the position changed)
 *   U <t_ms>            finger up
 *   E <err>             I2C read failed (NOT treated as "finger up")
 *
 * Pins (Week 02, Lesson 09): SDA GPIO16, SCL GPIO15, INT GPIO17, RST GPIO18 (active low),
 * FT6336G 7-bit address 0x38. The bus is shared with the ES8311 codec (0x18).
 */
#include <stdbool.h>
#include <stdio.h>

#include "driver/gpio.h"
#include "driver/i2c_master.h"
#include "esp_err.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#define TOUCH_SDA      16
#define TOUCH_SCL      15
#define TOUCH_RST      18
#define TOUCH_ADDR     0x38
#define REG_TD_STATUS  0x02      /* followed by P1_XH, P1_XL, P1_YH, P1_YL */
#define POLL_MS        10

static i2c_master_dev_handle_t s_touch;

static void touch_init(void)
{
    gpio_config_t rst = { .pin_bit_mask = 1ULL << TOUCH_RST, .mode = GPIO_MODE_OUTPUT };
    ESP_ERROR_CHECK(gpio_config(&rst));
    gpio_set_level(TOUCH_RST, 0);                 /* reset pulse */
    vTaskDelay(pdMS_TO_TICKS(10));
    gpio_set_level(TOUCH_RST, 1);
    vTaskDelay(pdMS_TO_TICKS(300));               /* controller boot time */

    i2c_master_bus_config_t bus_cfg = {
        .i2c_port = I2C_NUM_0,
        .sda_io_num = TOUCH_SDA,
        .scl_io_num = TOUCH_SCL,
        .clk_source = I2C_CLK_SRC_DEFAULT,
        .glitch_ignore_cnt = 7,
        .flags.enable_internal_pullup = true,
    };
    i2c_master_bus_handle_t bus;
    ESP_ERROR_CHECK(i2c_new_master_bus(&bus_cfg, &bus));
    i2c_device_config_t dev_cfg = {
        .dev_addr_length = I2C_ADDR_BIT_LEN_7,
        .device_address = TOUCH_ADDR,
        .scl_speed_hz = 400000,
    };
    ESP_ERROR_CHECK(i2c_master_bus_add_device(bus, &dev_cfg, &s_touch));
    ESP_ERROR_CHECK(i2c_master_probe(bus, TOUCH_ADDR, 100));
}

/* Returns ESP_OK and sets *down/x/y, or an error (which is NOT a release). */
static esp_err_t touch_read(bool *down, int *x, int *y)
{
    uint8_t reg = REG_TD_STATUS, d[5];
    esp_err_t err = i2c_master_transmit_receive(s_touch, &reg, 1, d, sizeof(d), 50);
    if (err != ESP_OK) {
        return err;
    }
    int touches = d[0] & 0x0F;
    *down = touches >= 1 && touches <= 2;
    *x = ((d[1] & 0x0F) << 8) | d[2];             /* mask the event-flag bits in XH */
    *y = ((d[3] & 0x0F) << 8) | d[4];             /* mask the touch-id bits in YH */
    return ESP_OK;
}

void app_main(void)
{
    touch_init();
    printf("TOUCH-LOGGER v1 ready\n");
    bool was_down = false;
    int last_x = -1, last_y = -1;
    for (;;) {
        bool down;
        int x, y;
        esp_err_t err = touch_read(&down, &x, &y);
        int64_t t_ms = esp_timer_get_time() / 1000;
        if (err != ESP_OK) {
            printf("E %s\n", esp_err_to_name(err));
        } else if (down && !was_down) {
            printf("D %d %d %lld\n", x, y, t_ms);
            last_x = x; last_y = y;
        } else if (down && (x != last_x || y != last_y)) {
            printf("M %d %d %lld\n", x, y, t_ms);
            last_x = x; last_y = y;
        } else if (!down && was_down) {
            printf("U %lld\n", t_ms);
        }
        if (err == ESP_OK) {
            was_down = down;
        }
        vTaskDelay(pdMS_TO_TICKS(POLL_MS));
    }
}
