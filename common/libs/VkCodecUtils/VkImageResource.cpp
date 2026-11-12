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

#include <atomic>
#include "VkCodecUtils/HelpersDispatchTable.h"
#include "VkCodecUtils/Helpers.h"
#include "VkCodecUtils/VulkanDeviceContext.h"
#include "nvidia_utils/vulkan/ycbcrvkinfo.h"
#include "VkImageResource.h"

VkImageResource::VkImageResource(const VulkanDeviceContext* vkDevCtx,
                const VkImageCreateInfo* pImageCreateInfo,
                VkImage image, VkDeviceSize imageOffset, VkDeviceSize imageSize,
                VkSharedBaseObj<VulkanDeviceMemoryImpl>& vulkanDeviceMemory,
                uint64_t drmFormatModifier,
                uint32_t memoryPlaneCount)
   : m_refCount(0), m_imageCreateInfo(*pImageCreateInfo), m_vkDevCtx(vkDevCtx)
   , m_image(image), m_imageOffset(imageOffset), m_imageSize(imageSize)
   , m_vulkanDeviceMemory(vulkanDeviceMemory), m_layouts{}, m_memoryPlaneLayouts{}
   , m_drmFormatModifier(drmFormatModifier), m_memoryPlaneCount(memoryPlaneCount)
   , m_isLinearImage(false), m_is16Bit(false), m_isSubsampledX(false), m_isSubsampledY(false)
   , m_usesDrmFormatModifier(drmFormatModifier != 0 || pImageCreateInfo->tiling == VK_IMAGE_TILING_DRM_FORMAT_MODIFIER_EXT) {

    // Query memory plane layouts for DRM format modifier images
    // Per Vulkan spec: For VK_IMAGE_TILING_DRM_FORMAT_MODIFIER_EXT, must use
    // VK_IMAGE_ASPECT_MEMORY_PLANE_*_BIT_EXT aspect flags
    if (m_usesDrmFormatModifier && m_memoryPlaneCount > 0) {
        static const VkImageAspectFlagBits memoryPlaneAspects[] = {
            VK_IMAGE_ASPECT_MEMORY_PLANE_0_BIT_EXT,
            VK_IMAGE_ASPECT_MEMORY_PLANE_1_BIT_EXT,
            VK_IMAGE_ASPECT_MEMORY_PLANE_2_BIT_EXT,
            VK_IMAGE_ASPECT_MEMORY_PLANE_3_BIT_EXT
        };
        for (uint32_t p = 0; p < m_memoryPlaneCount && p < 4; ++p) {
            VkImageSubresource subRes{};
            subRes.aspectMask = memoryPlaneAspects[p];
            subRes.mipLevel = 0;
            subRes.arrayLayer = 0;
            m_vkDevCtx->GetImageSubresourceLayout(*vkDevCtx, image, &subRes, &m_memoryPlaneLayouts[p]);
        }
    }

    const VkMpFormatInfo* mpInfo = YcbcrVkFormatInfo(pImageCreateInfo->format);
    VkImageSubresource subResource = {};
    if (mpInfo == nullptr) {
        m_isLinearImage = (pImageCreateInfo->tiling == VK_IMAGE_TILING_LINEAR);
        if (m_isLinearImage) {
            subResource.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT;
            m_vkDevCtx->GetImageSubresourceLayout(*vkDevCtx, image, &subResource, &m_layouts[0]);
        }
        return;
    }

    m_isSubsampledX = (mpInfo && mpInfo->planesLayout.secondaryPlaneSubsampledX);
    m_isSubsampledY = (mpInfo && mpInfo->planesLayout.secondaryPlaneSubsampledY);

    // Treat all non 8bpp formats as 16bpp for output to prevent any loss.
    m_is16Bit = (mpInfo->planesLayout.bpp != YCBCRA_8BPP);

    VkMemoryPropertyFlags memoryPropertyFlags = vulkanDeviceMemory->GetMemoryPropertyFlags();
    if ((memoryPropertyFlags & VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT) == 0) {
        return;
    }

    m_isLinearImage = true;
    bool isUnnormalizedRgba = false;
    if (mpInfo && (mpInfo->planesLayout.layout == YCBCR_SINGLE_PLANE_UNNORMALIZED) && !(mpInfo->planesLayout.disjoint)) {
        isUnnormalizedRgba = true;
    }

    if (mpInfo && !isUnnormalizedRgba) {
        switch (mpInfo->planesLayout.layout) {
            case YCBCR_SINGLE_PLANE_UNNORMALIZED:
            case YCBCR_SINGLE_PLANE_INTERLEAVED:
                subResource.aspectMask = VK_IMAGE_ASPECT_PLANE_0_BIT;
                m_vkDevCtx->GetImageSubresourceLayout(*vkDevCtx, image, &subResource, &m_layouts[0]);
                break;
            case YCBCR_SEMI_PLANAR_CBCR_INTERLEAVED:
                subResource.aspectMask = VK_IMAGE_ASPECT_PLANE_0_BIT;
                m_vkDevCtx->GetImageSubresourceLayout(*vkDevCtx, image, &subResource, &m_layouts[0]);
                subResource.aspectMask = VK_IMAGE_ASPECT_PLANE_1_BIT;
                m_vkDevCtx->GetImageSubresourceLayout(*vkDevCtx, image, &subResource, &m_layouts[1]);
                break;
            case YCBCR_PLANAR_CBCR_STRIDE_INTERLEAVED:
            case YCBCR_PLANAR_CBCR_BLOCK_JOINED:
            case YCBCR_PLANAR_STRIDE_PADDED:
                subResource.aspectMask = VK_IMAGE_ASPECT_PLANE_0_BIT;
                m_vkDevCtx->GetImageSubresourceLayout(*vkDevCtx, image, &subResource, &m_layouts[0]);
                subResource.aspectMask = VK_IMAGE_ASPECT_PLANE_1_BIT;
                m_vkDevCtx->GetImageSubresourceLayout(*vkDevCtx, image, &subResource, &m_layouts[1]);
                subResource.aspectMask = VK_IMAGE_ASPECT_PLANE_2_BIT;
                m_vkDevCtx->GetImageSubresourceLayout(*vkDevCtx, image, &subResource, &m_layouts[2]);
                break;
            default:
                assert(0);
        }

    } else {
        m_vkDevCtx->GetImageSubresourceLayout(*vkDevCtx, image, &subResource, &m_layouts[0]);
    }
}

