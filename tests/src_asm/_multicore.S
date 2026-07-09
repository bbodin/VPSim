.global _Reset
    .section .vectors, "ax"
    .align 11
vector_table:
    // 16 entries spaced by 128 bytes (0x80)
    .rept 16
        b exception_handler
        .space 124
    .endr

    .text

_Reset:
    msr daifset, #0xf           // Disable interrupts

    // Set vector base address (VBAR_EL1)
    ldr x0, =vector_table
    msr VBAR_EL1, x0
    isb

    mrs x0, mpidr_el1           // Read MPIDR_EL1 (CPU id)
    and x0, x0, #0xff           // cpu_id in x0

    ldr x1, =stack_top          // Load top of the stack region (highest address)
    mov x2, #0x1000             // Stack size per core = 4KB

    add x3, x0, #1              // x3 = cpu_id + 1
    mul x3, x3, x2              // x3 = (cpu_id + 1) * 4KB
    sub sp, x1, x3              // sp = stack_top - (cpu_id + 1)*4KB

    bl c_entry                  // Jump to main C entry point
    b .                        // Loop forever

// Exception handler for synchronous exceptions
exception_handler:
    // Read ESR_EL1 into x0
    mrs x0, ESR_EL1

    // Extract EC (Exception Class): bits [31:26]
    ubfx x1, x0, #26, #6

    // Compare EC with 0x00 = Unknown reason (Undefined Instruction)
    cmp x1, #0x00
    b.ne handle_other_exception

    // call smc #0
    smc #0
    
    // Advance PC to skip faulting instruction
    mrs x2, ELR_EL1
    add x2, x2, #4            // Next instruction address
    msr ELR_EL1, x2

handle_other_exception:
    // Return from exception
    eret
