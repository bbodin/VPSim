#include <sesam.h>

#include <sleep.h>
#include <printf.h>
#include <qemu.h>
#include <sve.h>
#include <stress.h>

void test_benchmark() {
    // Check if SVE is supported before enabling
    if (!has_sve()) {
        printf_str("SVE not supported on this CPU, skipping SVE test\n");
        return;
    }

    enable_fp_el1();
    enable_sve_el1();
    

    sesam_start_bench_simple("long_float");
    stress_fpu(100000);

    sesam_end_benchmark();     // opcode 0x54


    sesam_start_bench_simple("long_sve");


 
    
    stress_sve(100000);



    sesam_end_benchmark();     // opcode 0x54



}

void c_entry() {
  printf_str("Start benchmark\n");
  test_benchmark();
  printf_str("Quit\n");
  sesam_quit();
  qemu_exit(0);
}