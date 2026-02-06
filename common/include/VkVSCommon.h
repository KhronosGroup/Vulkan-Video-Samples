#ifndef VKVS_COMMON_H
#define VKVS_COMMON_H

// Common definitions for Vulkan Video Samples

#ifdef __cplusplus
extern "C" {
#endif

// Version information
#define VKVS_VERSION_MAJOR 0
#define VKVS_VERSION_MINOR 4
#define VKVS_VERSION_PATCH 4

// Helper macros for version string construction (prefixed to avoid reserved identifier issues)
#define VKVS_STRINGIFY(x) #x
#define VKVS_VERSION_STRING_IMPL(major,minor,patch) VKVS_STRINGIFY(major) "." VKVS_STRINGIFY(minor) "." VKVS_STRINGIFY(patch)

#define VKVS_VERSION_STRING \
    VKVS_VERSION_STRING_IMPL(VKVS_VERSION_MAJOR,VKVS_VERSION_MINOR,VKVS_VERSION_PATCH)

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
} // extern "C"

// C++ only macros and utilities
#include <iostream>
#include "vulkan_interfaces.h"
#include <string>

// Macro to check Vulkan features and return error if not supported
// Note: This macro contains a return statement - use with care
#define CHECK_VULKAN_FEATURE(feature, name, optional) \
    do { \
        if (!(feature)) { \
            std::cerr << ((optional) ? "WARNING: " : "ERROR: ") << (name) << " feature not supported" << std::endl; \
            if (!(optional)) { \
                return VK_ERROR_FEATURE_NOT_PRESENT; \
            } \
        } \
    } while(0)

// Stringification macros (prefixed to avoid collisions with common macro names)
#ifndef VKVS_CASE_STR
#define VKVS_CASE_STR(x) case x: return VKVS_STRINGIFY(x)
#endif

// Helper function to get string representation of VkResult codes
inline const char* string_VkResult(VkResult result) {
    switch (result) {
        VKVS_CASE_STR(VK_SUCCESS);
        VKVS_CASE_STR(VK_NOT_READY);
        VKVS_CASE_STR(VK_TIMEOUT);
        VKVS_CASE_STR(VK_EVENT_SET);
        VKVS_CASE_STR(VK_EVENT_RESET);
        VKVS_CASE_STR(VK_INCOMPLETE);
        VKVS_CASE_STR(VK_ERROR_OUT_OF_HOST_MEMORY);
        VKVS_CASE_STR(VK_ERROR_OUT_OF_DEVICE_MEMORY);
        VKVS_CASE_STR(VK_ERROR_INITIALIZATION_FAILED);
        VKVS_CASE_STR(VK_ERROR_DEVICE_LOST);
        VKVS_CASE_STR(VK_ERROR_MEMORY_MAP_FAILED);
        VKVS_CASE_STR(VK_ERROR_LAYER_NOT_PRESENT);
        VKVS_CASE_STR(VK_ERROR_EXTENSION_NOT_PRESENT);
        VKVS_CASE_STR(VK_ERROR_FEATURE_NOT_PRESENT);
        VKVS_CASE_STR(VK_ERROR_INCOMPATIBLE_DRIVER);
        VKVS_CASE_STR(VK_ERROR_TOO_MANY_OBJECTS);
        VKVS_CASE_STR(VK_ERROR_FORMAT_NOT_SUPPORTED);
        VKVS_CASE_STR(VK_ERROR_FRAGMENTED_POOL);
        VKVS_CASE_STR(VK_ERROR_OUT_OF_POOL_MEMORY);
        VKVS_CASE_STR(VK_ERROR_INVALID_EXTERNAL_HANDLE);
        VKVS_CASE_STR(VK_ERROR_FRAGMENTATION);
        VKVS_CASE_STR(VK_ERROR_INVALID_OPAQUE_CAPTURE_ADDRESS);
        VKVS_CASE_STR(VK_ERROR_SURFACE_LOST_KHR);
        VKVS_CASE_STR(VK_ERROR_NATIVE_WINDOW_IN_USE_KHR);
        VKVS_CASE_STR(VK_SUBOPTIMAL_KHR);
        VKVS_CASE_STR(VK_ERROR_OUT_OF_DATE_KHR);
        VKVS_CASE_STR(VK_ERROR_INCOMPATIBLE_DISPLAY_KHR);
        VKVS_CASE_STR(VK_ERROR_VALIDATION_FAILED_EXT);
        VKVS_CASE_STR(VK_ERROR_INVALID_SHADER_NV);
        VKVS_CASE_STR(VK_ERROR_INVALID_DRM_FORMAT_MODIFIER_PLANE_LAYOUT_EXT);
        VKVS_CASE_STR(VK_ERROR_NOT_PERMITTED_EXT);
        VKVS_CASE_STR(VK_ERROR_FULL_SCREEN_EXCLUSIVE_MODE_LOST_EXT);
        VKVS_CASE_STR(VK_ERROR_UNKNOWN);
        default:
            return "VK_RESULT_UNKNOWN";
    }
}
inline const char* string_VkResult_Extended(VkResult result) {
    // First try video-specific error codes
    switch (result) {
        VKVS_CASE_STR(VK_ERROR_VIDEO_PROFILE_OPERATION_NOT_SUPPORTED_KHR);
        VKVS_CASE_STR(VK_ERROR_VIDEO_PROFILE_FORMAT_NOT_SUPPORTED_KHR);
        VKVS_CASE_STR(VK_ERROR_VIDEO_PROFILE_CODEC_NOT_SUPPORTED_KHR);
        VKVS_CASE_STR(VK_ERROR_VIDEO_STD_VERSION_NOT_SUPPORTED_KHR);
        default:
            // Fall back to generated string_VkResult()
            return string_VkResult(result);
    }
}

// Helper function to check if a VkResult indicates video profile/feature not supported
// Returns true for video-specific KHR errors (profile, format, codec, std version)
// and general Vulkan capability errors (format, feature, driver, extension)
inline bool IsVideoUnsupportedResult(VkResult result) {
    return result == VK_ERROR_VIDEO_PROFILE_OPERATION_NOT_SUPPORTED_KHR ||
           result == VK_ERROR_VIDEO_PROFILE_FORMAT_NOT_SUPPORTED_KHR ||
           result == VK_ERROR_VIDEO_PROFILE_CODEC_NOT_SUPPORTED_KHR ||
           result == VK_ERROR_VIDEO_STD_VERSION_NOT_SUPPORTED_KHR ||
           result == VK_ERROR_FORMAT_NOT_SUPPORTED ||
           result == VK_ERROR_FEATURE_NOT_PRESENT ||
           result == VK_ERROR_INCOMPATIBLE_DRIVER ||
           result == VK_ERROR_EXTENSION_NOT_PRESENT;
}

inline int ExitCodeFromVkResult(VkResult result) {
    if (IsVideoUnsupportedResult(result)) {
        return VVS_EXIT_UNSUPPORTED;
    }
    return (result == VK_SUCCESS) ? EXIT_SUCCESS : EXIT_FAILURE;
}

#endif // __cplusplus

#endif // VKVS_COMMON_H
