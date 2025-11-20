all: vpsim-release/bin/vpsim vpsim-release/lib/qemu/vpsim-qemu.so

build/Makefile :
	mkdir build -p && cd build && cmake ..

.PHONY : systemc
systemc : build/Makefile
	cmake --build build/ --target vpsim

	
.PHONY : qemu
qemu : build/Makefile
	cmake --build build/ --target qemu

vpsim-release/bin/vpsim vpsim-release/lib/qemu/vpsim-qemu.so : build/Makefile
	make -C build/


test : vpsim-release/bin/vpsim vpsim-release/lib/qemu/vpsim-qemu.so
	ctest --test-dir ./build --tests-regex vpsim[.] --output-on-failure
clean:
	rm -rf build/
