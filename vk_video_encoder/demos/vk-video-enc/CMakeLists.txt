set(sources
    Main.cpp
    ${VK_VIDEO_ENCODER_LIBS_SOURCE_ROOT}/VkVideoEncoder/VkEncoderConfigH264.cpp
    ${VK_VIDEO_ENCODER_LIBS_SOURCE_ROOT}/VkVideoEncoder/VkEncoderConfigH264.h
    ${VK_VIDEO_ENCODER_LIBS_SOURCE_ROOT}/VkVideoEncoder/VkEncoderDpbH264.cpp
    ${VK_VIDEO_ENCODER_LIBS_SOURCE_ROOT}/VkVideoEncoder/VkEncoderDpbH264.h
    ${VK_VIDEO_ENCODER_LIBS_SOURCE_ROOT}/VkVideoEncoder/VkVideoEncoderH264.cpp
    ${VK_VIDEO_ENCODER_LIBS_SOURCE_ROOT}/VkVideoEncoder/VkVideoEncoderH264.h
    ${VK_VIDEO_ENCODER_LIBS_SOURCE_ROOT}/VkVideoEncoder/VkEncoderConfigH265.cpp
    ${VK_VIDEO_ENCODER_LIBS_SOURCE_ROOT}/VkVideoEncoder/VkEncoderConfigH265.h
    ${VK_VIDEO_ENCODER_LIBS_SOURCE_ROOT}/VkVideoEncoder/VkEncoderDpbH265.cpp
    ${VK_VIDEO_ENCODER_LIBS_SOURCE_ROOT}/VkVideoEncoder/VkEncoderDpbH265.h
    ${VK_VIDEO_ENCODER_LIBS_SOURCE_ROOT}/VkVideoEncoder/VkVideoEncoderH265.cpp
    ${VK_VIDEO_ENCODER_LIBS_SOURCE_ROOT}/VkVideoEncoder/VkVideoEncoderH265.h
    ${VK_VIDEO_ENCODER_LIBS_SOURCE_ROOT}/VkVideoEncoder/VkEncoderConfigAV1.cpp
    ${VK_VIDEO_ENCODER_LIBS_SOURCE_ROOT}/VkVideoEncoder/VkEncoderConfigAV1.h
    ${VK_VIDEO_ENCODER_LIBS_SOURCE_ROOT}/VkVideoEncoder/VkEncoderDpbAV1.cpp
    ${VK_VIDEO_ENCODER_LIBS_SOURCE_ROOT}/VkVideoEncoder/VkEncoderDpbAV1.h
    ${VK_VIDEO_ENCODER_LIBS_SOURCE_ROOT}/VkVideoEncoder/VkVideoEncoderAV1.cpp
    ${VK_VIDEO_ENCODER_LIBS_SOURCE_ROOT}/VkVideoEncoder/VkVideoEncoderAV1.h
    ${VK_VIDEO_ENCODER_LIBS_SOURCE_ROOT}/VkVideoEncoder/VkEncoderConfig.cpp
    ${VK_VIDEO_ENCODER_LIBS_SOURCE_ROOT}/VkVideoEncoder/VkVideoEncoder.cpp
    ${VK_VIDEO_ENCODER_LIBS_SOURCE_ROOT}/VkVideoEncoder/VkVideoGopStructure.cpp
    ${VK_VIDEO_ENCODER_LIBS_SOURCE_ROOT}/VkVideoEncoder/VkVideoGopStructure.h
    ${VK_VIDEO_ENCODER_LIBS_SOURCE_ROOT}/VkVideoEncoder/VkVideoEncoder.h
    ${VK_VIDEO_COMMON_LIBS_SOURCE_ROOT}/VkCodecUtils/YCbCrConvUtilsCpu.cpp
    ${VK_VIDEO_COMMON_LIBS_SOURCE_ROOT}/VkCodecUtils/YCbCrConvUtilsCpu.h
    ${VK_VIDEO_COMMON_LIBS_SOURCE_ROOT}/VkShell/Shell.cpp
    ${VK_VIDEO_COMMON_LIBS_SOURCE_ROOT}/VkShell/ShellDirect.cpp
    ${VK_VIDEO_COMMON_LIBS_SOURCE_ROOT}/VkShell/Shell.h
    ${VK_VIDEO_COMMON_LIBS_SOURCE_ROOT}/VkCodecUtils/Helpers.h
    ${VK_VIDEO_COMMON_LIBS_SOURCE_ROOT}/VkCodecUtils/HelpersDispatchTable.cpp
    ${VK_VIDEO_COMMON_LIBS_SOURCE_ROOT}/VkCodecUtils/HelpersDispatchTable.h
    ${VK_VIDEO_COMMON_LIBS_SOURCE_ROOT}/VkCodecUtils/VulkanDeviceContext.cpp
    ${VK_VIDEO_COMMON_LIBS_SOURCE_ROOT}/VkCodecUtils/VulkanDeviceContext.h
    ${VK_VIDEO_COMMON_LIBS_SOURCE_ROOT}/VkCodecUtils/VulkanShaderCompiler.cpp
    ${VK_VIDEO_COMMON_LIBS_SOURCE_ROOT}/VkCodecUtils/VulkanShaderCompiler.h
    ${VK_VIDEO_COMMON_LIBS_SOURCE_ROOT}/VkCodecUtils/VulkanDeviceMemoryImpl.h
    ${VK_VIDEO_COMMON_LIBS_SOURCE_ROOT}/VkCodecUtils/VulkanDeviceMemoryImpl.cpp
    ${VK_VIDEO_COMMON_LIBS_SOURCE_ROOT}/VkCodecUtils/VkBufferResource.cpp
    ${VK_VIDEO_COMMON_LIBS_SOURCE_ROOT}/VkCodecUtils/VkBufferResource.h
    ${VK_VIDEO_COMMON_LIBS_SOURCE_ROOT}/VkCodecUtils/VkImageResource.cpp
    ${VK_VIDEO_COMMON_LIBS_SOURCE_ROOT}/VkCodecUtils/VkImageResource.h
    ${VK_VIDEO_COMMON_LIBS_SOURCE_ROOT}/VkCodecUtils/VulkanVideoImagePool.cpp
    ${VK_VIDEO_COMMON_LIBS_SOURCE_ROOT}/VkCodecUtils/VulkanVideoImagePool.h
    ${VK_VIDEO_COMMON_LIBS_SOURCE_ROOT}/VkCodecUtils/VulkanCommandBufferPool.cpp
    ${VK_VIDEO_COMMON_LIBS_SOURCE_ROOT}/VkCodecUtils/VulkanCommandBufferPool.h
    ${VK_VIDEO_COMMON_LIBS_SOURCE_ROOT}/VkCodecUtils/VulkanQueryPoolSet.cpp
    ${VK_VIDEO_COMMON_LIBS_SOURCE_ROOT}/VkCodecUtils/VulkanQueryPoolSet.h
    ${VK_VIDEO_COMMON_LIBS_SOURCE_ROOT}/VkCodecUtils/VulkanDescriptorSetLayout.cpp
    ${VK_VIDEO_COMMON_LIBS_SOURCE_ROOT}/VkCodecUtils/VulkanDescriptorSetLayout.h
    ${VK_VIDEO_COMMON_LIBS_SOURCE_ROOT}/VkCodecUtils/VulkanCommandBuffersSet.cpp
    ${VK_VIDEO_COMMON_LIBS_SOURCE_ROOT}/VkCodecUtils/VulkanCommandBuffersSet.h
    ${VK_VIDEO_COMMON_LIBS_SOURCE_ROOT}/VkCodecUtils/VulkanVideoSession.cpp
    ${VK_VIDEO_COMMON_LIBS_SOURCE_ROOT}/VkCodecUtils/VulkanVideoSession.h
    ${VK_VIDEO_COMMON_LIBS_SOURCE_ROOT}/VkCodecUtils/VulkanVideoSessionParameters.cpp
    ${VK_VIDEO_COMMON_LIBS_SOURCE_ROOT}/VkCodecUtils/VulkanVideoSessionParameters.h
    ${VK_VIDEO_COMMON_LIBS_SOURCE_ROOT}/VkCodecUtils/FrameProcessor.h
    ${VK_VIDEO_COMMON_LIBS_SOURCE_ROOT}/VkCodecUtils/VulkanVideoDisplayQueue.cpp
    ${VK_VIDEO_COMMON_LIBS_SOURCE_ROOT}/VkCodecUtils/VulkanVideoDisplayQueue.h
    ${VK_VIDEO_COMMON_LIBS_SOURCE_ROOT}/VkCodecUtils/VulkanFrame.cpp
    ${VK_VIDEO_COMMON_LIBS_SOURCE_ROOT}/VkCodecUtils/VulkanFrame.h
    ${VK_VIDEO_COMMON_LIBS_SOURCE_ROOT}/VkCodecUtils/pattern.cpp
    ${VK_VIDEO_COMMON_LIBS_SOURCE_ROOT}/VkCodecUtils/pattern.h
    ${VK_VIDEO_COMMON_LIBS_SOURCE_ROOT}/VkCodecUtils/VulkanVideoUtils.cpp
    ${VK_VIDEO_COMMON_LIBS_SOURCE_ROOT}/VkCodecUtils/VulkanVideoUtils.h
    ${VK_VIDEO_COMMON_LIBS_SOURCE_ROOT}/VkCodecUtils/VulkanComputePipeline.cpp
    ${VK_VIDEO_COMMON_LIBS_SOURCE_ROOT}/VkCodecUtils/VulkanComputePipeline.h
    ${VK_VIDEO_COMMON_LIBS_SOURCE_ROOT}/VkCodecUtils/VulkanFilter.cpp
    ${VK_VIDEO_COMMON_LIBS_SOURCE_ROOT}/VkCodecUtils/VulkanFilter.h
    ${VK_VIDEO_COMMON_LIBS_SOURCE_ROOT}/VkCodecUtils/VulkanFilterYuvCompute.cpp
    ${VK_VIDEO_COMMON_LIBS_SOURCE_ROOT}/VkCodecUtils/VulkanFilterYuvCompute.h
    ${VK_VIDEO_COMMON_LIBS_SOURCE_ROOT}/VkCodecUtils/VulkanSamplerYcbcrConversion.cpp
    ${VK_VIDEO_COMMON_LIBS_SOURCE_ROOT}/VkCodecUtils/VulkanSamplerYcbcrConversion.h
    ${VK_VIDEO_COMMON_LIBS_SOURCE_ROOT}/VkCodecUtils/VulkanFenceSet.cpp
    ${VK_VIDEO_COMMON_LIBS_SOURCE_ROOT}/VkCodecUtils/VulkanFenceSet.h
    ${VK_VIDEO_COMMON_LIBS_SOURCE_ROOT}/VkCodecUtils/VulkanSemaphoreSet.cpp
    ${VK_VIDEO_COMMON_LIBS_SOURCE_ROOT}/VkCodecUtils/VulkanSemaphoreSet.h
    ${VK_VIDEO_COMMON_LIBS_SOURCE_ROOT}/VkCodecUtils/VkVideoRefCountBase.h
    ${VK_VIDEO_COMMON_LIBS_SOURCE_ROOT}/VkCodecUtils/nvVkFormats.cpp
    ${VK_VIDEO_COMMON_LIBS_SOURCE_ROOT}/VkCodecUtils/VulkanBistreamBufferImpl.h
    ${VK_VIDEO_COMMON_LIBS_SOURCE_ROOT}/VkCodecUtils/VulkanBistreamBufferImpl.cpp
    ${VK_VIDEO_DECODER_LIBS_SOURCE_ROOT}/VulkanVideoFrameBuffer/VulkanVideoFrameBuffer.h
    ${VK_VIDEO_DECODER_LIBS_SOURCE_ROOT}/VulkanVideoFrameBuffer/VulkanVideoFrameBuffer.cpp
    )


