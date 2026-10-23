# robotos package config — find_package(robotos)
# Provides imported targets:
#   robotos::ffi   — C ABI shared library (required for all language
#                    bindings and C users)
#   robotos::cpp   — prebuilt C++20 RAII SDK (static, links ffi)
#   robotos::msgs  — prebuilt protobuf message types (static,
#                    requires system protobuf)

get_filename_component(ROBOTOS_PACKAGE_ROOT
    "${CMAKE_CURRENT_LIST_DIR}/../.." ABSOLUTE)

set(ROBOTOS_INCLUDE_DIR "${ROBOTOS_PACKAGE_ROOT}/include")
set(ROBOTOS_LIB_DIR "${ROBOTOS_PACKAGE_ROOT}/lib")

# --- C ABI shared library --------------------------------------------
if(NOT TARGET robotos::ffi)
    add_library(robotos::ffi SHARED IMPORTED)
    if(WIN32)
        set_target_properties(robotos::ffi PROPERTIES
            IMPORTED_LOCATION "${ROBOTOS_LIB_DIR}/robotos_ffi.dll"
            IMPORTED_IMPLIB "${ROBOTOS_LIB_DIR}/robotos_ffi.lib"
            INTERFACE_INCLUDE_DIRECTORIES "${ROBOTOS_INCLUDE_DIR}")
    else()
        set_target_properties(robotos::ffi PROPERTIES
            IMPORTED_LOCATION
                "${ROBOTOS_LIB_DIR}/${CMAKE_SHARED_LIBRARY_PREFIX}robotos_ffi${CMAKE_SHARED_LIBRARY_SUFFIX}"
            INTERFACE_INCLUDE_DIRECTORIES "${ROBOTOS_INCLUDE_DIR}")
    endif()
endif()

# --- C++ SDK (static, built from the C ABI) --------------------------
if(NOT TARGET robotos::cpp)
    add_library(robotos::cpp STATIC IMPORTED)
    set_target_properties(robotos::cpp PROPERTIES
        IMPORTED_LOCATION
            "${ROBOTOS_LIB_DIR}/${CMAKE_STATIC_LIBRARY_PREFIX}robotos_cpp${CMAKE_STATIC_LIBRARY_SUFFIX}"
        INTERFACE_INCLUDE_DIRECTORIES "${ROBOTOS_INCLUDE_DIR}"
        INTERFACE_LINK_LIBRARIES robotos::ffi
        INTERFACE_COMPILE_FEATURES cxx_std_20)
endif()

# --- Protobuf message types (static, needs system protobuf) ----------
if(NOT TARGET robotos::msgs)
    add_library(robotos::msgs STATIC IMPORTED)
    set_target_properties(robotos::msgs PROPERTIES
        IMPORTED_LOCATION
            "${ROBOTOS_LIB_DIR}/${CMAKE_STATIC_LIBRARY_PREFIX}robotos_msgs${CMAKE_STATIC_LIBRARY_SUFFIX}"
        INTERFACE_INCLUDE_DIRECTORIES "${ROBOTOS_INCLUDE_DIR}")
    find_package(Protobuf QUIET)
    if(Protobuf_FOUND)
        set_property(TARGET robotos::msgs APPEND PROPERTY
            INTERFACE_LINK_LIBRARIES protobuf::libprotobuf)
    endif()
endif()

set(ROBOTOS_FOUND TRUE)
