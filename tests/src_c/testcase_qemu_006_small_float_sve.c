#include <printf.h>
#include <qemu.h>
#include <sve.h>

void test_sve() {
    // Check if SVE is supported before enabling
    if (!has_sve()) {
        printf_str("SVE not supported on this CPU, skipping SVE test\n");
        return;
    }

    enable_fp_el1();
    enable_sve_el1();
    
    // Use double instead of float to match the ldr d0 instruction (64-bit)
    double b = 42.0;

    
__asm__ volatile (
    // Load scalar double
    "ldr d0, %0\n\t"       // load a into d0

    // Perform two FP operations
    "fadd d1, d0, d0\n\t"  // d1 = d0 + d0
    "fmul d2, d0, d0\n\t"  // d2 = d0 * d0
    :
    : "m"(b)               // input memory operand
    : "d0","d1","d2"       // clobbered FP registers
);




    
__asm__ volatile(
    // Load base address of array into x0
    "ldr x0, %0\n\t"

    // Activate lanes 0..3
    "mov x1, #4\n\t"
    "whilelo p0.s, xzr, x1\n\t"

    // Load vector
    "ld1w { z0.s }, p0/z, [x0]\n\t"

    // Do predicated operations (Zd is also the first src)
    "movprfx z1, z0\n\t"          // z1 = z0
    "add z1.s, p0/m, z1.s, z0.s\n\t"   // z1 = z1 + z0

    "movprfx z2, z0\n\t"          // z2 = z0
    "mul z2.s, p0/m, z2.s, z0.s\n\t"   // z2 = z2 * z0
    :
    : "m"(b)
    : "x0", "x1", "p0", "z0", "z1", "z2", "memory"
);




}

void c_entry() {
  printf_str("Start benchmark\n");
  test_sve();
  printf_str("Quit\n");
  qemu_exit(0);
}