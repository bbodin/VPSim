#ifndef  __STRESS_H__
#define __STRESS_H__

#include <stdint.h>
#include <stddef.h>

#define BUFFER_SIZE (1024 * 1024)  // 1 MiB buffer
volatile uint8_t buffer[BUFFER_SIZE];

// A simple lightweight deterministic "pseudo-random" pattern generator:
// Uses a linear congruential generator style increment (not truly random)
static inline uint32_t next_index(uint32_t prev) {
    // constants chosen to cover buffer well, avoid clustering
    return (prev * 31 + 17) % BUFFER_SIZE;
}

// Stress memory with sparse and deterministic read/write patterns
void stress_memory(size_t read_count, size_t write_count) {
    uint32_t idx = 0;
    uint32_t val = 0x55;  // some constant to write
    
    // Writes: sparse spaced writes
    for (size_t i = 0; i < write_count; i++) {
        idx = next_index(idx);
        buffer[idx] = (uint8_t)(val & 0xFF);
        val += 13;  // vary written values deterministically
    }

    idx = 0;
    uint32_t sum = 0;

    // Reads: sparse spaced reads
    for (size_t i = 0; i < read_count; i++) {
        idx = next_index(idx);
        sum += buffer[idx];
    }

    // Use sum so reads aren't optimized away
    if (sum == 0xFFFFFFFF) {
        volatile int dummy = 0;
        (void)dummy;
    }
}

void read_in_order(size_t n_count) {
    volatile int dummy = 0;

    // Read the elements in order from the buffer
    for (size_t i = 0; i < n_count; i++) {
        dummy += buffer[i];
    }
}

void write_in_order(size_t n_count) {
    for (size_t i = 0; i < n_count; i++) {
        buffer[i] = i;
    }
}

void stress_fpu(unsigned iterations)
{
    float b = 42.0f;

    for (unsigned i = 0; i < iterations; i++) {
        __asm__ volatile (
            "ldr     s0, %0      \n\t"   // load b into s0 (single precision)
            "fadd    s1, s0, s0  \n\t"
            "fmul    s2, s0, s0  \n\t"
            "fsub    s3, s1, s2  \n\t"
            "fdiv    s4, s2, s1  \n\t"
            :
            : "m"(b)
            : "s0","s1","s2","s3","s4"
        );
    }
}

void stress_sve(unsigned iterations)
{
    float b[4] = {1,2,3,4};

    __asm__ volatile(
        "mov x0, %1\n"
        "mov w1, %w0\n"

        "ptrue p0.s\n"

        "1:\n"
        "ld1w {z0.s}, p0/z, [x0]\n"

        "movprfx z1, z0\n"
        "add z1.s, p0/m, z1.s, z0.s\n"

        "movprfx z2, z0\n"
        "mul z2.s, p0/m, z2.s, z0.s\n"

        "subs w1, w1, #1\n"
        "b.ne 1b\n"
        :
        : "r"(iterations), "r"(b)
        : "x0","x1","p0","z0","z1","z2","cc","memory");
}



#endif // __STRESS_H__