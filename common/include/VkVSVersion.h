#ifndef VKVS_VERSION_H
#define VKVS_VERSION_H

#ifdef __cplusplus
extern "C" {
#endif

#define VKVS_VERSION_MAJOR 0
#define VKVS_VERSION_MINOR 3
#define VKVS_VERSION_PATCH 4

#define _STR(x) #x
#define _VERSION_STRING(major,minor,patch) _STR(major) "." _STR(minor) "." _STR(patch)

#define VKVS_VERSION_STRING \
    _VERSION_STRING(VKVS_VERSION_MAJOR,VKVS_VERSION_MINOR,VKVS_VERSION_PATCH)

#ifdef __cplusplus
}
#endif

#endif // VKVS_VERSION_H