set(definitions
    PRIVATE -DVK_NO_PROTOTYPES
    PRIVATE -DGLM_FORCE_RADIANS
    PRIVATE -DVIDEO_DISPLAY_QUEUE_SUPPORT)

set(includes
    PRIVATE ${VK_VIDEO_ENCODER_LIBS_SOURCE_ROOT}
    PRIVATE ${VK_VIDEO_DECODER_LIBS_SOURCE_ROOT}
    PRIVATE ${VK_VIDEO_COMMON_LIBS_SOURCE_ROOT}
    PRIVATE ${CMAKE_CURRENT_BINARY_DIR})

set(libraries PRIVATE ${CMAKE_THREAD_LIBS_INIT})

link_directories(
    ${VULKAN_VIDEO_DEVICE_LIBS_PATH}
    ${VULKAN_VIDEO_DEC_LIBS_PATH}
    ${VULKAN_VIDEO_PARSER_LIB_PATH}
    ${LIBNVPARSER_BINARY_ROOT}
    )

if(WIN32)
    list(APPEND libraries PRIVATE ${VULKAN_VIDEO_PARSER_LIB} ${SHADERC_SHARED_LIBRARY})
else()
    list(APPEND libraries PRIVATE -lX11)
    list(APPEND libraries PRIVATE ${SHADERC_SHARED_LIBRARY})
    list(APPEND libraries PRIVATE -L${CMAKE_INSTALL_LIBDIR} -l${VULKAN_VIDEO_PARSER_LIB})
    list(APPEND libraries PRIVATE -L${LIBNVPARSER_BINARY_ROOT} -l${VULKAN_VIDEO_PARSER_LIB})
