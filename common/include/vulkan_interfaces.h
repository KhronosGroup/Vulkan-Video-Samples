/*
* Copyright 2020 NVIDIA Corporation.
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

// Using the Vulkan APIs from Vulkan SDK
#ifndef VK_ENABLE_BETA_EXTENSIONS
#define VK_ENABLE_BETA_EXTENSIONS 1
#endif

// This flag is defined in CTS to build the parser source files which are also in the vk namespace in external/vulkancts/modules/vulkan/video
#ifdef DE_BUILD_VIDEO
#include "vkDefs.hpp"
using namespace vk;
// This flag is defined in CTS to build VVS library and provide the vulkan definitions from CTS in vkVulkan_c.inl
#elif defined(VVS_CTS_VULKAN_HEADER)
#include "vkDefs.h"
#if defined(VK_USE_PLATFORM_WIN32_KHR)
// windows.h is included only by vulkan/vulkan.h.
// In the case of CTS build using inl files, vkVulkan_c.inl does not include vulkan.h directly so
// does not expose the windows includes necessary in VulkanDeviceContext.h for ie HMODULE.
#include <windows.h>
// Disable win32 surface as vkVulan_c.inl does not expose the win32 functions such as CreateWin32SurfaceKHR.
#define VK_DISABLE_WIN32_SURFACE_KHR 1
#endif
#else
#include "vulkan/vulkan.h"
#endif
