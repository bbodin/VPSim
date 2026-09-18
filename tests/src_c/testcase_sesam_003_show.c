#include <sesam.h>
#include <printf.h>
#include <qemu.h>


void test_show_cpu0() {
    sesam_reset_args();
    sesam_push_string("show");
    sesam_push_string("cpu_0");
    sesam_exec_params();

}

void test_show_uart0() {
    sesam_reset_args();
    sesam_push_string("show");
    sesam_push_string("uart0");
    sesam_exec_params();

}

void c_entry() {
  printf_str("Run show CPU0\n");
  test_show_cpu0();
  printf_str("Run show UART0\n");
  test_show_uart0();
  printf_str("Quit\n");
  sesam_quit();
  qemu_exit(0);
}