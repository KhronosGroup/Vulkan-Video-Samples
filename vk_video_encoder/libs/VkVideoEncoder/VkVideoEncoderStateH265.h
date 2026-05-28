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

#ifndef _VKVIDEOENCODER_VKVIDEOENCODERSTATEH265_H_
#define _VKVIDEOENCODER_VKVIDEOENCODERSTATEH265_H_

class VideoSessionParametersInfoH265 {
public:
    VideoSessionParametersInfoH265(VkVideoSessionKHR videoSession,
                                   StdVideoH265VideoParameterSet* vps,
                                   StdVideoH265SequenceParameterSet* sps,
                                   StdVideoH265PictureParameterSet* pps,
                                   uint32_t qualityLevel,
                                   bool enableQpMap = false, VkExtent2D qpMapTexelSize = {0, 0})
    {
        m_videoSession = videoSession;

        m_encodeH265SessionParametersAddInfo.sType = VK_STRUCTURE_TYPE_VIDEO_ENCODE_H265_SESSION_PARAMETERS_ADD_INFO_KHR;
        m_encodeH265SessionParametersAddInfo.pNext = nullptr;
        m_encodeH265SessionParametersAddInfo.stdVPSCount = 1;
        m_encodeH265SessionParametersAddInfo.pStdVPSs = vps;
        m_encodeH265SessionParametersAddInfo.stdSPSCount = 1;
        m_encodeH265SessionParametersAddInfo.pStdSPSs = sps;
        m_encodeH265SessionParametersAddInfo.stdPPSCount = 1;
        m_encodeH265SessionParametersAddInfo.pStdPPSs = pps;

        m_encodeH265SessionParametersCreateInfo.sType = VK_STRUCTURE_TYPE_VIDEO_ENCODE_H265_SESSION_PARAMETERS_CREATE_INFO_KHR;
        m_encodeH265SessionParametersCreateInfo.pNext = nullptr;
        m_encodeH265SessionParametersCreateInfo.maxStdVPSCount = 1;
        m_encodeH265SessionParametersCreateInfo.maxStdSPSCount = 1;
        m_encodeH265SessionParametersCreateInfo.maxStdPPSCount = 1;
        m_encodeH265SessionParametersCreateInfo.pParametersAddInfo = &m_encodeH265SessionParametersAddInfo;

        m_encodeSessionParametersCreateInfo.sType = VK_STRUCTURE_TYPE_VIDEO_SESSION_PARAMETERS_CREATE_INFO_KHR;
        m_encodeSessionParametersCreateInfo.pNext = &m_encodeH265SessionParametersCreateInfo;
        m_encodeSessionParametersCreateInfo.flags = 0;
        m_encodeSessionParametersCreateInfo.videoSessionParametersTemplate = VK_NULL_HANDLE;
        m_encodeSessionParametersCreateInfo.videoSession = m_videoSession;

        m_qualityLevelInfo.sType = VK_STRUCTURE_TYPE_VIDEO_ENCODE_QUALITY_LEVEL_INFO_KHR;
        m_qualityLevelInfo.pNext = nullptr;
        m_qualityLevelInfo.qualityLevel = qualityLevel;

        m_encodeH265SessionParametersCreateInfo.pNext = &m_qualityLevelInfo;

        if (enableQpMap) {
            m_encodeQuantizationMapSessionParametersCreateInfo.sType = VK_STRUCTURE_TYPE_VIDEO_ENCODE_QUANTIZATION_MAP_SESSION_PARAMETERS_CREATE_INFO_KHR;
            m_encodeQuantizationMapSessionParametersCreateInfo.pNext = nullptr;
            m_encodeQuantizationMapSessionParametersCreateInfo.quantizationMapTexelSize = qpMapTexelSize;

            m_qualityLevelInfo.pNext = &m_encodeQuantizationMapSessionParametersCreateInfo;

            m_encodeSessionParametersCreateInfo.flags = VK_VIDEO_SESSION_PARAMETERS_CREATE_QUANTIZATION_MAP_COMPATIBLE_BIT_KHR;
        }
    }

    inline VkVideoSessionParametersCreateInfoKHR* getVideoSessionParametersInfo()
    {
        return &m_encodeSessionParametersCreateInfo;
    };
private:
    VkVideoSessionKHR m_videoSession;
    VkVideoEncodeH265SessionParametersAddInfoKHR m_encodeH265SessionParametersAddInfo;
    VkVideoEncodeH265SessionParametersCreateInfoKHR m_encodeH265SessionParametersCreateInfo;
    VkVideoSessionParametersCreateInfoKHR m_encodeSessionParametersCreateInfo;
    VkVideoEncodeQualityLevelInfoKHR m_qualityLevelInfo;
    VkVideoEncodeQuantizationMapSessionParametersCreateInfoKHR m_encodeQuantizationMapSessionParametersCreateInfo;
};

struct VpsH265
{
    StdVideoH265VideoParameterSet vpsInfo = {};
};

struct SpsH265 {
    SpsH265()
    {
        hrdParameters.pSubLayerHrdParametersNal = &subLayerHrdParametersNal;

        vuiInfo.pHrdParameters = &hrdParameters;

        sps.pProfileTierLevel        = &profileTierLevel;
        sps.pDecPicBufMgr            = &decPicBufMgr;
        sps.pShortTermRefPicSet      = &shortTermRefPicSet;
        sps.pSequenceParameterSetVui = &vuiInfo;
    }

    StdVideoH265SequenceParameterSet     sps = {};
    StdVideoH265DecPicBufMgr             decPicBufMgr = {};
    StdVideoH265HrdParameters            hrdParameters = {};
    StdVideoH265ProfileTierLevel         profileTierLevel = {};
    StdVideoH265ShortTermRefPicSet       shortTermRefPicSet = {};
    StdVideoH265LongTermRefPicsSps       longTermRefPicsSps = {};
    StdVideoH265SequenceParameterSetVui  vuiInfo = {};
    StdVideoH265SubLayerHrdParameters    subLayerHrdParametersNal = {};
};

#endif /* _VKVIDEOENCODER_VKVIDEOENCODERSTATEH265_H_ */
