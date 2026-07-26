#
# Find the native FFMPEG includes and library
# This module defines
# FFMPEG_INCLUDE_DIR, where to find avcodec.h, avformat.h ...
# FFMPEG_LIBRARIES, the libraries to link against to use FFMPEG.
# FFMPEG_FOUND, If false, do not try to use FFMPEG.
# FFMPEG_ROOT, if this module use this path to find FFMPEG headers
# and libraries.

if(WIN32 AND DOWNLOAD_FFMPEG)
    set(FFMPEG_BTBN_TAG        "autobuild-2026-03-31-13-11")
    set(FFMPEG_BTBN_REVISION   "n8.1-7-ga3475e2554")
    set(FFMPEG_BTBN_SUFFIX     "8.1")
    set(FFMPEG_WIN64_SHA256    "6093603479c4bf6f14268d399a46f9ce2d050cce0a9f5e4ed81af2ac373e367b")
    set(FFMPEG_WINARM64_SHA256 "055fd2c58a01042e9da66bfa046c8aa3fa7ea69b9d60fa82bfc9a1a96fc694a0")

    if(CMAKE_GENERATOR_PLATFORM MATCHES "^(aarch64|arm64|ARM64)")
        set(FFMPEG_PLATFORM_DIR "winarm64")
        set(FFMPEG_EXPECTED_HASH "${FFMPEG_WINARM64_SHA256}")
    else()
        set(FFMPEG_PLATFORM_DIR "win64")
        set(FFMPEG_EXPECTED_HASH "${FFMPEG_WIN64_SHA256}")
    endif()

    set(FFMPEG_ARCHIVE_NAME "ffmpeg-${FFMPEG_BTBN_REVISION}-${FFMPEG_PLATFORM_DIR}-lgpl-shared-${FFMPEG_BTBN_SUFFIX}")
    set(FFMPEG_DOWNLOAD_URL "https://github.com/BtbN/FFmpeg-Builds/releases/download/${FFMPEG_BTBN_TAG}/${FFMPEG_ARCHIVE_NAME}.zip")
    set(FFMPEG_DEST_DIR "${CMAKE_CURRENT_SOURCE_DIR}/vk_video_decoder/bin/libs/ffmpeg/${FFMPEG_PLATFORM_DIR}")

    file(GLOB FFMPEG_EXISTING_LIBS "${FFMPEG_DEST_DIR}/lib/avcodec*.lib")
    if(FFMPEG_EXISTING_LIBS)
        message(STATUS "FFmpeg libraries already present in ${FFMPEG_DEST_DIR}")
    else()
        message(STATUS "FFmpeg libraries not found in ${FFMPEG_DEST_DIR}")
        message(STATUS "Downloading FFmpeg from ${FFMPEG_DOWNLOAD_URL} ...")

        include(FetchContent)
        FetchContent_Declare(
            ffmpeg_prebuilt
            URL                        "${FFMPEG_DOWNLOAD_URL}"
            URL_HASH                   "SHA256=${FFMPEG_EXPECTED_HASH}"
            TLS_VERIFY                 ON
            DOWNLOAD_EXTRACT_TIMESTAMP FALSE
        )
        FetchContent_MakeAvailable(ffmpeg_prebuilt)

        foreach(SUBDIR bin lib include)
            if(EXISTS "${ffmpeg_prebuilt_SOURCE_DIR}/${SUBDIR}")
                file(COPY "${ffmpeg_prebuilt_SOURCE_DIR}/${SUBDIR}/" DESTINATION "${FFMPEG_DEST_DIR}/${SUBDIR}")
            endif()
        endforeach()

        message(STATUS "FFmpeg libraries installed to ${FFMPEG_DEST_DIR}")
    endif()
endif()

