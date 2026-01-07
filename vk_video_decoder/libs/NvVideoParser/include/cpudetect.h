#ifndef CPUDETECT_H
#define CPUDETECT_H

#include <assert.h>
#ifdef _WIN32
#include <intrin.h>
#endif

enum SIMD_ISA
{
    NOSIMD = 0,
    SSSE3,
    AVX2,
    AVX512,
    NEON,
    SVE
};

static int inline count_trailing_zeros(unsigned long long resmask)
{
    assert(resmask != 0ULL); // result is undefined if resmask is zero

#ifdef _WIN64
    unsigned long offset = 0;
    (void)_BitScanForward64(&offset, resmask);
#elif _WIN32
    unsigned long offset = 0;
    unsigned long resmaskLsb = (unsigned long)(resmask & 0xFFFFFFFFULL);
    if (resmaskLsb != 0U) {
        (void)_BitScanForward(&offset, resmaskLsb);
    }
    else {
        unsigned long resmaskMsb = (unsigned long)(resmask >> 32U);
        (void)_BitScanForward(&offset, resmaskMsb);
        offset += 32U;
    }
#else
    int offset = __builtin_ctzll(resmask);
#endif
    return offset;
}

SIMD_ISA check_simd_support();

#endif
