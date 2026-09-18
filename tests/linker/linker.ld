ENTRY(_Reset)
SECTIONS
{
	. = 0x40000000;
	.start . : { *(.start) }
	.text : { *(.text) }
	.data : { *(.data) }
	.bss : { *(.bss COMMON) }
	. = ALIGN(8);
	. = . + 0x200000; /* 512KB = 128 * 4KB stack size */
	stack_top = .;

	/* SESAM memory - 4KB region */
	. = ALIGN(8);
	sesam_mem = .;
	. += 4096;

}
