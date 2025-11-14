all: vpsim-release/bin/vpsim vpsim-release/lib/qemu/vpsim-qemu.so

build/Makefile :
	mkdir build -p && cd build && cmake ..

vpsim-release/bin/vpsim vpsim-release/lib/qemu/vpsim-qemu.so : build/Makefile
	make -C build/

test :
	ctest --test-dir ./build/vpsim-build/ -R vpsim[.] 
	ctest --test-dir ./build/tests/ -R vpsim[.] 

clean:
	rm -rf build/
