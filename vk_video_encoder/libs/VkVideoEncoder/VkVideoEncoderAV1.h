/*
 * Copyright 2022 NVIDIA Corporation.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#ifndef _VKVIDEOENCODER_VKVIDEOENCODERAV1_H_
#define _VKVIDEOENCODER_VKVIDEOENCODERAV1_H_

#include <cstdio>
#include <set>
#include <string>
#include <vector>
#include "VkVideoEncoder/VkVideoEncoder.h"
#include "VkVideoEncoder/VkVideoEncoderStateAV1.h"
#include "VkVideoEncoder/VkEncoderConfigAV1.h"

class VkVideoEncoderAV1 : public VkVideoEncoder
{

public:
    struct VkVideoEncodeFrameInfoAV1 : public VkVideoEncodeFrameInfo {

        VkVideoEncodeAV1PictureInfoKHR pictureInfo;
        StdVideoEncodeAV1PictureInfo stdPictureInfo;
        StdVideoAV1TileInfo stdTileInfo;
        uint16_t heightInSbsMinus1[STD_VIDEO_AV1_MAX_TILE_ROWS];
        uint16_t widthInSbsMinus1[STD_VIDEO_AV1_MAX_TILE_COLS];
        StdVideoAV1Quantization stdQuantInfo;
        StdVideoAV1CDEF stdCdefInfo;
        StdVideoAV1LoopFilter stdLfInfo;
        StdVideoAV1LoopRestoration stdLrInfo;
        bool bShowExistingFrame;
        int32_t frameToShowBufId;
        bool bIsKeyFrame;
        bool bShownKeyFrameOrSwitch;
        bool bOverlayFrame;
        bool bIsReference;
        StdVideoEncodeAV1ReferenceInfo stdReferenceInfo[STD_VIDEO_AV1_REFS_PER_FRAME];
        VkVideoEncodeAV1DpbSlotInfoKHR dpbSlotInfo[STD_VIDEO_AV1_REFS_PER_FRAME];
        VkVideoEncodeAV1RateControlInfoKHR rateControlInfoAV1;
        VkVideoEncodeAV1RateControlLayerInfoKHR rateControlLayersInfoAV1[1];

        VkVideoCodecOperationFlagBitsKHR GetCodecType() const override {
            return VK_VIDEO_CODEC_OPERATION_ENCODE_AV1_BIT_KHR;
        }

        VkVideoEncodeFrameInfoAV1()
            : VkVideoEncodeFrameInfo()
            , pictureInfo{ VK_STRUCTURE_TYPE_VIDEO_ENCODE_AV1_PICTURE_INFO_KHR }
            , stdPictureInfo{}
            , stdTileInfo{}
            , stdQuantInfo{}
            , stdCdefInfo{}
            , stdLfInfo{}
            , stdLrInfo{}
            , bShowExistingFrame{}
            , frameToShowBufId{-1}
            , bIsKeyFrame{}
            , bShownKeyFrameOrSwitch{}
            , bOverlayFrame{}
            , bIsReference{}
            , rateControlInfoAV1{ VK_STRUCTURE_TYPE_VIDEO_ENCODE_AV1_RATE_CONTROL_INFO_KHR }
            , rateControlLayersInfoAV1{{ VK_STRUCTURE_TYPE_VIDEO_ENCODE_AV1_RATE_CONTROL_LAYER_INFO_KHR }}
        {
            encodeInfo.pNext = &pictureInfo;

            pictureInfo.pStdPictureInfo = &stdPictureInfo;
        }

        virtual void Reset(bool releaseResources = true) override {

            pictureInfo.pNext = nullptr;

            // Reset the base first
            VkVideoEncodeFrameInfo::Reset(releaseResources);

            // After resetting the base structure parameters, start building the pNext chain again
            assert(pictureInfo.sType == VK_STRUCTURE_TYPE_VIDEO_ENCODE_AV1_PICTURE_INFO_KHR);
            encodeInfo.pNext = &pictureInfo;
        }

        virtual ~VkVideoEncodeFrameInfoAV1() {
            Reset(true);
        }
    };

    struct VkVideoEncoderAV1BitWriter {
        std::vector<uint8_t>& buffer;
        uint8_t bytedata;
        uint8_t bitcount;

        VkVideoEncoderAV1BitWriter(std::vector<uint8_t>& buffer_)
            : buffer(buffer_)
            , bytedata(0)
            , bitcount(0)
        { }

        void PutBits(int32_t code, int32_t len) {
            for (int32_t i = len - 1; i >= 0; i--) {
                uint8_t mask = static_cast<uint8_t>(1 << i);
                uint8_t bit = (code & mask) ? 1 : 0;
                bytedata = (uint8_t)(bytedata << 1);
                bytedata |= bit;
                bitcount++;

                if (bitcount >= 8) {
                    buffer.push_back(bytedata);
                    bytedata = 0;
                    bitcount = 0;
                }
            }
        }

        void PutTrailingBits() {
            PutBits(1, 1);
            if (bitcount > 0) {
                bytedata = (uint8_t)(bytedata << (8 - bitcount));
                buffer.push_back(bytedata);
            }
        }

        void PutLeb128(uint32_t size) {
            assert(bitcount == 0);

            while (size >> 7) {
                buffer.push_back(0x80 & (size & 0x7f));
                size >>= 7;
            }
            buffer.push_back((uint8_t)size);
        }
    };

    VkVideoEncoderAV1(const VulkanDeviceContext* vkDevCtx)
        : VkVideoEncoder(vkDevCtx)
        , m_encoderConfig()
        , m_stateAV1()
        , m_dpbAV1()
        , m_lastKeyFrameOrderHint()
        , m_numBFramesToEncode()
    { }

    virtual VkResult InitEncoderCodec(VkSharedBaseObj<EncoderConfig>& encoderConfig);
    virtual VkResult InitRateControl(VkCommandBuffer cmdBuf, uint32_t qp);
    virtual VkResult EncodeVideoSessionParameters(VkSharedBaseObj<VkVideoEncodeFrameInfo>& encodeFrameInfo);
    virtual VkResult ProcessDpb(VkSharedBaseObj<VkVideoEncodeFrameInfo>& encodeFrameInfo,
                                uint32_t frameIdx, uint32_t ofTotalframes);
    virtual VkResult CreateFrameInfoBuffersQueue(uint32_t numPoolNodes);
    virtual bool GetAvailablePoolNode(VkSharedBaseObj<VkVideoEncodeFrameInfo>& encodeFrameInfo) {
        VkSharedBaseObj<VkVideoEncodeFrameInfoAV1> encodeFrameInfoAV1;
        bool success = m_frameInfoBuffersQueue->GetAvailablePoolNode(encodeFrameInfoAV1);
        if (success) {
            encodeFrameInfo = encodeFrameInfoAV1;
        }
        return success;
    }

    virtual VkResult EncodeFrame(VkSharedBaseObj<VkVideoEncodeFrameInfo>& encodeFrameInfo);
    virtual VkResult HandleCtrlCmd(VkSharedBaseObj<VkVideoEncodeFrameInfo>& encodeFrameInfo);
    virtual VkResult StartOfVideoCodingEncodeOrder(VkSharedBaseObj<VkVideoEncodeFrameInfo>& encodeFrameInfo, uint32_t frameIdx, uint32_t ofTotalFrames);
    virtual VkResult RecordVideoCodingCmd(VkSharedBaseObj<VkVideoEncodeFrameInfo>& encodeFrameInfo,
                                         uint32_t frameIdx, uint32_t ofTotalFrames);
    virtual VkResult SubmitVideoCodingCmds(VkSharedBaseObj<VkVideoEncodeFrameInfo>& encodeFrameInfo,
                                           uint32_t frameIdx, uint32_t ofTotalFrames);
    virtual VkResult AssembleBitstreamData(VkSharedBaseObj<VkVideoEncodeFrameInfo>& encodeFrameInfo,
                                           uint32_t frameIdx, uint32_t ofTotalFrames);
    void WriteShowExistingFrameHeader(VkSharedBaseObj<VkVideoEncodeFrameInfo>& encodeFrameInfo);

    virtual void InsertOrdered(VkSharedBaseObj<VkVideoEncodeFrameInfo>& current,
                               VkSharedBaseObj<VkVideoEncodeFrameInfo>& prev,
                               VkSharedBaseObj<VkVideoEncodeFrameInfo>& node);
    void AppendShowExistingFrame(VkSharedBaseObj<VkVideoEncodeFrameInfo>& prev,
                                 VkSharedBaseObj<VkVideoEncodeFrameInfo>& node);

protected:
    virtual ~VkVideoEncoderAV1()
    {
        m_feedback2Output.Close();
        m_frameInfoBuffersQueue = nullptr;
        m_videoSessionParameters = nullptr;
        m_videoSession = nullptr;

        if (m_dpbAV1) {
            m_dpbAV1->DpbDestroy();
            m_dpbAV1 = nullptr;
        }
    }

private:
    struct Feedback2PartitionInfo {
        uint32_t index;
        VkQueryResultStatusKHR status;
        uint32_t offset;
        uint32_t size;
    };

    struct Feedback2FrameOutput {
        uint64_t frameIndex;
        bool hasAvgQp;
        bool hasMinQp;
        bool hasMaxQp;
        int32_t avgQp;
        int32_t minQp;
        int32_t maxQp;
        bool hasIntraPixels;
        bool hasInterPixels;
        bool hasSkippedPixels;
        uint32_t intraPixels;
        uint32_t interPixels;
        uint32_t skippedPixels;
        bool hasPicturePartitionCount;
        uint32_t picturePartitionCount;
        std::vector<Feedback2PartitionInfo> partitions;
    };

    struct EncodeFeedbackResults {
        uint32_t bitstreamStartOffset;
        uint32_t bitstreamSize;
        VkQueryResultStatusKHR status;
        VkBool32 hasOverrides;
        bool hasAverageQuantization;
        bool hasMinQuantization;
        bool hasMaxQuantization;
        int32_t averageQuantization;
        int32_t minQuantization;
        int32_t maxQuantization;
        bool hasIntraPixels;
        bool hasInterPixels;
        bool hasSkippedPixels;
        uint32_t intraPixels;
        uint32_t interPixels;
        uint32_t skippedPixels;
        bool hasPicturePartitionCount;
        uint32_t picturePartitionCount;
        std::vector<Feedback2PartitionInfo> partitions;
    };

    class Feedback2TextOutput {
    public:
        Feedback2TextOutput()
            : m_pictureEnabled(false)
            , m_partitionEnabled(false)
            , m_path()
            , m_file()
        {
        }

        VkResult Init(const EncoderConfigAV1& config);
        void Close();
        bool Enabled() const { return m_pictureEnabled || m_partitionEnabled; }
        bool PictureEnabled() const { return m_pictureEnabled; }
        bool PartitionEnabled() const { return m_partitionEnabled; }
        const std::string& GetPath() const { return m_path; }
        void WriteFrame(const Feedback2FrameOutput& output);

    private:
        bool m_pictureEnabled;
        bool m_partitionEnabled;
        std::string m_path;
        EncoderOutputFileHandler m_file;
    };

    VkVideoEncodeFrameInfoAV1* GetEncodeFrameInfoAV1(VkSharedBaseObj<VkVideoEncodeFrameInfo>& encodeFrameInfo) {
        assert(VK_VIDEO_CODEC_OPERATION_ENCODE_AV1_BIT_KHR == encodeFrameInfo->GetCodecType());
        VkVideoEncodeFrameInfo* pEncodeFrameInfo = encodeFrameInfo;
        return (VkVideoEncodeFrameInfoAV1*)pEncodeFrameInfo;
    }

    void InitializeFrameHeader(StdVideoAV1SequenceHeader* pSequenceHdr, VkVideoEncodeFrameInfoAV1* pFrameInfo,
                               StdVideoAV1ReferenceName& refName);
    VkResult GetEncodeFeedbackResults(VkQueryPool queryPool, uint32_t querySlotId, EncodeFeedbackResults& results);
    size_t GetEncodeFeedbackResultsSize() const;
    void WriteFeedback2Output(const VkVideoEncodeFrameInfoAV1* frameInfo,
                              const EncodeFeedbackResults* results);

    VkSharedBaseObj<EncoderConfigAV1>   m_encoderConfig;
    EncoderAV1State                     m_stateAV1;
    VkEncDpbAV1*                        m_dpbAV1;
    VkSharedBaseObj<VulkanBufferPool<VkVideoEncodeFrameInfoAV1>> m_frameInfoBuffersQueue;
    Feedback2TextOutput                 m_feedback2Output;

    int32_t                             m_lastKeyFrameOrderHint;
    uint32_t                            m_numBFramesToEncode;
    std::set<uint32_t>                  m_batchFramesIndxSetToAssemble;
    std::vector<std::vector<uint8_t>>   m_bitstream;

};


#endif /* _VKVIDEOENCODER_VKVIDEOENCODERAV1_H__ */
