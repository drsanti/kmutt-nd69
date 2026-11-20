# esp-tflite-micro and led_strip come from main/idf_component.yml and are added
# to this component's requirements automatically by the component manager.
idf_component_register(SRCS "kws_main.cc" "kws_features.c" "model_data.cc"
                       PRIV_REQUIRES es3c28p_audio esp_timer
                       INCLUDE_DIRS ".")

# TFLite Micro headers trigger a few warnings that ESP-IDF treats as errors.
target_compile_options(${COMPONENT_LIB} PRIVATE
    -Wno-maybe-uninitialized
    -Wno-missing-field-initializers
    -Wno-error=sign-compare
    -Wno-error=double-promotion
    -Wno-type-limits)
