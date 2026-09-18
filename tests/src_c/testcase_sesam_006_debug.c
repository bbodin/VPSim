#include <sesam.h>
#include <qemu.h>


void test_sdebug() {

    sesam_reset_args();            // opcode 0x58
    sesam_push_string("debug");    // "debug"
    sesam_push_string("1");        // lvl
    sesam_push_string("cpu_1");     // component
    sesam_exec_params();           // opcode 0x78
}

void test_sdebug_multi() {

    sesam_reset_args();
    sesam_push_string("debug");
    sesam_push_string("2");        
    sesam_push_string("system_bus");     
    sesam_push_string("cpu_0");      
    sesam_push_string("network");  // This one does not exist 
    sesam_exec_params();
}


void c_entry() {
  test_sdebug();
  test_sdebug_multi();
  sesam_quit();
  qemu_exit(0);
}