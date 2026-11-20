idf_component_register(SRCS "es3c28p_audio.c"
                       INCLUDE_DIRS "include"
                       REQUIRES esp_driver_i2c
                       PRIV_REQUIRES esp_driver_i2s esp_driver_gpio)
