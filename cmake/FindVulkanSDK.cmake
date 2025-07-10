MACRO(FIND_VULKAN_HEADERS VK_MINIMUM_MAJOR_VERSION VK_MINIMUM_MINOR_VERSION VK_MINIMUM_PATCH_VERSION)

    set(USE_SYSTEM_VULKAN OFF)
    set(NEED_FETCH_CONTENT OFF)

    # First try to detect system Vulkan SDK without creating targets
    if(WIN32)
        # Try to find Vulkan SDK Bin directory
        if(DEFINED ENV{VULKAN_SDK})
            file(TO_CMAKE_PATH "$ENV{VULKAN_SDK}" VULKAN_SDK_PATH)
            set(VULKAN_HEADERS_INCLUDE_DIR ${VULKAN_SDK_PATH}/Include CACHE PATH "Path to Vulkan SDK include headers directory" FORCE)
            set(USE_SYSTEM_VULKAN ON)
        endif()
    else()
        # Use pkg-config to detect Vulkan without creating CMake targets
        find_package(PkgConfig QUIET)
        if(PKG_CONFIG_FOUND)
            pkg_check_modules(VULKAN_PC QUIET vulkan)
            if(VULKAN_PC_FOUND)
                message(STATUS "Found Vulkan via pkg-config: ${VULKAN_PC_VERSION}")
                # Get include directory from pkg-config
                set(VULKAN_HEADERS_INCLUDE_DIR ${VULKAN_PC_INCLUDEDIR})
                set(VULKAN_LIBRARIES ${VULKAN_PC_LIBRARIES})
                message(STATUS "VULKAN_HEADERS_INCLUDE_DIR: ${VULKAN_HEADERS_INCLUDE_DIR}")
                set(USE_SYSTEM_VULKAN ON)
            endif()
        endif()

        # Fallback: try to find headers manually if pkg-config failed
        if(NOT VULKAN_PC_FOUND)
            find_path(VULKAN_HEADERS_INCLUDE_DIR
                NAMES vulkan/vulkan.h
                PATHS /usr/include /usr/local/include
                DOC "Vulkan Headers include directory"
            )
            if(VULKAN_HEADERS_INCLUDE_DIR)
                message(STATUS "Found Vulkan headers manually: ${VULKAN_HEADERS_INCLUDE_DIR}")
            endif()
        endif()
    endif()

    # Check if we found a suitable version
    if(EXISTS "${VULKAN_HEADERS_INCLUDE_DIR}/vulkan/vulkan_core.h")
        file(STRINGS "${VULKAN_HEADERS_INCLUDE_DIR}/vulkan/vulkan_core.h" VK_HEADER_VERSION_LINE
            REGEX "^#define VK_HEADER_VERSION ")
        file(STRINGS "${VULKAN_HEADERS_INCLUDE_DIR}/vulkan/vulkan_core.h" VK_HEADER_VERSION_COMPLETE_LINE
            REGEX "^#define VK_HEADER_VERSION_COMPLETE ")

        message(STATUS "Vulkan Header Version Line: ${VK_HEADER_VERSION_LINE}")
        message(STATUS "Vulkan Complete Version Line: ${VK_HEADER_VERSION_COMPLETE_LINE}")

        # Extract version number from VK_HEADER_VERSION
        string(REGEX MATCH "([0-9]+)$" _ ${VK_HEADER_VERSION_LINE})
        set(VK_PATCH_VERSION ${CMAKE_MATCH_1})

        # Extract major and minor version
        file(STRINGS "${VULKAN_HEADERS_INCLUDE_DIR}/vulkan/vulkan_core.h" VK_VERSION_1_3_LINE
            REGEX "^#define VK_API_VERSION_1_3")
        if(VK_VERSION_1_3_LINE)
            set(VK_MAJOR_VERSION 1)
            set(VK_MINOR_VERSION 3)
        endif()

        # Compare versions
        message(STATUS "Found Vulkan version: ${VK_MAJOR_VERSION}.${VK_MINOR_VERSION}.${VK_PATCH_VERSION}")
        if(VK_MAJOR_VERSION LESS ${VK_MINIMUM_MAJOR_VERSION} OR VK_MINOR_VERSION LESS ${VK_MINIMUM_MINOR_VERSION} OR VK_PATCH_VERSION LESS ${VK_MINIMUM_PATCH_VERSION})
            message(STATUS "System Vulkan SDK version ${VK_MAJOR_VERSION}.${VK_MINOR_VERSION}.${VK_PATCH_VERSION} is too old, the minimum required version is ${VK_MINIMUM_MAJOR_VERSION}.${VK_MINIMUM_MINOR_VERSION}.${VK_MINIMUM_PATCH_VERSION}. Will fetch and build required version")
            set(NEED_FETCH_CONTENT ON)
        else()
            message(STATUS "Found suitable Vulkan version on the system: ${VK_MAJOR_VERSION}.${VK_MINOR_VERSION}.${VK_PATCH_VERSION}")
            set(USE_SYSTEM_VULKAN ON)
        endif()
    else()
        message(STATUS "Could not find vulkan_core.h. Will fetch and build required version")
        set(NEED_FETCH_CONTENT ON)
    endif()

    # Only download vulkan-headers if system SDK is not found or insufficient
    if(NEED_FETCH_CONTENT)
        message(STATUS "Downloading and using Vulkan Headers from source")
        FetchContent_Declare(
            vulkan-headers
            GIT_REPOSITORY https://github.com/KhronosGroup/Vulkan-Headers.git
            GIT_TAG main
        )
        FetchContent_MakeAvailable(vulkan-headers)

        # Set Vulkan headers path (we are using the downloaded headers)
        set(VULKAN_HEADERS_INCLUDE_DIR ${vulkan-headers_SOURCE_DIR}/include CACHE PATH "Path to Vulkan include headers directory" FORCE)
        message(STATUS "VULKAN_HEADERS_INCLUDE_DIR: ${VULKAN_HEADERS_INCLUDE_DIR}")
    else()
        # System version is good, now call find_package to create targets
        message(STATUS "Using system Vulkan SDK")
    endif()
ENDMACRO(FIND_VULKAN_HEADERS)


MACRO(FIND_VULKAN_SDK minimum_major_version minimum_minor_version minimum_patch_version)

    FIND_VULKAN_HEADERS(${minimum_major_version} ${minimum_minor_version} ${minimum_patch_version})

    if(NOT USE_SYSTEM_VULKAN)
        # Fetch and build our own Vulkan components
        message(STATUS "Building Vulkan loader from source")

        # Set Vulkan Loader options to disable tests
        set(BUILD_TESTS OFF CACHE BOOL "Disable Vulkan-Loader tests" FORCE)

        # Fetch the Vulkan Loader
        FetchContent_Declare(
            vulkan-loader
            GIT_REPOSITORY https://github.com/KhronosGroup/Vulkan-Loader.git
            GIT_TAG main
        )
        FetchContent_MakeAvailable(vulkan-loader)
        set(VULKAN_LOADER_LIBRARY_DIR "${CMAKE_BINARY_DIR}/_deps/vulkan-loader-build/loader")
        link_directories(${VULKAN_LOADER_LIBRARY_DIR})
    endif()
ENDMACRO(FIND_VULKAN_SDK)