VkImageResource::~VkImageResource()
{
    Destroy();
}

VkResult VkImageResource::Create(const VulkanDeviceContext* vkDevCtx,
                                 const VkImageCreateInfo* pImageCreateInfo,
                                 VkMemoryPropertyFlags memoryPropertyFlags,
                                 VkSharedBaseObj<VkImageResource>& imageResource)
{
    VkResult result = VK_ERROR_INITIALIZATION_FAILED;

    VkDevice device = vkDevCtx->getDevice();
    VkImage image = VK_NULL_HANDLE;

    do {

        result = vkDevCtx->CreateImage(device, pImageCreateInfo, nullptr, &image);
        if (result != VK_SUCCESS) {
            assert(!"CreateImage Failed!");
            break;
        }

        VkMemoryRequirements memoryRequirements = { };
        vkDevCtx->GetImageMemoryRequirements(device, image, &memoryRequirements);

        // Allocate memory for the image
        VkSharedBaseObj<VulkanDeviceMemoryImpl> vkDeviceMemory;
        result = VulkanDeviceMemoryImpl::Create(vkDevCtx,
                                                memoryRequirements,
                                                memoryPropertyFlags,
                                                nullptr,  // pInitializeMemory
                                                0ULL,     // initializeMemorySize
                                                false,    // clearMemory
                                                vkDeviceMemory);
        if (result != VK_SUCCESS) {
            assert(!"Create Memory Failed!");
            break;
        }

        VkDeviceSize imageOffset = 0;
        result = vkDevCtx->BindImageMemory(device, image, *vkDeviceMemory, imageOffset);
        if (result != VK_SUCCESS) {
            assert(!"BindImageMemory Failed!");
            break;
        }

        imageResource = new VkImageResource(vkDevCtx,
                                            pImageCreateInfo,
                                            image,
                                            imageOffset,
                                            memoryRequirements.size,
                                            vkDeviceMemory);
        if (imageResource == nullptr) {
            break;
        }
        return result;

    } while (0);

    if (device != VK_NULL_HANDLE) {

        if (image != VK_NULL_HANDLE) {
            vkDevCtx->DestroyImage(device, image, nullptr);
        }
    }

    return result;
}

