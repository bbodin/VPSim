import mmap
import os
import sys

# SESAM operation constants
SESAMOP = 0x00
SESAMOP_SHOW = 0x01
SESAMOP_QUIT = 0x42
SESAMOP_START_BENCH = 0x52
SESAMOP_END_BENCH = 0x54
SESAMOP_LIST = 0x20
SESAMOP_CLEAN_PARAMS = 0x58
SESAMOP_START_PARAM = 0x62
SESAMOP_END_PARAM = 0x72
SESAMOP_EXECUTE_PARAMS = 0x78

sesam_mem = None
fd = None

def map_sesam_mem():
    global sesam_mem, fd

    # Read configuration file
    try:
        with open("/etc/config_sesam", "r") as f:
            base_address_str = f.read().strip()
            if not base_address_str:
                raise ValueError("Config file is empty")
            base_address = int(base_address_str, 16)
    except Exception as e:
        print("Error while opening /etc/config_sesam:", e)
        print("Please type in your terminal 'echo [hex addr sesam_monitor] > /etc/config_sesam'")
        sys.exit(1)

    # Open /dev/mem
    try:
        fd = os.open("/dev/mem", os.O_RDWR | os.O_SYNC)
    except OSError as e:
        print("Error opening /dev/mem:", e)
        sys.exit(1)

    if base_address == 0:
        print("File /etc/config_sesam is empty or not in the right format")
        print("Please type in your terminal 'echo [hex addr sesam_monitor] > /etc/config_sesam'")
        sys.exit(1)

    # Memory-map 4 bytes at the base address
    try:
        sesam_mem = mmap.mmap(fd, 4, mmap.MAP_SHARED, mmap.PROT_READ | mmap.PROT_WRITE, offset=base_address)
    except Exception as e:
        print("mmap failed:", e)
        print("Please check the correct address in /etc/config_sesam")
        sys.exit(1)

def sesam_start():
    if not sesam_mem :
        map_sesam_mem()
    sesam_reset_args()
    sesam_push_string("start")
    sesam_exec_params()

def sesam_stop():
    sesam_reset_args()
    sesam_push_string("stop")
    sesam_exec_params()

def unmap_sesam():
    global sesam_mem, fd
    if sesam_mem:
        sesam_mem.close()
    if fd:
        os.close(fd)


# SESAM operation functions
def sesam_reset_args():
    if sesam_mem:
        sesam_mem[0] = SESAMOP_CLEAN_PARAMS


def sesam_exec_params():
    if sesam_mem:
        sesam_mem[0] = SESAMOP_EXECUTE_PARAMS


def sesam_start_benchmark():
    if sesam_mem:
        sesam_mem[0] = SESAMOP_START_BENCH


def sesam_end_benchmark():
    if sesam_mem:
        sesam_mem[0] = SESAMOP_END_BENCH


def sesam_list():
    if sesam_mem:
        sesam_mem[0] = SESAMOP_LIST


def sesam_quit():
    if sesam_mem:
        sesam_mem[0] = SESAMOP_QUIT


def sesam_push_string(string):
    if sesam_mem:
        sesam_mem[0] = SESAMOP_START_PARAM
        for c in string:
            sesam_mem[1] = ord(c)  # Write each character as a byte
        sesam_mem[0] = SESAMOP_END_PARAM


def sesam_snapshot(name):
    sesam_reset_args()
    sesam_push_string("snapshot")
    sesam_push_string(name)
    sesam_exec_params()


def sesam_start_bench_simple(name):
    sesam_reset_args()
    sesam_push_string(name)
    sesam_start_benchmark()


def sesam_end_bench_simple():
    sesam_end_benchmark()