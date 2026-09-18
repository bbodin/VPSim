#include <sesam.h>

#include <stress.h>
#include <sleep.h>
#include <printf.h>
#include <qemu.h>

void test_snapshot() {

    // Do snapshot
    sesam_reset_args();
    sesam_push_string("snapshot");
    sesam_push_string("snap_empty");
    sesam_exec_params();

  stress_memory(100,100);

        // Do snapshot
    sesam_reset_args();
    sesam_push_string("snapshot");
    sesam_push_string("snap_100_100");
    sesam_exec_params();

    
  stress_memory(0,100);

        // Do snapshot
    sesam_reset_args();
    sesam_push_string("snapshot");
    sesam_push_string("snap_100_200");
    sesam_exec_params();

  stress_memory(100,100);

        // Do snapshot
    sesam_reset_args();
    sesam_push_string("snapshot");
    sesam_push_string("snap_200_300");
    sesam_exec_params();


}

void c_entry() {
  printf_str("Start snapshot test\n");
  test_snapshot();
  printf_str("Quit\n");
  sesam_quit();
  qemu_exit(0);
}