// DRM format modifiers the driver supports for this format.
static std::vector<VkDrmFormatModifierPropertiesEXT> QueryDrmFormatModifiers(const VulkanDeviceContext* vkDevCtx,
                                                                             VkFormat format)
{
    VkDrmFormatModifierPropertiesListEXT modList{VK_STRUCTURE_TYPE_DRM_FORMAT_MODIFIER_PROPERTIES_LIST_EXT};
    VkFormatProperties2 fmtProps{VK_STRUCTURE_TYPE_FORMAT_PROPERTIES_2, &modList};
    vkDevCtx->GetPhysicalDeviceFormatProperties2(vkDevCtx->getPhysicalDevice(), format, &fmtProps);
    std::vector<VkDrmFormatModifierPropertiesEXT> mods(modList.drmFormatModifierCount);
    modList.pDrmFormatModifierProperties = mods.data();
    vkDevCtx->GetPhysicalDeviceFormatProperties2(vkDevCtx->getPhysicalDevice(), format, &fmtProps);
    return mods;
}

// View formats for VkImageFormatListCreateInfo, required with MUTABLE_FORMAT_BIT on
// DRM format modifier images (VUID-VkImageCreateInfo-tiling-02353).
static uint32_t GetDrmModifierViewFormats(VkFormat format, VkFormat (&viewFormats)[4])
{
    uint32_t viewFormatCount = 0;
    viewFormats[viewFormatCount++] = format;
    const VkMpFormatInfo* mpInfo = YcbcrVkFormatInfo(format);
    if (mpInfo && mpInfo->planesLayout.numberOfExtraPlanes > 0) {
        const uint32_t numPlanes = 1 + mpInfo->planesLayout.numberOfExtraPlanes;
        for (uint32_t p = 0; p < numPlanes && p < VK_MAX_NUM_IMAGE_PLANES_EXT; ++p) {
            if (mpInfo->vkPlaneFormat[p] != VK_FORMAT_UNDEFINED && mpInfo->vkPlaneFormat[p] != format) {
                viewFormats[viewFormatCount++] = mpInfo->vkPlaneFormat[p];
            }
        }
    }
    return viewFormatCount;
}

// vkGetPhysicalDeviceImageFormatProperties2 for exporting createInfo's image with handleType.
// createInfo.pNext must only hold structs valid there (e.g. the video profile list).
static VkResult GetExportImageFormatProperties(const VulkanDeviceContext* vkDevCtx,
                                               const VkImageCreateInfo& createInfo,
                                               VkImageTiling tiling, uint64_t drmFormatModifier,
                                               VkExternalMemoryHandleTypeFlagBits handleType,
                                               VkImageFormatProperties& limits,
                                               VkExternalMemoryFeatureFlags& externalMemoryFeatures)
{
    VkFormat viewFormats[4] = {};
    VkImageFormatListCreateInfo formatList{VK_STRUCTURE_TYPE_IMAGE_FORMAT_LIST_CREATE_INFO};
    VkPhysicalDeviceImageDrmFormatModifierInfoEXT modInfo{
        VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_IMAGE_DRM_FORMAT_MODIFIER_INFO_EXT};
    const void* pNext = createInfo.pNext;
    if (tiling == VK_IMAGE_TILING_DRM_FORMAT_MODIFIER_EXT) {
        if (createInfo.flags & VK_IMAGE_CREATE_MUTABLE_FORMAT_BIT) {
            formatList.pNext = pNext;
            formatList.viewFormatCount = GetDrmModifierViewFormats(createInfo.format, viewFormats);
            formatList.pViewFormats = viewFormats;
            pNext = &formatList;
        }
        modInfo.pNext = pNext;
        modInfo.drmFormatModifier = drmFormatModifier;
        modInfo.sharingMode = createInfo.sharingMode;
        if (createInfo.sharingMode == VK_SHARING_MODE_CONCURRENT) {
            modInfo.queueFamilyIndexCount = createInfo.queueFamilyIndexCount;
            modInfo.pQueueFamilyIndices = createInfo.pQueueFamilyIndices;
        }
        pNext = &modInfo;
    }
    VkPhysicalDeviceExternalImageFormatInfo extInfo{
        VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_EXTERNAL_IMAGE_FORMAT_INFO, pNext, handleType};
    VkPhysicalDeviceImageFormatInfo2 info{VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_IMAGE_FORMAT_INFO_2, &extInfo};
    info.format = createInfo.format;
    info.type = createInfo.imageType;
    info.tiling = tiling;
    info.usage = createInfo.usage;
    info.flags = createInfo.flags;

    VkExternalImageFormatProperties extProps{VK_STRUCTURE_TYPE_EXTERNAL_IMAGE_FORMAT_PROPERTIES};
    VkImageFormatProperties2 props{VK_STRUCTURE_TYPE_IMAGE_FORMAT_PROPERTIES_2, &extProps};
    const VkResult result = vkDevCtx->GetPhysicalDeviceImageFormatProperties2(
        vkDevCtx->getPhysicalDevice(), &info, &props);
    limits = props.imageFormatProperties;
    externalMemoryFeatures = extProps.externalMemoryProperties.externalMemoryFeatures;
    return result;
}

