idf_component_register(SRCS "touch_logger_main.c"
                       PRIV_REQUIRES esp_driver_i2c esp_driver_gpio esp_timer
                       INCLUDE_DIRS "")
