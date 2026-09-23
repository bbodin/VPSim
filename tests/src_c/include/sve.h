#ifndef  __SVE_H__
#define __SVE_H__

#include <stdint.h>
#include <stdio.h>


static inline void enable_fp_el1(void) {
    asm volatile(
        "mrs x0, cpacr_el1       \n" // Read CPACR_EL1
        "orr x0, x0, (3 << 20) \n" // Set FPEN bits [21:20] = 0b11 to enable FP/SIMD at EL1
        "msr cpacr_el1, x0       \n" // Write back to CPACR_EL1
        "isb                     \n" // Instruction Synchronization Barrier
        :
        :
        : "x0", "memory"
    );
}

static inline int has_sve(void) {
    uint64_t pfr0 = 0;
    
    // Try to read ID_AA64PFR0_EL1 register
    // In QEMU without SVE support, this may return 0 or cause issues
    // We use inline asm with memory clobber to ensure the read happens
    asm volatile(
        "mrs %0, id_aa64pfr0_el1\n\t"
        : "=r" (pfr0)
        :
        : "memory"
    );
    
    // Check SVE field in ID_AA64PFR0_EL1 (bits 35:32)
    // SVE version field: bits 35:32
    // 0x0 = SVE not implemented
    // 0x1 = SVE implemented (version 1)
    // 0x2 = SVE implemented (version 2)
    // etc.
    uint64_t sve_version = (pfr0 >> 32) & 0xF;
    
    // SVE is supported if version field is non-zero
    return (sve_version != 0);
}


static inline void enable_sve_el1(void)
{
    asm volatile(
        // Enable SVE in CPACR_EL1: ZEN (bits 17:16) = 0b11
        "mrs x0, cpacr_el1\n"
        "orr x0, x0, (3 << 16)\n"
        "msr cpacr_el1, x0\n"
        "isb\n"

        // Set ZCR_EL1: vector length = 0 (max available)
        "mov x0, 0\n"
        "msr zcr_el1, x0\n"
        "isb\n"
        :
        :
        : "x0", "memory"
    );
}

static inline void _enable_sve_el1(void) {
if (has_sve()) {
    _enable_sve_el1(); // Only on CPUs that support it
}
}
#endif