bool VkImageResource::SelectExportDrmModifier(const VulkanDeviceContext* vkDevCtx,
                                              const VkImageCreateInfo& createInfo,
                                              VkExternalMemoryHandleTypeFlagBits handleType,
                                              uint64_t& drmFormatModifier)
{
    static constexpr uint64_t drmFormatModLinear = 0; // DRM_FORMAT_MOD_LINEAR

    const std::vector<VkDrmFormatModifierPropertiesEXT> mods = QueryDrmFormatModifiers(vkDevCtx, createInfo.format);

    // Non-linear modifiers first, LINEAR as the fallback.
    for (const bool wantLinear : { false, true }) {
        for (const auto& m : mods) {
            if ((m.drmFormatModifier == drmFormatModLinear) != wantLinear) {
                continue;
            }
            VkImageFormatProperties limits{};
            VkExternalMemoryFeatureFlags externalMemoryFeatures = 0;
            if (GetExportImageFormatProperties(vkDevCtx, createInfo, VK_IMAGE_TILING_DRM_FORMAT_MODIFIER_EXT,
                                               m.drmFormatModifier, handleType,
                                               limits, externalMemoryFeatures) != VK_SUCCESS) {
                continue;
            }
            if (((externalMemoryFeatures & VK_EXTERNAL_MEMORY_FEATURE_EXPORTABLE_BIT) == 0) ||
                (createInfo.extent.width > limits.maxExtent.width) ||
                (createInfo.extent.height > limits.maxExtent.height) ||
                (createInfo.arrayLayers > limits.maxArrayLayers)) {
                continue;
            }
            drmFormatModifier = m.drmFormatModifier;
            return true;
        }
    }
    return false;
}

