#include <sesam.h>
#include <printf.h>
#include <qemu.h>


// Bare-metal version of test_showmem
void test_showmem() {

    unsigned int a = 2964369584;

    char addr_str[20];
    char size_str[12];

    ptr_to_hex(&a, addr_str);
    itoa_dec(sizeof(a), size_str);

    printf_str("Showmem call with ");
    printf_str(addr_str);
    printf_str(" ");
    printf_str(size_str);
    printf_str("\n");

    sesam_reset_args();
    sesam_push_string("showmem");
    sesam_push_string(addr_str);   // address of a
    sesam_push_string(size_str);   // size of a
    sesam_exec_params();
}


void c_entry() {
  printf_str("Test SHOWMEM\n");
  test_showmem();
  printf_str("Quit\n");
  sesam_quit();
  qemu_exit(0);
}