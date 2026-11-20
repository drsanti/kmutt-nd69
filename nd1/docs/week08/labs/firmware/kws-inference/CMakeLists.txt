# Week 08 - kws-inference: on-device keyword spotting with TensorFlow Lite Micro.
cmake_minimum_required(VERSION 3.22)

# Shared board code (ES8311 microphone capture) lives in ../components.
set(EXTRA_COMPONENT_DIRS "${CMAKE_CURRENT_LIST_DIR}/../components")

include($ENV{IDF_PATH}/tools/cmake/project.cmake)
idf_build_set_property(MINIMAL_BUILD ON)
project(kws_inference)