VkResult VkImageResource::CreateExportable(const VulkanDeviceContext* vkDevCtx,
                                           const VkImageCreateInfo* pImageCreateInfo,
                                           VkMemoryPropertyFlags memoryPropertyFlags,
                                           VkExternalMemoryHandleTypeFlags exportHandleTypes,
                                           uint64_t drmFormatModifier,
                                           VkSharedBaseObj<VkImageResource>& imageResource)
{
    VkResult result = VK_ERROR_INITIALIZATION_FAILED;

    VkDevice device = vkDevCtx->getDevice();
    VkImage image = VK_NULL_HANDLE;

    // Build modified image create info with external memory and DRM format modifier
    VkImageCreateInfo modifiedImageInfo = *pImageCreateInfo;

    // Setup DRM format modifier if specified
    VkImageDrmFormatModifierListCreateInfoEXT drmModList{VK_STRUCTURE_TYPE_IMAGE_DRM_FORMAT_MODIFIER_LIST_CREATE_INFO_EXT};
    VkExternalMemoryImageCreateInfo extMemImageInfo{VK_STRUCTURE_TYPE_EXTERNAL_MEMORY_IMAGE_CREATE_INFO};

    // For MUTABLE_FORMAT_BIT with DRM modifiers, we need VkImageFormatListCreateInfo
    // Include the main format plus plane formats for YCbCr
    VkFormat viewFormats[4] = {};
    uint32_t viewFormatCount = 0;
    VkImageFormatListCreateInfo formatList{VK_STRUCTURE_TYPE_IMAGE_FORMAT_LIST_CREATE_INFO};

    // Check if DRM format modifier should be used:
    // - UINT64_MAX = sentinel for "no DRM modifier, use VK_IMAGE_TILING_OPTIMAL with opaque FD"
    // - DMA_BUF handle type requires DRM format modifier (modifier 0 = LINEAR is valid)
    // - Or explicit non-zero modifier was specified
    bool useDrmModifier = (drmFormatModifier != UINT64_MAX) &&
                          ((exportHandleTypes & VK_EXTERNAL_MEMORY_HANDLE_TYPE_DMA_BUF_BIT_EXT) ||
                           (drmFormatModifier != 0));

    if (useDrmModifier || exportHandleTypes != 0) {
        extMemImageInfo.handleTypes = exportHandleTypes;

        if (useDrmModifier) {
            // Use DRM format modifier tiling (modifier 0 = DRM_FORMAT_MOD_LINEAR)
            modifiedImageInfo.tiling = VK_IMAGE_TILING_DRM_FORMAT_MODIFIER_EXT;
            drmModList.drmFormatModifierCount = 1;
            drmModList.pDrmFormatModifiers = &drmFormatModifier;

            // If MUTABLE_FORMAT_BIT is set, we need VkImageFormatListCreateInfo
            // per VUID-VkImageCreateInfo-tiling-02353
            if (pImageCreateInfo->flags & VK_IMAGE_CREATE_MUTABLE_FORMAT_BIT) {
                viewFormatCount = GetDrmModifierViewFormats(pImageCreateInfo->format, viewFormats);
                formatList.viewFormatCount = viewFormatCount;
                formatList.pViewFormats = viewFormats;

                // Build pNext chain: formatList -> drmModList -> extMemImageInfo -> original pNext
                formatList.pNext = &drmModList;
                drmModList.pNext = &extMemImageInfo;
                extMemImageInfo.pNext = pImageCreateInfo->pNext;
                modifiedImageInfo.pNext = &formatList;
            } else {
                // No MUTABLE_FORMAT_BIT - no format list needed
                // Build pNext chain: drmModList -> extMemImageInfo -> original pNext
                drmModList.pNext = &extMemImageInfo;
                extMemImageInfo.pNext = pImageCreateInfo->pNext;
                modifiedImageInfo.pNext = &drmModList;
            }
        } else {
            // Just add external memory info
            extMemImageInfo.pNext = pImageCreateInfo->pNext;
            modifiedImageInfo.pNext = &extMemImageInfo;
        }
    }

    do {
        result = vkDevCtx->CreateImage(device, &modifiedImageInfo, nullptr, &image);
        if (result != VK_SUCCESS) {
            assert(!"CreateImage Failed!");
            break;
        }

        // Query the actual DRM format modifier used by the driver
        uint64_t actualDrmModifier = 0;
        uint32_t memoryPlaneCount = 1;  // Default for non-DRM images
        if (modifiedImageInfo.tiling == VK_IMAGE_TILING_DRM_FORMAT_MODIFIER_EXT) {
            VkImageDrmFormatModifierPropertiesEXT modProps{VK_STRUCTURE_TYPE_IMAGE_DRM_FORMAT_MODIFIER_PROPERTIES_EXT};
            // Use PFN from device context (inherits from VkInterfaceFunctions)
            PFN_vkGetImageDrmFormatModifierPropertiesEXT pfnGetDrmMod =
                (PFN_vkGetImageDrmFormatModifierPropertiesEXT)vkDevCtx->GetDeviceProcAddr(device, "vkGetImageDrmFormatModifierPropertiesEXT");
            if (pfnGetDrmMod) {
                pfnGetDrmMod(device, image, &modProps);
                actualDrmModifier = modProps.drmFormatModifier;
            } else {
                actualDrmModifier = drmFormatModifier; // Fallback to requested value
            }

            // The memory plane count belongs to the modifier and may differ from the format's
            // plane count; MEMORY_PLANE_i may only be queried below it.
            memoryPlaneCount = 0;
            for (const auto& m : QueryDrmFormatModifiers(vkDevCtx, modifiedImageInfo.format)) {
                if (m.drmFormatModifier == actualDrmModifier) {
                    memoryPlaneCount = m.drmFormatModifierPlaneCount;
                    break;
                }
            }
            if (memoryPlaneCount == 0) {
                assert(!"Image DRM format modifier not listed for its format");
                result = VK_ERROR_FORMAT_NOT_SUPPORTED;
                break;
            }
        }

        VkMemoryRequirements memoryRequirements = { };
        vkDevCtx->GetImageMemoryRequirements(device, image, &memoryRequirements);

        // Build export memory allocate info
        VkExportMemoryAllocateInfo exportMemInfo{VK_STRUCTURE_TYPE_EXPORT_MEMORY_ALLOCATE_INFO};
        exportMemInfo.handleTypes = exportHandleTypes;

        // A handle type may require a dedicated allocation (VUID-VkMemoryAllocateInfo-pNext-00639);
        // NVIDIA reports it for DMA-BUF with block-linear modifiers.
        VkMemoryDedicatedAllocateInfo dedicatedInfo{VK_STRUCTURE_TYPE_MEMORY_DEDICATED_ALLOCATE_INFO};
        dedicatedInfo.image = image;
        for (uint32_t bit = 0; bit < 32; bit++) {
            const auto handleType = static_cast<VkExternalMemoryHandleTypeFlagBits>(1u << bit);
            if ((exportHandleTypes & handleType) == 0) {
                continue;
            }
            VkImageFormatProperties limits{};
            VkExternalMemoryFeatureFlags features = 0;
            if ((GetExportImageFormatProperties(vkDevCtx, *pImageCreateInfo, modifiedImageInfo.tiling,
                                                actualDrmModifier, handleType, limits, features) == VK_SUCCESS) &&
                (features & VK_EXTERNAL_MEMORY_FEATURE_DEDICATED_ONLY_BIT)) {
                exportMemInfo.pNext = &dedicatedInfo;
                break;
            }
        }

        // Allocate memory with export capabilities
        VkSharedBaseObj<VulkanDeviceMemoryImpl> vkDeviceMemory;
        result = VulkanDeviceMemoryImpl::CreateWithExport(vkDevCtx,
                                                          memoryRequirements,
                                                          memoryPropertyFlags,
                                                          (exportHandleTypes != 0) ? &exportMemInfo : nullptr,
                                                          nullptr,  // pInitializeMemory
                                                          0ULL,     // initializeMemorySize
                                                          false,    // clearMemory
                                                          vkDeviceMemory);
        if (result != VK_SUCCESS) {
            assert(!"Create Memory Failed!");
            break;
        }

        VkDeviceSize imageOffset = 0;
        result = vkDevCtx->BindImageMemory(device, image, *vkDeviceMemory, imageOffset);
        if (result != VK_SUCCESS) {
            assert(!"BindImageMemory Failed!");
            break;
        }

        imageResource = new VkImageResource(vkDevCtx,
                                            &modifiedImageInfo,
                                            image,
                                            imageOffset,
                                            memoryRequirements.size,
                                            vkDeviceMemory,
                                            actualDrmModifier,
                                            memoryPlaneCount);
        if (imageResource == nullptr) {
            break;
        }
        return result;

    } while (0);

    if (device != VK_NULL_HANDLE) {
        if (image != VK_NULL_HANDLE) {
            vkDevCtx->DestroyImage(device, image, nullptr);
        }
    }

    return result;
}

