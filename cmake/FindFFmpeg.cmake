#
# Find the native FFmpeg includes and libraries.
#
# This module defines:
#   FFMPEG_FOUND                   - True if FFmpeg was found
#   FFMPEG_INCLUDE_DIRS            - FFmpeg include directories
#   FFMPEG_LIBRARIES               - All FFmpeg libraries
#   FFMPEG_LIBAVCODEC_LIBRARY      - avcodec library
#   FFMPEG_LIBAVFORMAT_LIBRARY     - avformat library
#   FFMPEG_LIBAVUTIL_LIBRARY       - avutil library
#   FFMPEG_LIB_DIR                 - Directory containing FFmpeg libraries
#
# Accepts:
#   FFMPEG_ROOT or ENV{FFMPEG_ROOT} - Custom search path
#

# Prioritize explicit FFMPEG_ROOT, otherwise fall back to pkg-config
if(NOT FFMPEG_ROOT)
    set(FFMPEG_ROOT "$ENV{FFMPEG_ROOT}")
endif()

if(NOT FFMPEG_ROOT)
    find_package(PkgConfig QUIET)
    if(PKG_CONFIG_FOUND)
        pkg_check_modules(PC_LIBAVCODEC QUIET libavcodec)
        pkg_check_modules(PC_LIBAVFORMAT QUIET libavformat)
        pkg_check_modules(PC_LIBAVUTIL   QUIET libavutil)
    endif()
endif()

if(PC_LIBAVCODEC_FOUND AND PC_LIBAVFORMAT_FOUND AND PC_LIBAVUTIL_FOUND)
    set(FFMPEG_LIBAVCODEC_INCLUDE_DIR "${PC_LIBAVCODEC_INCLUDEDIR}")
    set(FFMPEG_LIBAVFORMAT_INCLUDE_DIR "${PC_LIBAVFORMAT_INCLUDEDIR}")
    set(FFMPEG_LIBAVUTIL_INCLUDE_DIR   "${PC_LIBAVUTIL_INCLUDEDIR}")
    set(FFMPEG_LIBAVCODEC_LIBRARY "${PC_LIBAVCODEC_LINK_LIBRARIES}")
    set(FFMPEG_LIBAVFORMAT_LIBRARY "${PC_LIBAVFORMAT_LINK_LIBRARIES}")
    set(FFMPEG_LIBAVUTIL_LIBRARY   "${PC_LIBAVUTIL_LINK_LIBRARIES}")
