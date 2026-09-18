#include <sesam.h>
#include <printf.h>
#include <stdbool.h>
#include <qemu.h>
// TODO : This test fails in Qemu obviously ...

void test_list() {
    // Execute the list command
    sesam_reset_args();
    sesam_push_string("list");
    sesam_exec_params();

    // Read back the output from the controller
    char c;
    int index = 0;
    printf_str("List of IPs:\n");
    while (true) {
        c = sesam_mem[1];  // reading from base+1, where read() returns mCommandOutputBuffer
        if (c == 0) break; // stop at null terminator (or empty buffer)
        printf_char(c);
        index++;
    }
    printf_str("\nEnd of list.\n");
}

void c_entry() {
  test_list();
  sesam_quit();
  qemu_exit(0);
}