bool VkImageResource::IsExportable() const
{
    return m_vulkanDeviceMemory && m_vulkanDeviceMemory->IsExportable();
}

bool VkImageResource::GetMemoryPlaneLayout(uint32_t planeIndex, VkSubresourceLayout& layout) const
{
    if (!m_usesDrmFormatModifier || planeIndex >= m_memoryPlaneCount || planeIndex >= 4) {
        return false;
    }
    layout = m_memoryPlaneLayouts[planeIndex];
    return true;
}

#ifdef _WIN32
VkResult VkImageResource::ExportNativeHandle(VkExternalMemoryHandleTypeFlagBits handleType, void** outHandle) const
{
    if (!m_vulkanDeviceMemory) {
        return VK_ERROR_INITIALIZATION_FAILED;
    }
    return m_vulkanDeviceMemory->ExportNativeHandle(handleType, outHandle);
}
#else
VkResult VkImageResource::ExportNativeHandle(VkExternalMemoryHandleTypeFlagBits handleType, int* outHandle) const
{
    if (!m_vulkanDeviceMemory) {
        return VK_ERROR_INITIALIZATION_FAILED;
    }
    return m_vulkanDeviceMemory->ExportNativeHandle(handleType, outHandle);
}
#endif

uint32_t VkImageResource::GetMemoryTypeIndex() const
{
    if (!m_vulkanDeviceMemory) {
        return 0;
    }
    return m_vulkanDeviceMemory->GetMemoryTypeIndex();
}


