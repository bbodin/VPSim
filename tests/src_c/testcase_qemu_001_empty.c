#include "qemu.h"

void test_empty() {
    return;
}

void c_entry() {
  test_empty();
  qemu_exit(0);
}
