v0.3.2:
  - Prepare VVS to be able to build inside CTS using the custom vulkan headers
  - Use the version tag for vulkan headers instead of main
  - Fix various warnings such as signed/unsigned comparison etc.

v0.3.1:
  - Common: better detection of vulkan SDK, new CMake macro for vulkan headers detection

v0.3.0:
  - Encoder: add intra refresh support
  - Encoder: fix mesa driver support with preferredGopFrameCount equal to 0
  - Parser: add support for aarch64 cross compilation
  - Common: fix win32 build
  - Common: various bug fixes in both decoder and encoder

v0.2.0:
 - Add VP9 support in decoder.
 - Support of separate transfer queue in encoder.
 - Various fixes in decoder.
 - Various fixes in encoder.

v0.1.0:
 - First revision, see [README.md](README.md) for features.