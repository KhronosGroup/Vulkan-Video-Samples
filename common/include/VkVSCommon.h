#ifndef VKVS_COMMON_H
#define VKVS_COMMON_H

// Common definitions for Vulkan Video Samples

#ifdef __cplusplus
extern "C" {
#endif

// Version information
#define VKVS_VERSION_MAJOR 0
#define VKVS_VERSION_MINOR 3
#define VKVS_VERSION_PATCH 5

#define _STR(x) #x
#define _VERSION_STRING(major,minor,patch) _STR(major) "." _STR(minor) "." _STR(patch)

#define VKVS_VERSION_STRING \
    _VERSION_STRING(VKVS_VERSION_MAJOR,VKVS_VERSION_MINOR,VKVS_VERSION_PATCH)

// Include stdlib.h for standard exit codes
#include <stdlib.h>

// Standard exit codes for Vulkan Video applications
// Use EXIT_SUCCESS and EXIT_FAILURE from stdlib.h
// Exit code 77 is commonly used to indicate "skipped" or "not supported" in test frameworks
// Avoiding code 3 which Windows uses for asserts
#define VVS_EXIT_CUSTOM_NOT_SUPPORTED  77

#ifdef __cplusplus
}
#endif

#endif // VKVS_COMMON_H