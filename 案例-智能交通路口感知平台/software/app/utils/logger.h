#pragma once
#include <string>
#include <cstdio>
#include <ctime>
#include <mutex>

// 简单日志器（生产环境可替换为 spdlog）
class Logger {
public:
    enum Level { DEBUG=0, INFO=1, WARN=2, ERROR=3 };

    static void init(const std::string& level_str, const std::string& log_file);
    static void log(Level lv, const char* file, int line, const char* fmt, ...);

    static Level current_level;
    static FILE*  log_fp;
    static std::mutex mtx;
};

// 带文件名/行号的宏
#define LOG_DEBUG(...) Logger::log(Logger::DEBUG, __FILE__, __LINE__, __VA_ARGS__)
#define LOG_INFO(...)  Logger::log(Logger::INFO,  __FILE__, __LINE__, __VA_ARGS__)
#define LOG_WARN(...)  Logger::log(Logger::WARN,  __FILE__, __LINE__, __VA_ARGS__)
#define LOG_ERROR(...) Logger::log(Logger::ERROR, __FILE__, __LINE__, __VA_ARGS__)
