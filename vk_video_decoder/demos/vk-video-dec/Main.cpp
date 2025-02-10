/*
 * Copyright (C) 2016 Google, Inc.
 * Copyright 2020 NVIDIA Corporation.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#include <assert.h>
#include <string>
#include <vector>
#include <cstring>
#include <cstdio>

#include "VkCodecUtils/DecoderConfig.h"
#include "VkCodecUtils/VulkanDeviceContext.h"
#include "VkCodecUtils/VulkanVideoProcessor.h"
#include "VkCodecUtils/VulkanDecoderFrameProcessor.h"
#include "VkShell/Shell.h"

int main(int argc, const char **argv) {

    DecoderConfig decoderConfig(argv[0]);
    decoderConfig.ParseArgs(argc, argv);

    // In the regular application usecase the CRC output variables are allocated here and also output as part of main.
    // In the library case it is up to the caller of the library to allocate the values and initialize them.
    std::vector<uint32_t> crcAllocation;
    crcAllocation.resize(decoderConfig.crcInitValue.size());
    if (crcAllocation.empty() == false) {
        decoderConfig.crcOutput = &crcAllocation[0];
        for (size_t i = 0; i < decoderConfig.crcInitValue.size(); i += 1) {
            crcAllocation[i] = decoderConfig.crcInitValue[i];
        }
    }

    VulkanDeviceContext vkDevCtxt;
    VkResult result = vkDevCtxt.InitVulkanDecoderDevice(decoderConfig.appName.c_str(),
                                                        VK_NULL_HANDLE,
                                                        !decoderConfig.noPresent,
                                                        decoderConfig.directMode,
                                                        decoderConfig.validate,
                                                        decoderConfig.validateVerbose,
                                                        decoderConfig.verbose);

    if (result != VK_SUCCESS) {
        printf("Could not initialize the Vulkan decoder device!\n");
        return -1;
    }

    const int32_t numDecodeQueues = ((decoderConfig.queueId != 0) ||
                                     (decoderConfig.enableHwLoadBalancing != 0)) ?
                                     -1 : // all available HW decoders
                                      1;  // only one HW decoder instance

    VkQueueFlags requestVideoDecodeQueueMask = VK_QUEUE_VIDEO_DECODE_BIT_KHR;

    VkQueueFlags requestVideoEncodeQueueMask = 0;
    if (decoderConfig.enableVideoEncoder) {
        requestVideoEncodeQueueMask |= VK_QUEUE_VIDEO_ENCODE_BIT_KHR;
    }

    if (decoderConfig.selectVideoWithComputeQueue) {
        requestVideoDecodeQueueMask |= VK_QUEUE_COMPUTE_BIT;
        if (decoderConfig.enableVideoEncoder) {
            requestVideoEncodeQueueMask |= VK_QUEUE_COMPUTE_BIT;
        }
    }

    VkQueueFlags requestVideoComputeQueueMask = 0;
    if (decoderConfig.enablePostProcessFilter != -1) {
        requestVideoComputeQueueMask = VK_QUEUE_COMPUTE_BIT;
    }

    VkVideoCodecOperationFlagsKHR videoDecodeCodecs = (VK_VIDEO_CODEC_OPERATION_DECODE_H264_BIT_KHR  |
                                                       VK_VIDEO_CODEC_OPERATION_DECODE_H265_BIT_KHR  |
                                                       VK_VIDEO_CODEC_OPERATION_DECODE_AV1_BIT_KHR);

    VkVideoCodecOperationFlagsKHR videoEncodeCodecs = ( VK_VIDEO_CODEC_OPERATION_ENCODE_H264_BIT_KHR  |
                                                        VK_VIDEO_CODEC_OPERATION_ENCODE_H265_BIT_KHR  |
                                                        VK_VIDEO_CODEC_OPERATION_ENCODE_AV1_BIT_KHR);

    VkVideoCodecOperationFlagsKHR videoCodecs = videoDecodeCodecs |
                                        (decoderConfig.enableVideoEncoder ? videoEncodeCodecs : (VkVideoCodecOperationFlagsKHR) VK_VIDEO_CODEC_OPERATION_NONE_KHR);

    if (!decoderConfig.noPresent) {

        VkSharedBaseObj<Shell> displayShell;
        const Shell::Configuration configuration(decoderConfig.appName.c_str(),
                                                 decoderConfig.backBufferCount,
                                                 decoderConfig.directMode);

        result = Shell::Create(&vkDevCtxt, configuration, displayShell);
        if (result != VK_SUCCESS) {
            assert(!"Can't allocate display shell! Out of memory!");
            return -1;
        }

        result = vkDevCtxt.InitPhysicalDevice(decoderConfig.deviceId, decoderConfig.GetDeviceUUID(),
                                              (VK_QUEUE_GRAPHICS_BIT | VK_QUEUE_TRANSFER_BIT |
                                              requestVideoComputeQueueMask |
                                              requestVideoDecodeQueueMask |
                                              requestVideoEncodeQueueMask),
                                              displayShell,
                                              requestVideoDecodeQueueMask,
                                              (VK_VIDEO_CODEC_OPERATION_DECODE_H264_BIT_KHR |
                                               VK_VIDEO_CODEC_OPERATION_DECODE_H265_BIT_KHR |
                                               VK_VIDEO_CODEC_OPERATION_DECODE_AV1_BIT_KHR),
                                              requestVideoEncodeQueueMask,
                                              (VK_VIDEO_CODEC_OPERATION_ENCODE_H264_BIT_KHR |
                                               VK_VIDEO_CODEC_OPERATION_ENCODE_H265_BIT_KHR |
                                               VK_VIDEO_CODEC_OPERATION_ENCODE_AV1_BIT_KHR));
        if (result != VK_SUCCESS) {

            assert(!"Can't initialize the Vulkan physical device!");
            return -1;
        }
        assert(displayShell->PhysDeviceCanPresent(vkDevCtxt.getPhysicalDevice(),
                                                  vkDevCtxt.GetPresentQueueFamilyIdx()));

        vkDevCtxt.CreateVulkanDevice(numDecodeQueues,
                                     decoderConfig.enableVideoEncoder ? 1 : 0, // num encode queues
                                     videoCodecs,
                                     false, //  createTransferQueue
                                     true,  // createGraphicsQueue
                                     true,  // createDisplayQueue
                                     requestVideoComputeQueueMask != 0  // createComputeQueue
                                     );

        VkSharedBaseObj<VideoStreamDemuxer> videoStreamDemuxer;
        result = VideoStreamDemuxer::Create(decoderConfig.videoFileName.c_str(),
                                            decoderConfig.forceParserType,
                                            (decoderConfig.enableStreamDemuxing == 1),
                                            decoderConfig.initialWidth,
                                            decoderConfig.initialHeight,
                                            decoderConfig.initialBitdepth,
                                            videoStreamDemuxer);

        if (result != VK_SUCCESS) {

            assert(!"Can't initialize the VideoStreamDemuxer!");
            return result;
        }

        VkSharedBaseObj<VulkanVideoProcessor> vulkanVideoProcessor;
        result = VulkanVideoProcessor::Create(decoderConfig, &vkDevCtxt, vulkanVideoProcessor);
        if (result != VK_SUCCESS) {
            return -1;
        }
        vulkanVideoProcessor->Initialize(&vkDevCtxt, videoStreamDemuxer, decoderConfig);

        VkSharedBaseObj<VkVideoQueue<VulkanDecodedFrame>> videoQueue(vulkanVideoProcessor);
        DecoderFrameProcessorState frameProcessor(&vkDevCtxt, videoQueue, 0);

        displayShell->AttachFrameProcessor(frameProcessor);

        displayShell->RunLoop();

    } else {

        result = vkDevCtxt.InitPhysicalDevice(decoderConfig.deviceId, decoderConfig.GetDeviceUUID(),
                                              (VK_QUEUE_TRANSFER_BIT        |
                                               requestVideoDecodeQueueMask  |
                                               requestVideoComputeQueueMask |
                                               requestVideoEncodeQueueMask),
                                              nullptr,
                                              requestVideoDecodeQueueMask);
        if (result != VK_SUCCESS) {

            assert(!"Can't initialize the Vulkan physical device!");
            return -1;
        }


        result = vkDevCtxt.CreateVulkanDevice(numDecodeQueues,
                                              0,     // num encode queues
                                              videoCodecs,
                                              // If no graphics or compute queue is requested, only video queues
                                              // will be created. Not all implementations support transfer on video queues,
                                              // so request a separate transfer queue for such implementations.
                                              ((vkDevCtxt.GetVideoDecodeQueueFlag() & VK_QUEUE_TRANSFER_BIT) == 0), //  createTransferQueue
                                              false, // createGraphicsQueue
                                              false, // createDisplayQueue
                                              requestVideoComputeQueueMask != 0   // createComputeQueue
                                              );
        if (result != VK_SUCCESS) {

            assert(!"Failed to create Vulkan device!");
            return -1;
        }

        VkSharedBaseObj<VideoStreamDemuxer> videoStreamDemuxer;
        result = VideoStreamDemuxer::Create(decoderConfig.videoFileName.c_str(),
                                            decoderConfig.forceParserType,
                                            (decoderConfig.enableStreamDemuxing == 1),
                                            decoderConfig.initialWidth,
                                            decoderConfig.initialHeight,
                                            decoderConfig.initialBitdepth,
                                            videoStreamDemuxer);

        if (result != VK_SUCCESS) {

            assert(!"Can't initialize the VideoStreamDemuxer!");
            return result;
        }

        VkSharedBaseObj<VulkanVideoProcessor> vulkanVideoProcessor;
        result = VulkanVideoProcessor::Create(decoderConfig, &vkDevCtxt, vulkanVideoProcessor);
        if (result != VK_SUCCESS) {
            std::cerr << "Error creating the decoder instance: " << result << std::endl;
            return -1;
        }
        vulkanVideoProcessor->Initialize(&vkDevCtxt, videoStreamDemuxer, decoderConfig);

        VkSharedBaseObj<VkVideoQueue<VulkanDecodedFrame>> videoQueue(vulkanVideoProcessor);
        DecoderFrameProcessorState frameProcessor(&vkDevCtxt, videoQueue, decoderConfig.decoderQueueSize);

        bool continueLoop = true;
        do {
            continueLoop = frameProcessor->OnFrame(0);
        } while (continueLoop);
    }

    if (decoderConfig.outputcrc != 0) {
        fprintf(decoderConfig.crcOutputFile, "CRC: ");
        for (size_t i = 0; i < decoderConfig.crcInitValue.size(); i += 1) {
            fprintf(decoderConfig.crcOutputFile, "0x%08X ", crcAllocation[i]);
        }

        fprintf(decoderConfig.crcOutputFile, "\n");
        if (decoderConfig.crcOutputFile != stdout) {
            fclose(decoderConfig.crcOutputFile);
            decoderConfig.crcOutputFile = stdout;
        }
    }

    return 0;
}