# Macro to find header and lib directories
# example: FFMPEG_FIND(AVFORMAT avformat avformat.h)
MACRO(FFMPEG_FIND varname shortname headername)
    # old version of ffmpeg put header in $prefix/include/[ffmpeg]
    # so try to find header in include directory
    FIND_PATH(FFMPEG_${varname}_INCLUDE_DIRS lib${shortname}/${headername}
        PATHS
        ${FFMPEG_ROOT}/include/lib${shortname}
        $ENV{FFMPEG_DIR}/include/lib${shortname}
        ~/Library/Frameworks/lib${shortname}
        /Library/Frameworks/lib${shortname}
        /usr/local/include/lib${shortname}
        /usr/include/lib${shortname}
        /sw/include/lib${shortname} # Fink
        /opt/local/include/lib${shortname} # DarwinPorts
        /opt/csw/include/lib${shortname} # Blastwave
        /opt/include/lib${shortname}
        /usr/freeware/include/lib${shortname}
        PATH_SUFFIXES ffmpeg
        DOC "Location of FFMPEG Headers"
    )

    FIND_PATH(FFMPEG_${varname}_INCLUDE_DIRS lib${shortname}/${headername}
        PATHS
        ${FFMPEG_ROOT}/include
        $ENV{FFMPEG_DIR}/include
        ~/Library/Frameworks
        /Library/Frameworks
        /usr/local/include
        /usr/include
        /sw/include # Fink
        /opt/local/include # DarwinPorts
        /opt/csw/include # Blastwave
        /opt/include
        /usr/freeware/include
        PATH_SUFFIXES ffmpeg
        DOC "Location of FFMPEG Headers"
    )

    FIND_LIBRARY(FFMPEG_${varname}_LIBRARIES
        NAMES ${shortname}
        PATHS
        ${FFMPEG_ROOT}/lib
        $ENV{FFMPEG_DIR}/lib
        ~/Library/Frameworks
        /Library/Frameworks
        /usr/local/lib
        /usr/local/lib64
        /usr/lib/x86_64-linux-gnu
        /usr/lib
        /usr/lib64
        /sw/lib
        /opt/local/lib
        /opt/csw/lib
        /opt/lib
        /usr/freeware/lib64
        DOC "Location of FFMPEG Libraries"
    )

    IF (FFMPEG_${varname}_LIBRARIES AND FFMPEG_${varname}_INCLUDE_DIRS)
        SET(FFMPEG_${varname}_FOUND 1)
    ENDIF(FFMPEG_${varname}_LIBRARIES AND FFMPEG_${varname}_INCLUDE_DIRS)

ENDMACRO(FFMPEG_FIND)

SET(FFMPEG_ROOT "$ENV{FFMPEG_DIR}" CACHE PATH "Location of FFMPEG")

# find stdint.h
IF(WIN32)

    FIND_PATH(FFMPEG_STDINT_INCLUDE_DIR stdint.h
        PATHS
        ${FFMPEG_ROOT}/include
        $ENV{FFMPEG_DIR}/include
        ~/Library/Frameworks
        /Library/Frameworks
        /usr/local/include
        /usr/include
        /sw/include # Fink
        /opt/local/include # DarwinPorts
        /opt/csw/include # Blastwave
        /opt/include
        /usr/freeware/include
        PATH_SUFFIXES ffmpeg
        DOC "Location of FFMPEG stdint.h Header"
    )

    IF (FFMPEG_STDINT_INCLUDE_DIR)
        SET(STDINT_OK TRUE)
    ENDIF()

ELSE()

    SET(STDINT_OK TRUE)

ENDIF()

FFMPEG_FIND(LIBAVFORMAT avformat avformat.h)
FFMPEG_FIND(LIBAVDEVICE avdevice avdevice.h)
FFMPEG_FIND(LIBAVCODEC  avcodec  avcodec.h)
FFMPEG_FIND(LIBAVUTIL   avutil   avutil.h)
FFMPEG_FIND(LIBSWSCALE  swscale  swscale.h)  # not sure about the header to look for here.
FFMPEG_FIND(LIBX264  x264 x264.h)
FFMPEG_FIND(LIBX265  x265 x265.h)

SET(FFMPEG_FOUND "NO")

