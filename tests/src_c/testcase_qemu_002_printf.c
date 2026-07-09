#include "qemu.h"
#include "printf.h"

void test_printf_str() {
    printf_str("Hello World\n");  
  return;
}

void c_entry() {
  test_printf_str();
  qemu_exit(0);
}
