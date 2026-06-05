cmake_minimum_required(VERSION 3.18)
project(traffic_edge_app VERSION 2.3.1 LANGUAGES CXX C)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_BUILD_TYPE Release CACHE STRING "Build type")

# ── 交叉编译配置 ─────────────────────────────────────────────
# 使用方式：cmake -DCMAKE_TOOLCHAIN_FILE=../cmake/aarch64-toolchain.cmake ..
if(DEFINED CMAKE_TOOLCHAIN_FILE)
    message(STATUS "Cross-compiling with toolchain: ${CMAKE_TOOLCHAIN_FILE}")
endif()

# ── 依赖库查找 ───────────────────────────────────────────────
find_package(OpenCV 4.5 REQUIRED COMPONENTS core imgproc imgcodecs highgui)
find_package(Threads REQUIRED)
find_package(Protobuf REQUIRED)
find_package(gRPC CONFIG REQUIRED)

# Vitis AI Runtime（VART）
find_library(VART_LIB   vart-runner PATHS /usr/lib /opt/vitis_ai/lib REQUIRED)
find_library(XIR_LIB    xir          PATHS /usr/lib /opt/vitis_ai/lib REQUIRED)
find_library(TARGET_LIB target-factory PATHS /usr/lib REQUIRED)

# MQTT
find_library(MOSQUITTO_LIB mosquitto REQUIRED)

# JSON（Header-only，使用 nlohmann/json）
find_path(NLOHMANN_JSON_INCLUDE nlohmann/json.hpp
    PATHS /usr/include /usr/local/include REQUIRED)

# ── Protobuf 代码生成 ────────────────────────────────────────
set(PROTO_SRC_DIR ${CMAKE_SOURCE_DIR}/../proto)
set(PROTO_OUT_DIR ${CMAKE_BINARY_DIR}/proto_gen)
file(MAKE_DIRECTORY ${PROTO_OUT_DIR})

file(GLOB PROTO_FILES "${PROTO_SRC_DIR}/*.proto")
protobuf_generate_cpp(PROTO_SRCS PROTO_HDRS ${PROTO_FILES})
grpc_generate_cpp(GRPC_SRCS GRPC_HDRS ${PROTO_OUT_DIR} ${PROTO_FILES})

# ── 主可执行文件 ─────────────────────────────────────────────
set(APP_SOURCES
    main.cpp
    frame_manager.cpp
    inference_engine.cpp
    event_detector.cpp
    utils/config.cpp
    utils/logger.cpp
    ${PROTO_SRCS}
    ${GRPC_SRCS}
)

add_executable(traffic_edge_app ${APP_SOURCES})

target_include_directories(traffic_edge_app PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${PROTO_OUT_DIR}
    ${OpenCV_INCLUDE_DIRS}
    ${Protobuf_INCLUDE_DIRS}
    ${NLOHMANN_JSON_INCLUDE}
    /opt/vitis_ai/include          # Vitis AI headers
    /usr/include/vart              # VART headers
    /usr/include/xir
)

target_link_libraries(traffic_edge_app PRIVATE
    ${OpenCV_LIBS}
    Threads::Threads
    ${VART_LIB}
    ${XIR_LIB}
    ${TARGET_LIB}
    ${MOSQUITTO_LIB}
    ${Protobuf_LIBRARIES}
    gRPC::grpc++
    gRPC::grpc++_reflection
    atomic       # std::atomic 需要在某些平台显式链接
)

target_compile_options(traffic_edge_app PRIVATE
    -O2 -march=armv8-a -mtune=cortex-a53
    -Wall -Wextra -Wno-unused-parameter
)

# 调试版本开启地址清理
if(CMAKE_BUILD_TYPE STREQUAL "Debug")
    target_compile_options(traffic_edge_app PRIVATE -fsanitize=address -g)
    target_link_options(traffic_edge_app PRIVATE -fsanitize=address)
endif()

# ── 安装 ─────────────────────────────────────────────────────
install(TARGETS traffic_edge_app DESTINATION /usr/bin)
install(DIRECTORY ${CMAKE_SOURCE_DIR}/../../ai/deploy/compiled_models/
        DESTINATION /opt/models)
install(FILES ${CMAKE_SOURCE_DIR}/config/config.toml.example
        DESTINATION /etc/traffic_edge
        RENAME config.toml)

# ── 单元测试 ─────────────────────────────────────────────────
enable_testing()
find_package(GTest QUIET)
if(GTest_FOUND)
    add_subdirectory(tests)
endif()

message(STATUS "Build type: ${CMAKE_BUILD_TYPE}")
message(STATUS "OpenCV: ${OpenCV_VERSION}")
message(STATUS "Install prefix: ${CMAKE_INSTALL_PREFIX}")