# Note we don't check FFMPEG_LIBSWSCALE_FOUND, FFMPEG_LIBAVDEVICE_FOUND,
# and FFMPEG_LIBAVUTIL_FOUND as they are optional.
IF (FFMPEG_LIBAVFORMAT_FOUND AND FFMPEG_LIBAVCODEC_FOUND AND STDINT_OK)

    SET(FFMPEG_FOUND "YES")

    SET(FFMPEG_INCLUDE_DIR ${FFMPEG_LIBAVFORMAT_INCLUDE_DIRS})

    SET(FFMPEG_LIBRARY_DIRS ${FFMPEG_LIBAVFORMAT_LIBRARY_DIRS})

    # Note we don't add FFMPEG_LIBSWSCALE_LIBRARIES here,
    # it will be added if found later.
    SET(FFMPEG_LIBRARIES
        ${FFMPEG_LIBAVFORMAT_LIBRARIES}
        ${FFMPEG_LIBAVDEVICE_LIBRARIES}
        ${FFMPEG_LIBAVCODEC_LIBRARIES}
        ${FFMPEG_LIBAVUTIL_LIBRARIES}
        ${FFMPEG_LIBSWSCALE_LIBRARIES}
        ${FFMPEG_LIBX264_LIBRARIES}
        ${FFMPEG_LIBX265_LIBRARIES})
ENDIF()

# Find FFmpeg components
find_package(PkgConfig QUIET)
if(PKG_CONFIG_FOUND)
    pkg_check_modules(FFMPEG QUIET
        libavcodec
        libavformat
        libavutil
        libswscale
    )
endif()

# Find individual components
find_path(FFMPEG_INCLUDE_DIR
    NAMES libavcodec/avcodec.h libavformat/avformat.h libavutil/avutil.h libswscale/swscale.h
    PATHS
        ${FFMPEG_INCLUDE_DIRS}
        /usr/include
        /usr/local/include
        $ENV{FFMPEG_ROOT}/include
    PATH_SUFFIXES ffmpeg
)

# Find libraries
find_library(AVCODEC_LIBRARY
    NAMES avcodec
    PATHS
        ${FFMPEG_LIBRARY_DIRS}
        /usr/lib
        /usr/local/lib
        $ENV{FFMPEG_ROOT}/lib
)

find_library(AVFORMAT_LIBRARY
    NAMES avformat
    PATHS
        ${FFMPEG_LIBRARY_DIRS}
        /usr/lib
        /usr/local/lib
        $ENV{FFMPEG_ROOT}/lib
)

find_library(AVUTIL_LIBRARY
    NAMES avutil
    PATHS
        ${FFMPEG_LIBRARY_DIRS}
        /usr/lib
        /usr/local/lib
        $ENV{FFMPEG_ROOT}/lib
)

find_library(SWSCALE_LIBRARY
    NAMES swscale
    PATHS
        ${FFMPEG_LIBRARY_DIRS}
        /usr/lib
        /usr/local/lib
        $ENV{FFMPEG_ROOT}/lib
)

# Set FFmpeg libraries
set(FFMPEG_LIBRARIES
    ${AVCODEC_LIBRARY}
    ${AVFORMAT_LIBRARY}
    ${AVUTIL_LIBRARY}
    ${SWSCALE_LIBRARY}
)

# Handle the QUIETLY and REQUIRED arguments
include(FindPackageHandleStandardArgs)
find_package_handle_standard_args(FFmpeg
    REQUIRED_VARS
        FFMPEG_INCLUDE_DIR
        AVCODEC_LIBRARY
        AVFORMAT_LIBRARY
        AVUTIL_LIBRARY
        SWSCALE_LIBRARY
)

# Mark as advanced
mark_as_advanced(
    FFMPEG_INCLUDE_DIR
    AVCODEC_LIBRARY
    AVFORMAT_LIBRARY
    AVUTIL_LIBRARY
    SWSCALE_LIBRARY
)

# Set variables for use in the project
if(FFMPEG_FOUND)
    set(FFMPEG_INCLUDE_DIRS ${FFMPEG_INCLUDE_DIR})
    set(FFMPEG_DEFINITIONS ${FFMPEG_CFLAGS_OTHER})
endif()
