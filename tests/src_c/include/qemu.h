#ifndef  _QEMU_
#define _QEMU_

#include <stdint.h>

// Generic semihosting function
static inline void qemu_semihost(uint64_t syscall, uint64_t arg0, uint64_t arg1) {
    __asm__ volatile (
        "mov x1, %1\n"
        "str x1, [sp, #0]\n"
        "mov x1, %2\n"
        "str x1, [sp, #8]\n"
        "mov x0, %0\n"
        "hlt #0xf000\n"
        :
        : "r"(syscall), "r"(arg0), "r"(arg1)
        : "x0", "x1"
    );
}



static inline void qemu_exit(int status) {
    uint64_t reason = 0x20026; // ADP_Stopped_ApplicationExit
    qemu_semihost(0x20, reason, status); // SYS_EXIT_EXTENDED
}

#endif // _QEMU_