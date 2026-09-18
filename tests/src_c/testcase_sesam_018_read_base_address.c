#include <sesam.h>

#include <stress.h>
#include <sleep.h>
#include <printf.h>
#include <qemu.h>

void test_read_base_address() {
 uint8_t val = sesam_mem[0];

    if (val == 42) {
        printf_str("SESAM value is correct (42)\n");
    } else {
        printf_str("SESAM value mismatch: got ");
        printf_hex(val);
        printf_str(", expected 2A\n");
    }

}

void c_entry() {
  printf_str("Start test_read_base_address\n");
  test_read_base_address();
  printf_str("Quit\n");
  sesam_quit();
  qemu_exit(0);
}