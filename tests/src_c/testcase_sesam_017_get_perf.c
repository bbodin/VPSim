#include <sesam.h>

#include <stress.h>
#include <sleep.h>
#include <printf.h>
#include <qemu.h>
#include <string.h>

void test_get_perf() {

  
  sesam_reset_args();
  sesam_push_string("snapshot");
  sesam_push_string("snap_empty");
  sesam_exec_params();

  stress_memory(10000,10000);

  sesam_reset_args();
  sesam_push_string("get-perf");
  sesam_push_string("cpu_0");
  sesam_push_string("count_tlb_hit");
  sesam_exec_params();

  
  char buf[512];
  sesam_collect_output(buf, sizeof(buf));
  printf_str("We should received cpu_0.count_tlb_hit = .... :\n");
  printf_str(buf); // should be cpu_0.count_tlb_hit = ....



  stress_memory(10000,10000);

  sesam_reset_args();
  sesam_push_string("get-perf");
  sesam_push_string("cpu_0");
  sesam_push_string("count_tlb_hit");
  sesam_exec_params();

  sesam_reset_args();
  sesam_push_string("snapshot");
  sesam_push_string("snap_empty");
  sesam_exec_params();

  sesam_reset_args();
  sesam_push_string("get-perf");
  sesam_push_string("cpu_0");
  sesam_exec_params();

  stress_memory(10000,10000);

  
  sesam_reset_args();
  sesam_push_string("get-perf");
  sesam_push_string("timestamp");
  sesam_exec_params();

  printf_str("We received:\n");
  sesam_collect_output(buf, sizeof(buf));
  printf_str(buf); // should be timestamp = ..... ns

  stress_memory(10000,10000);
}

void c_entry() {
  printf_str("Start test_get_perf\n");
  test_get_perf();
  printf_str("Quit\n");
  sesam_quit();
  qemu_exit(0);
}