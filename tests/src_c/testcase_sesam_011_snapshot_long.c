#include <sesam.h>

#include <stress.h>
#include <sleep.h>
#include <printf.h>
#include <qemu.h>

void test_snapshot() {


  stress_memory(100000,100000);

        // Do snapshot
    sesam_reset_args();
    sesam_push_string("snapshot");
    sesam_push_string("snap_100000_100000");
    sesam_exec_params();

    
  stress_memory(0,100000);

        // Do snapshot
    sesam_reset_args();
    sesam_push_string("snapshot");
    sesam_push_string("snap_100000_200000");
    sesam_exec_params();

  stress_memory(100000,100000);

        // Do snapshot
    sesam_reset_args();
    sesam_push_string("snapshot");
    sesam_push_string("snap_200000_300000");
    sesam_exec_params();


}

void c_entry() {
  printf_str("Start snapshot test\n");
  test_snapshot();
  printf_str("Quit\n");
  sesam_quit();
  qemu_exit(0);
}