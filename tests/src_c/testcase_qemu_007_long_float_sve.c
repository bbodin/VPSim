#include <printf.h>
#include <qemu.h>
#include <sve.h>
#include <stress.h>

void test_benchmark() {

    printf_str("call enable_fp_el1\n");
    enable_fp_el1();
    printf_str("call enable_sve_el1\n");
    enable_sve_el1();
    
    printf_str("call stress_fpu\n");
    stress_fpu(100000);
    printf_str("call small stress_sve\n");
    stress_sve(10);
    printf_str("call medium stress_sve\n");
    stress_sve(1000);
    printf_str("call large stress_sve\n");
    stress_sve(100000);

}

void c_entry() {
  printf_str("Start benchmark\n");
  test_benchmark();
  printf_str("Quit\n");
  qemu_exit(0);
}