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
    uint64_t pfr0;
    asm volatile("mrs %0, id_aa64pfr0_el1" : "=r" (pfr0));
    return ((pfr0 >> 32) & 0xF) != 0; // SVE field
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