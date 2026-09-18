#include <sesam.h>
#include <printf.h>
#include <qemu.h>


void test_configure() {
    sesam_reset_args();
    sesam_push_string("configure");
    sesam_push_string("domain0");
    sesam_push_string("fast_mode");
    sesam_exec_params();
}

void c_entry() {
  
  printf_str("Test CONFIGURE\n");
  test_configure();
  printf_str("Quit\n");
  sesam_quit();
  qemu_exit(0);
}