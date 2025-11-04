build/Makefile :
	mkdir build -p && cd build && cmake ..

vpsim-release/bin/vpsim vpsim-release/lib/qemu/vpsim-qemu.so : build/Makefile
	make -C build/