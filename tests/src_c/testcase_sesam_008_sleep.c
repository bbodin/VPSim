#include <sesam.h>

#include <sleep.h>
#include <printf.h>
#include <qemu.h>



void c_entry() {
  unsigned long COUNT = 10;
  unsigned long start_vct[COUNT], start_pct[COUNT];
  for (unsigned long i = 0 ; i < COUNT ; i++) {
    start_vct[i] =  read_cntvct();
    start_pct[i] =  read_cntpct();
  }

  unsigned long freq  = read_cntfrq();

  printf_str("read_cntvct returns: ");
  for (unsigned long i = 0 ; i < COUNT ; i++) {
   print_uint(start_vct[i]);
   printf_str(" ");
  }
  printf_str("\n");

    printf_str("read_cntpct returns: ");
  for (unsigned long i = 0 ; i < COUNT ; i++) {
   print_uint(start_pct[i]);
   printf_str(" ");
  }
  printf_str("\n");


  printf_str("read_cntfrq returns: ");
  print_uint(freq);
  printf_str("\n");

  //printf_str("Sleep for 1 sec\n");
  //sleep_s(1);
  printf_str("Sleep for 10 ms\n");
  sleep_ms(10);
  printf_str("Sleep for 20 ms\n");
  sleep_ms(20);
  printf_str("Quit, sc_simulation_time should be around 30,000,000 ns\n");
  sesam_quit();
  qemu_exit(0);
}