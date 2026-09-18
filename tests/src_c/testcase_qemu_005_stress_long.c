#include <stress.h>
#include <printf.h>
#include <qemu.h>

void test_stress_long() {


  stress_memory(100000,100000);

  stress_memory(0,100000);

  stress_memory(100000,100000);


}

void c_entry() {
  printf_str("Start stress test\n");
  test_stress_long();
  printf_str("Quit\n");
  qemu_exit(0);
}