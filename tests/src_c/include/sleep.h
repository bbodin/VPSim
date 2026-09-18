#ifndef __SLEEP__
#define __SLEEP__
#include <stdint.h>



// Function to enable the FPU
void enable_fpu(void) {
    // Read the CPACR_EL1 register
    uint32_t cpacr;
    __asm__ volatile ("mrs %0, cpacr_el1" : "=r" (cpacr));

    // Set the FPU enable bits (bits 20 and 21)
    cpacr |= (3 << 20);

    // Write the modified CPACR_EL1 register back
    __asm__ volatile ("msr cpacr_el1, %0" : : "r" (cpacr));

    // Ensure the FPU is enabled in the SCTLR_EL1 register (optional)
    uint32_t sctlr;
    __asm__ volatile ("mrs %0, sctlr_el1" : "=r" (sctlr));
    sctlr |= (1 << 12); // Set the M bit (bit 12) to enable the FPU
    __asm__ volatile ("msr sctlr_el1, %0" : : "r" (sctlr));
}

static inline unsigned long read_cntvct(void) {
    unsigned long cnt;
    asm volatile("mrs %0, cntvct_el0" : "=r" (cnt));
    return cnt;
}

static inline unsigned long read_cntfrq(void) {
    unsigned long frq;
    asm volatile("mrs %0, cntfrq_el0" : "=r" (frq));
    return frq;
}

static inline unsigned long read_cntpct(void) {
    unsigned long cnt;
    asm volatile("mrs %0, CNTPCT_EL0" : "=r" (cnt));
    return cnt;
}


void sleep_ms(unsigned int ms) {
    unsigned long start = read_cntpct();
    unsigned long  long freq  = read_cntfrq();
    unsigned long  long ticks = (freq * ms) / 1000ULL;
    while ((unsigned long long)(read_cntvct() - start) < ticks);
}

void sleep_s(unsigned int s) {
    unsigned long start = read_cntvct();
    unsigned long  long freq  = read_cntfrq();
    unsigned long  long ticks = (freq * s);
    while ((unsigned long long)(read_cntvct() - start) < ticks);
}


// Sleep function
void sleep_fp(float iterations) {
    float counter = iterations;
    while (counter > 0.0f) {
        counter = counter - 1.0f;
        __asm__ volatile ("nop");
    }
}

#endif