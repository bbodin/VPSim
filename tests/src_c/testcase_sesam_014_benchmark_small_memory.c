#include <sesam.h>

#include <sleep.h>
#include <printf.h>
#include <qemu.h>

void test_benchmark() {

    volatile int a = 10;        // two variables in the stack

    
    // Begin benchmark with a bench name
    sesam_reset_args();
    sesam_push_string("benchmark");
    sesam_push_string("small_memory");
    sesam_exec_params();

    
    __asm__ volatile (
        "mov x0, %0\n\t"
        "mov x1, %0\n\t"
        :
        : "r" (&a)      // input: address of a
        : "x0", "x1"    // clobbered registers
    );



    
    sesam_end_benchmark();     // opcode 0x54
}

void c_entry() {
  printf_str("Start benchmark\n");
  test_benchmark();
  printf_str("Quit\n");
  sesam_quit();
  qemu_exit(0);
}