else()
    # Windows FFmpeg paths
    if(WIN32)
        set(FFMPEG_WIN32_PREBUILT_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/vk_video_decoder/bin/libs/ffmpeg")
        if(CMAKE_SYSTEM_PROCESSOR MATCHES "^(aarch64|arm64|ARM64)")
            set(FFMPEG_WIN32_PREBUILT_DIR "${FFMPEG_WIN32_PREBUILT_ROOT}/winarm64")
        elseif(CMAKE_SYSTEM_PROCESSOR MATCHES "^(arm|ARM)")
            set(FFMPEG_WIN32_PREBUILT_DIR "${FFMPEG_WIN32_PREBUILT_ROOT}/winarm")
        else()
            set(FFMPEG_WIN32_PREBUILT_DIR "${FFMPEG_WIN32_PREBUILT_ROOT}/win64")
        endif()
    endif()

    # User specified FFMPEG_ROOT takes precedence
    set(FFMPEG_INCLUDE_HINTS)
    set(FFMPEG_LIB_HINTS)
    if(FFMPEG_ROOT)
        list(APPEND FFMPEG_INCLUDE_HINTS "${FFMPEG_ROOT}/include")
        list(APPEND FFMPEG_LIB_HINTS     "${FFMPEG_ROOT}/lib")
    endif()

    set(FFMPEG_INCLUDE_SEARCH_PATHS
        ${FFMPEG_WIN32_PREBUILT_DIR}/include
        /opt/csw/include       # Blastwave
        /opt/homebrew/include  # Homebrew
        /opt/include
        /opt/local/include     # DarwinPorts
        /sw/include            # Fink
        /usr/freeware/include
        /usr/include
        /usr/local/include
    )

    set(FFMPEG_LIB_SEARCH_PATHS
        ${FFMPEG_WIN32_PREBUILT_DIR}/lib
        /opt/csw/lib       # Blastwave
        /opt/homebrew/lib  # Homebrew
        /opt/lib
        /opt/local/lib     # DarwinPorts
        /sw/lib            # Fink
        /usr/freeware/lib64
        /usr/lib
        /usr/lib/aarch64-linux-gnu
        /usr/lib/x86_64-linux-gnu
        /usr/lib64
        /usr/local/lib
        /usr/local/lib64
    )

    find_path(FFMPEG_LIBAVCODEC_INCLUDE_DIR
        NAMES libavcodec/avcodec.h
        HINTS ${FFMPEG_INCLUDE_HINTS}
        PATHS ${FFMPEG_INCLUDE_SEARCH_PATHS}
        PATH_SUFFIXES ffmpeg
    )

    find_path(FFMPEG_LIBAVFORMAT_INCLUDE_DIR
        NAMES libavformat/avformat.h
        HINTS ${FFMPEG_INCLUDE_HINTS}
        PATHS ${FFMPEG_INCLUDE_SEARCH_PATHS}
        PATH_SUFFIXES ffmpeg
    )

    find_path(FFMPEG_LIBAVUTIL_INCLUDE_DIR
        NAMES libavutil/avutil.h
        HINTS ${FFMPEG_INCLUDE_HINTS}
        PATHS ${FFMPEG_INCLUDE_SEARCH_PATHS}
        PATH_SUFFIXES ffmpeg
    )

    find_library(FFMPEG_LIBAVCODEC_LIBRARY
        NAMES avcodec
        HINTS ${FFMPEG_LIB_HINTS}
        PATHS ${FFMPEG_LIB_SEARCH_PATHS}
    )

    find_library(FFMPEG_LIBAVFORMAT_LIBRARY
        NAMES avformat
        HINTS ${FFMPEG_LIB_HINTS}
        PATHS ${FFMPEG_LIB_SEARCH_PATHS}
    )

    find_library(FFMPEG_LIBAVUTIL_LIBRARY
        NAMES avutil
        HINTS ${FFMPEG_LIB_HINTS}
        PATHS ${FFMPEG_LIB_SEARCH_PATHS}
    )
endif()

include(FindPackageHandleStandardArgs)
find_package_handle_standard_args(FFmpeg
    REQUIRED_VARS
        FFMPEG_LIBAVCODEC_INCLUDE_DIR
        FFMPEG_LIBAVFORMAT_INCLUDE_DIR
        FFMPEG_LIBAVUTIL_INCLUDE_DIR
        FFMPEG_LIBAVCODEC_LIBRARY
        FFMPEG_LIBAVFORMAT_LIBRARY
        FFMPEG_LIBAVUTIL_LIBRARY
)

mark_as_advanced(
    FFMPEG_LIBAVCODEC_INCLUDE_DIR
    FFMPEG_LIBAVFORMAT_INCLUDE_DIR
    FFMPEG_LIBAVUTIL_INCLUDE_DIR
    FFMPEG_LIBAVCODEC_LIBRARY
    FFMPEG_LIBAVFORMAT_LIBRARY
    FFMPEG_LIBAVUTIL_LIBRARY
)

if(FFMPEG_FOUND)
    set(FFMPEG_INCLUDE_DIRS
        ${FFMPEG_LIBAVCODEC_INCLUDE_DIR}
        ${FFMPEG_LIBAVFORMAT_INCLUDE_DIR}
        ${FFMPEG_LIBAVUTIL_INCLUDE_DIR}
    )
    list(REMOVE_DUPLICATES FFMPEG_INCLUDE_DIRS)
    set(FFMPEG_LIBRARIES
        ${FFMPEG_LIBAVCODEC_LIBRARY}
        ${FFMPEG_LIBAVFORMAT_LIBRARY}
        ${FFMPEG_LIBAVUTIL_LIBRARY}
    )
    get_filename_component(FFMPEG_LIB_DIR "${FFMPEG_LIBAVCODEC_LIBRARY}" DIRECTORY)
endif()
