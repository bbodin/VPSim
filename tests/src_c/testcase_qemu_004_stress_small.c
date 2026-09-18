#include <stress.h>
#include <printf.h>
#include <qemu.h>

void test_stress_small() {


  stress_memory(100,100);

  stress_memory(0,100);

  stress_memory(100,100);


}

void c_entry() {
  printf_str("Start stress test\n");
  test_stress_small();
  printf_str("Quit\n");
  qemu_exit(0);
}