endif()

if(TARGET vulkan)
    list(APPEND definitions PRIVATE -DUNINSTALLED_LOADER="$<TARGET_FILE:vulkan>")
endif()

if(WIN32)
    list(APPEND definitions PRIVATE -DVK_USE_PLATFORM_WIN32_KHR)
    list(APPEND definitions PRIVATE -DWIN32_LEAN_AND_MEAN)

    list(APPEND sources ${VK_VIDEO_COMMON_LIBS_SOURCE_ROOT}/VkShell/ShellWin32.cpp ${VK_VIDEO_COMMON_LIBS_SOURCE_ROOT}/VkShell/ShellWin32.h)
elseif(${CMAKE_SYSTEM_NAME} STREQUAL "Linux")
    list(APPEND libraries PRIVATE -ldl -lrt -lpthread)

    if(BUILD_WSI_XCB_SUPPORT AND DEMOS_WSI_SELECTION STREQUAL "XCB")
        find_package(XCB REQUIRED)

        list(APPEND sources ${VK_VIDEO_COMMON_LIBS_SOURCE_ROOT}/VkShell/ShellXcb.cpp ${VK_VIDEO_COMMON_LIBS_SOURCE_ROOT}/VkShell/ShellXcb.h)
        list(APPEND definitions PRIVATE -DVK_USE_PLATFORM_XCB_KHR)
        list(APPEND includes PRIVATE ${XCB_INCLUDES})
        list(APPEND libraries PRIVATE ${XCB_LIBRARIES})
    elseif(BUILD_WSI_WAYLAND_SUPPORT AND DEMOS_WSI_SELECTION STREQUAL "WAYLAND")
        find_package(Wayland REQUIRED)

        list(APPEND sources ${VK_VIDEO_COMMON_LIBS_SOURCE_ROOT}/VkShell/ShellWayland.cpp ${VK_VIDEO_COMMON_LIBS_SOURCE_ROOT}/VkShell/ShellWayland.h)
        list(APPEND definitions PRIVATE -DVK_USE_PLATFORM_WAYLAND_KHR)
        list(APPEND includes PRIVATE ${WAYLAND_CLIENT_INCLUDE_DIR})
        list(APPEND libraries PRIVATE ${WAYLAND_CLIENT_LIBRARIES})
    endif()
endif()

set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/..)

list(APPEND includes PRIVATE ${VK_VIDEO_DECODER_LIBS_INCLUDE_ROOT})
list(APPEND includes PRIVATE ${VK_VIDEO_COMMON_LIBS_SOURCE_ROOT})
list(APPEND includes PRIVATE ${VULKAN_VIDEO_PARSER_INCLUDE})
list(APPEND includes PRIVATE ${VULKAN_VIDEO_APIS_INCLUDE})
list(APPEND includes PRIVATE ${VULKAN_VIDEO_APIS_INCLUDE}/vulkan)
list(APPEND includes PRIVATE ${VULKAN_VIDEO_APIS_INCLUDE}/nvidia_utils/vulkan)

add_executable(vk-video-enc-test ${sources})
target_compile_definitions(vk-video-enc-test ${definitions})
target_include_directories(vk-video-enc-test ${includes})
target_link_libraries(vk-video-enc-test PUBLIC ${libraries})
add_dependencies(vk-video-enc-test GenerateDispatchTables ${VULKAN_VIDEO_PARSER_LIB} ${SHADERC_LIB})

install(TARGETS vk-video-enc-test RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR})