void VkImageResource::Destroy()
{
    assert(m_vkDevCtx != nullptr);

    if (m_image != VK_NULL_HANDLE) {
        m_vkDevCtx->DestroyImage(*m_vkDevCtx, m_image, nullptr);
        m_image = VK_NULL_HANDLE;
    }

    m_vulkanDeviceMemory = nullptr;
    m_vkDevCtx = nullptr;
}

VkResult VkImageResourceView::Create(const VulkanDeviceContext* vkDevCtx,
                                     VkSharedBaseObj<VkImageResource>& imageResource,
                                     VkImageSubresourceRange &imageSubresourceRange,
                                     VkSharedBaseObj<VkImageResourceView>& imageResourceView)
{
    VkDevice device = vkDevCtx->getDevice();
    VkImageView  imageViews[4];
    uint32_t numViews = 0;
    VkImageViewCreateInfo viewInfo = VkImageViewCreateInfo();
    viewInfo.sType = VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO;
    viewInfo.pNext = nullptr;
    viewInfo.image = imageResource->GetImage();
    viewInfo.viewType = (imageSubresourceRange.layerCount > 1) ? VK_IMAGE_VIEW_TYPE_2D_ARRAY : VK_IMAGE_VIEW_TYPE_2D;
    viewInfo.format = imageResource->GetImageCreateInfo().format;
    viewInfo.components = { VK_COMPONENT_SWIZZLE_IDENTITY, VK_COMPONENT_SWIZZLE_IDENTITY,
                            VK_COMPONENT_SWIZZLE_IDENTITY, VK_COMPONENT_SWIZZLE_IDENTITY};
    viewInfo.subresourceRange = imageSubresourceRange;
    viewInfo.flags = 0;
    VkResult result = vkDevCtx->CreateImageView(device, &viewInfo, nullptr, &imageViews[numViews]);
    if (result != VK_SUCCESS) {
        return result;
    }
    numViews++;

    const VkMpFormatInfo* mpInfo = YcbcrVkFormatInfo(viewInfo.format);
    if (mpInfo) {
        uint32_t numPlanes = 0;
        // Create separate image views for Y and CbCr planes
        viewInfo.format = mpInfo->vkPlaneFormat[numPlanes];  // For the Y plane
        viewInfo.subresourceRange.aspectMask = VK_IMAGE_ASPECT_PLANE_0_BIT << numPlanes;
        result = vkDevCtx->CreateImageView(device, &viewInfo, nullptr, &imageViews[numViews]);
        if (result != VK_SUCCESS) {
            return result;
        }
        numViews++;
        numPlanes++;

        if (mpInfo->planesLayout.numberOfExtraPlanes > 0) {
            viewInfo.format = mpInfo->vkPlaneFormat[numPlanes];  // For the CbCr plane
            viewInfo.subresourceRange.aspectMask = VK_IMAGE_ASPECT_PLANE_0_BIT << numPlanes;
            result = vkDevCtx->CreateImageView(device, &viewInfo, nullptr, &imageViews[numViews]);
            if (result != VK_SUCCESS) {
                return result;
            }
            numViews++;
            numPlanes++;

            if (mpInfo->planesLayout.numberOfExtraPlanes > 1) {
                viewInfo.format = mpInfo->vkPlaneFormat[numPlanes];  // For the CbCr plane
                viewInfo.subresourceRange.aspectMask = VK_IMAGE_ASPECT_PLANE_0_BIT << numPlanes;
                result = vkDevCtx->CreateImageView(device, &viewInfo, nullptr, &imageViews[numViews]);
                if (result != VK_SUCCESS) {
                    return result;
                }
                numViews++;
                numPlanes++;
            }
        }
    }

    imageResourceView = new VkImageResourceView(vkDevCtx, imageResource,
                                                numViews, numViews - 1,
                                                imageViews, imageSubresourceRange);

    return result;
}

VkImageResourceView::~VkImageResourceView()
{
    for (uint32_t imageViewIndx = 0; imageViewIndx < m_numViews; imageViewIndx++) {
        if (m_imageViews[imageViewIndx] != VK_NULL_HANDLE) {
            m_vkDevCtx->DestroyImageView(*m_vkDevCtx, m_imageViews[imageViewIndx], nullptr);
            m_imageViews[imageViewIndx] = VK_NULL_HANDLE;
        }
    }

    m_imageResource = nullptr;
    m_vkDevCtx = nullptr;
}
