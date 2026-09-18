#include <sesam.h>
#include <qemu.h>

void test_quit() {
    sesam_quit();  // 0x42
}

void c_entry() {
  test_quit();
  qemu_exit(0);
}