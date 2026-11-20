# Week 08 - touch-logger: stream FT6336G touch strokes to the PC for the gesture track.
cmake_minimum_required(VERSION 3.22)
include($ENV{IDF_PATH}/tools/cmake/project.cmake)
idf_build_set_property(MINIMAL_BUILD ON)
project(touch_logger)
