#ifndef VKVS_COMMON_H
#define VKVS_COMMON_H

// Common definitions for Vulkan Video Samples

#ifdef __cplusplus
extern "C" {
#endif

// Version information
#define VKVS_VERSION_MAJOR 0
#define VKVS_VERSION_MINOR 3
#define VKVS_VERSION_PATCH 9

#define _STR(x) #x
#define _VERSION_STRING(major,minor,patch) _STR(major) "." _STR(minor) "." _STR(patch)

#define VVS_VERSION_STRING \
    _VERSION_STRING(VKVS_VERSION_MAJOR,VKVS_VERSION_MINOR,VKVS_VERSION_PATCH)

// Include stdlib.h for standard exit codes
#include <stdlib.h>

// Include sysexits.h for extended exit codes (POSIX systems)
// On Windows, define the exit codes manually as sysexits.h is not available
#ifndef _WIN32
#include <sysexits.h>
#else
// Define EX_UNAVAILABLE for Windows (service unavailable)
#define EX_UNAVAILABLE 69
#endif

// Standard exit codes for Vulkan Video applications
// Use EXIT_SUCCESS and EXIT_FAILURE from stdlib.h
// EX_UNAVAILABLE (69) indicates a required service is unavailable
// This is used when video codec features are not supported by hardware/driver
#define VVS_EXIT_UNSUPPORTED  EX_UNAVAILABLE

#ifdef __cplusplus
}
#endif

#endif // VKVS_COMMON_H
