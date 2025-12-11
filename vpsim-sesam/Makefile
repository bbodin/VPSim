CROSS_COMPILE?=aarch64-linux-gnu-
CC=$(CROSS_COMPILE)g++

CFLAGS=-Wall
INCS += 

MODULE=sesam
OBJ=sesam.o sesam_mmap.o

all : $(MODULE)

%.o: %.cpp
	$(CC) -c -o $(INCS) $@ $< $(CFLAGS)

$(MODULE) : $(OBJ)
	$(CC) -o $@ $^ $(CFLAGS)
	rm *.o

clean :
	rm -rf $(MODULE)
