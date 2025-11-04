build/Makefile :
	mkdir build -p && cd build && cmake ..

all : build/Makefile
	make -C build/