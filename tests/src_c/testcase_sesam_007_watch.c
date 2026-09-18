#include <sesam.h>
#include <printf.h>
#include <qemu.h>


void test_watch() {
    unsigned int dummy_var;
    char base_str[20];
    char size_str[12];

    ptr_to_hex(&dummy_var, base_str);  // convert pointer to hex string
    itoa_dec(sizeof(dummy_var), size_str); // convert size to string

    // Watch
    
    printf_str("Send watch\n");
    sesam_reset_args();
    sesam_push_string("watch");
    sesam_push_string(base_str);
    sesam_push_string(size_str);
    sesam_exec_params();

    dummy_var = 1;

    // Unwatch
    printf_str("Send unwatch\n");
    sesam_reset_args();
    sesam_push_string("unwatch");
    sesam_push_string(base_str);
    sesam_push_string(size_str);
    sesam_exec_params();
}

void c_entry() {
  printf_str("Run WATCH test\n");
  test_watch();
  printf_str("Quit\n");
  sesam_quit();
  qemu_exit(0);
}