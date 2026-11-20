#pragma once
// The int8 TFLite model as a C array. Regenerate model_data.cc with
//   python labs/python/export_c_array.py --model artifacts/model_int8.tflite --out-dir <this folder>
extern const unsigned char g_kws_model[];
extern const unsigned int g_kws_model_len;
