all: vpsim-release/bin/vpsim vpsim-release/lib/qemu/vpsim-qemu.so

build/Makefile :
	mkdir build -p && cd build && cmake ..

vpsim-release/bin/vpsim vpsim-release/lib/qemu/vpsim-qemu.so : build/Makefile
	make -C build/

test : vpsim-release/bin/vpsim vpsim-release/lib/qemu/vpsim-qemu.so
	ctest --test-dir ./build --tests-regex vpsim[.] --output-on-failure
clean:
	rm -rf build/
