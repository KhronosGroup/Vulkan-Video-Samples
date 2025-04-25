/*
* Copyright (C) 2025 Igalia, S.L.
*
* Licensed under the Apache License, Version 2.0 (the "License");
* you may not use this file except in compliance with the License.
* You may obtain a copy of the License at
*
*    http://www.apache.org/licenses/LICENSE-2.0
*
* Unless required by applicable law or agreed to in writing, software
* distributed under the License is distributed on an "AS IS" BASIS,
* WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
* See the License for the specific language governing permissions and
* limitations under the License.
*/
#ifndef _LOGGER_H_
#define _LOGGER_H_

#include <iostream>
#include <fstream>
#include <string>
#include <stdarg.h>

// Enum for log levels
enum LogLevel {
    LOG_NONE = 0,  // Use this to disable logging
    LOG_ERROR,
    LOG_WARNING,
    LOG_INFO,
    LOG_DEBUG
};

#define LOG_S_DEBUG Logger::instance()(LogLevel::LOG_DEBUG)
#define LOG_S_INFO Logger::instance()(LogLevel::LOG_INFO)
#define LOG_S_WARN Logger::instance()(LogLevel::LOG_WARNING)
#define LOG_S_ERROR Logger::instance()(LogLevel::LOG_ERROR)

#define LOG_CAT_LEVEL(LEVEL, CAT, FMT, ...) Logger::instance().printf(LEVEL, FMT, ##__VA_ARGS__)


#define LOG_DEBUG_CAT(CAT, FMT, ...) LOG_CAT_LEVEL(LogLevel::LOG_DEBUG, CAT, FMT, ##__VA_ARGS__)
#define LOG_INFO_CAT(CAT, FMT, ...) LOG_CAT_LEVEL(LogLevel::LOG_INFO, CAT, FMT, ##__VA_ARGS__)
#define LOG_WARN_CAT(CAT, FMT, ...) LOG_CAT_LEVEL(LogLevel::LOG_WARNING, CAT, FMT, ##__VA_ARGS__)
#define LOG_ERROR_CAT(CAT, FMT, ...) LOG_CAT_LEVEL(LogLevel::LOG_ERROR, CAT, FMT, ##__VA_ARGS__)

#define LOG_DEBUG(FMT, ...) LOG_DEBUG_CAT("", FMT, ##__VA_ARGS__)
#define LOG_INFO(FMT, ...) LOG_INFO_CAT("", FMT, ##__VA_ARGS__)
#define LOG_WARN( FMT,...) LOG_WARN_CAT("", FMT, ##__VA_ARGS__)
#define LOG_ERROR( FMT,...) LOG_DEBUG_CAT("", FMT, ##__VA_ARGS__)

#define LOG_DEBUG_CONFIG( FMT, ...) LOG_DEBUG_CAT("config:\t", FMT,##__VA_ARGS__)
#define LOG_INFO_CONFIG( FMT,...) LOG_INFO_CAT("config:\t", FMT,##__VA_ARGS__)
#define LOG_WARN_CONFIG( FMT,...) LOG_WARN_CAT("config:\t", FMT,##__VA_ARGS__)
#define LOG_ERROR_CONFIG( FMT,...) LOG_DEBUG_CAT("config:\t", FMT,##__VA_ARGS__)

class Logger {
private:
    std::ostream& os;      // The output stream (e.g., std::cout or std::ofstream)
    std::ostream& err;      // The error stream (e.g., std::cerr)
    LogLevel currentLevel; // Current log level
    LogLevel messageLevel; // The log level for the current message

public:
    static Logger &instance ()
    {
      static Logger instance;
      return instance;
    }
    // Constructor to set the output stream and log level (default is INFO)
    Logger(std::ostream& outStream = std::cout, std::ostream& errStream = std::cerr, LogLevel level = LogLevel::LOG_INFO)
        : os(outStream), err(errStream), currentLevel(level), messageLevel(LogLevel::LOG_INFO) {}

    // Set the log level for the logger
    void setLogLevel(int level) {
        if (level > LOG_DEBUG)
            level = LOG_DEBUG;
        currentLevel = static_cast<LogLevel>(level);
    }

    // Set the log level for the current message
    Logger& operator()(LogLevel level) {
        messageLevel = level;
        return *this;
    }

    // Overload the << operator for generic types
    template<typename T>
    Logger& operator<<(const T& data) {
        if (messageLevel <= currentLevel) {
            if (messageLevel == LOG_ERROR)
              err << data;
            else
              os << data;
        }
        return *this;
    }

    // Overload for stream manipulators (like std::endl)
    typedef std::ostream& (*StreamManipulator)(std::ostream&);
    Logger& operator<<(StreamManipulator manip) {
        if (messageLevel <= currentLevel) {
            if (messageLevel == LOG_ERROR)
              err << manip;
            else
              os << manip;  // Handle std::endl, std::flush, etc.
        }
        return *this;
    }

    void printf(LogLevel level, const char* format, ...) {
        if (level <= currentLevel) {
            va_list args;
            va_start(args, format);
            if (level == LOG_ERROR)
              vfprintf(stderr, format, args);
            else
              vfprintf(stdout,format, args);
            va_end(args);
        }
    }
};


#endif
