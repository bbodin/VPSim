RELEASE_DIR=./vpsim-release/

.PHONY: release debug
release: release/vpsim-release/bin/vpsim release/vpsim-release/lib/qemu/vpsim-qemu.so
debug: debug/vpsim-release/bin/vpsim debug/vpsim-release/lib/qemu/vpsim-qemu.so


debug/Makefile : CMakeLists.txt
	mkdir debug -p && cd debug && cmake .. -DCMAKE_BUILD_TYPE=Debug

release/Makefile : CMakeLists.txt
	mkdir release -p && cd release && cmake .. 

%/vpsim-release/bin/vpsim : %/Makefile
	make -C $*/ install_vpsim
	
%/vpsim-release/lib/qemu/vpsim-qemu.so : %/Makefile
	make -C $*/ install_qemu

test : debug/Makefile
	make -C debug/ 
	ctest --test-dir ./debug --tests-regex vpsim[.]unittest 
	ctest --test-dir ./debug --tests-regex vpsim[.]run_simple 

clean:
	rm -rf build/ debug/ release/ vpsim-release/bin/* vpsim-release/lib/*
