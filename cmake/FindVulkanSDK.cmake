MACRO(FIND_VULKAN_SDK minimum_major_version minimum_minor_version minimum_patch_version)
    # Download and make the Vulkan Headers first before find_package because otherwise
    # it will fait with:
    # add_library cannot create ALIAS target "Vulkan::Headers" because another
    # target with the same name already exists.
    message(STATUS "Downloading Vulkan Headers")
    FetchContent_Declare(
        vulkan-headers
        GIT_REPOSITORY https://github.com/KhronosGroup/Vulkan-Headers.git
        GIT_TAG main
    )
    FetchContent_MakeAvailable(vulkan-headers)

    set (VK_MINIMUM_MAJOR_VERSION ${minimum_major_version})
    set (VK_MINIMUM_MINOR_VERSION ${minimum_minor_version})
    set (VK_MINIMUM_PATCH_VERSION ${minimum_patch_version})

    # Find Vulkan SDK
    if(WIN32)
        # Try to find Vulkan SDK Bin directory
        if(DEFINED ENV{VULKAN_SDK})
            file(TO_CMAKE_PATH "$ENV{VULKAN_SDK}" VULKAN_SDK_PATH)
            set(VULKAN_HEADERS_INCLUDE_DIR ${VULKAN_SDK_PATH}/Include CACHE PATH "Path to Vulkan SDK include headers directory" FORCE)
        endif()
    else()
        find_package(Vulkan QUIET)

        if(Vulkan_FOUND)
            # Set Vulkan headers path (we are using the local headers)
            set(VULKAN_HEADERS_INCLUDE_DIR ${Vulkan_INCLUDE_DIR})

            # Additional Vulkan-related variables
            set(VULKAN_LIBRARIES ${Vulkan_LIBRARIES})

            message(STATUS "VULKAN_HEADERS_INCLUDE_DIR: ${VULKAN_HEADERS_INCLUDE_DIR}")
        else()
            message(STATUS "Vulkan SDK not found. Will fetch and build required version.")
        endif()
    endif()

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
            set(USE_SYSTEM_VULKAN OFF)
        else()
            message(STATUS "Found suitable Vulkan version on the system: ${VK_MAJOR_VERSION}.${VK_MINOR_VERSION}.${VK_PATCH_VERSION}")
            set(USE_SYSTEM_VULKAN ON)
        endif()
    else()
        message(STATUS "Could not find vulkan_core.h in ${VULKAN_HEADERS_INCLUDE_DIR}. Will fetch and build required version")
        set(USE_SYSTEM_VULKAN OFF)
    endif()

    # Optional: Find other dependencies like SPIRV-Tools if needed

    if(USE_SYSTEM_VULKAN)
        # Use system Vulkan
        message(STATUS "Using system Vulkan SDK")
        get_filename_component(VULKAN_LIB_DIR "${Vulkan_LIBRARIES}" DIRECTORY)
    else()
        # Fetch the latest Vulkan headers
        message(STATUS "Building Vulkan components from source")

        set(Vulkan_INCLUDE_DIR ${vulkan-headers_SOURCE_DIR}/include CACHE PATH "Path to Vulkan include headers directory" FORCE)
        set(VULKAN_HEADERS_INCLUDE_DIR ${vulkan-headers_SOURCE_DIR}/include CACHE PATH "Path to Vulkan local include headers directory" FORCE)
        # Fetch and build our own Vulkan components
        message(STATUS "VULKAN_HEADERS_INCLUDE_DIR: ${VULKAN_HEADERS_INCLUDE_DIR}")

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