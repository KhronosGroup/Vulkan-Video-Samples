#ifndef VVS_VERSION_H
#define VVS_VERSION_H

#ifdef __cplusplus
extern "C" {
#endif

#define VVS_VERSION_MAJOR 0
#define VVS_VERSION_MINOR 1
#define VVS_VERSION_PATCH 0

#define STRINGIFY_HELPER(x) #x
#define STRINGIFY(x) STRINGIFY_HELPER(x)

#define VVS_VERSION_STRING \
    STRINGIFY(VVS_VERSION_MAJOR) "." STRINGIFY(VVS_VERSION_MINOR) "." STRINGIFY(VVS_VERSION_PATCH)

#ifdef __cplusplus
}
#endif

#endif // VVS_VERSION_H