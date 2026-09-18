#include <sesam.h>

#include <sleep.h>
#include <printf.h>
#include <qemu.h>
#include <stress.h>

void test_benchmark() {

    // Begin benchmark with a bench name
    sesam_reset_args();
    sesam_push_string("benchmark");
    sesam_push_string("myBench_10000");
    sesam_exec_params();
    stress_memory(10000,10000);
    sesam_end_benchmark();     // opcode 0x54
}

void c_entry() {
  printf_str("Start benchmark\n");
  test_benchmark();
  printf_str("Quit\n");
  sesam_quit();
  qemu_exit(0);
}