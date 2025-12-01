# Contents
- `/GPP/gpp.py`: Example of high-level configuration script for the ARMV8 General Purpose Processor with 4 cores.
- `/GPP/gpp_32.py`: Example of high-level configuration script for the ARMV8 General Purpose Processor with 32 cores.
- `/GPP/gpp_64.py`: Example of high-level configuration script for the ARMV8 General Purpose Processor with 64 cores.
- `/GPP/disk_images/*`: Virtual disk images. (Containing Debian Linux, etc.).
- `/GPP/linux/*`: Linux kernel images (64K Pages, SVE and device drivers).
- `/GPP/dt/gpp.dts.template`: Device tree template file, used by VPSim to generate the gpp's device tree for Linux.

# Architecture description
The full architecture is configured at a high level in the `gpp.py` script. We can use this configuration to create/modify components, change the memory map, load new images, etc.

Following is a description of the modelled architecture (`/GPP/gpp.py`):

- **CPU Cluster**
  - A generic configurable multicore ARMv8-A architecture with SVE and PMU support.

- **Configurable memory subsystem**
  - Coherent 3-level cache hierarchy
  - 2D-Mesh NoC with contention

**NOTE:** The configuration is a regular Python dictionary, so for larger architectures (e.g., 32 cores), it may be preferable to fill the configuration parameters in the 'conf' object programmatically before instantiating FullSystem (see `gpp.py`).

- **Peripherals**
  - PL011 UART
  - PL031 RTC
  - PCI
  - VirtIO block device (Busybox disk image: `busybox.qcow2`)
  - VirtIO network device (Host machine accessible via IP address `192.168.0.2`)

**NOTE:** This version of the GPP model assumes that processors run at 1Ghz with an IPC=1. Therefore, the absolute timings that are observed should in principle be larger than the real system.

# Software modes:
**NOTE:** In this first version, only one software mode is made available (others will come later on: full, custom)
- **Minimal mode**: Linux kernel 4.20.17 + Busybox (SVE support, 64K pages).
  - Run this mode for more accurate simulations, application profiling, benchmarking.
  - Edit `gpp.py` and set the `'software' -> 'mode'` parameter to `'minimal'`.
  - Run the `gpp.py` script:
    ```sh
    $ python3 gpp.py
    ```
  - Login as 'root' (no password).
  - To end the simulation, enter the following command in your simulated userspace:
    ```sh
    $ sesam quit
    ```

**NOTE:** Although this mode is minimalistic, it still supports various useful applications, such as 'wget', 'ssh', 'tar', 'nano', 'gdb', etc.

# Accessing the virtual platform via SSH
- While you can do everything from the main console, you may want to share a single GPP image among several users, or simply have a better and wider display. For these cases, you may want to access the GPP using SSH.

**NOTE:** This feature is disabled by default. To enable it, you need to decomment line 78 in `gpp.py`

- In `gpp.py`, port 22 of the guest Linux is forwarded to port 2222 on the host machine. You may change this port in `gpp.py`, by modifying the value of `conf -> 'net' -> 'hostfwd_ssh_port'`.
- To access the virtual platform by SSH, simply execute the following command from a new terminal:
  ```sh
  $ ssh root@localhost -p2222   # if using the minimal Busybox image, no password
  ```

# Benchmarking/profiling

1. **Using 'perf' program**:
   - Edit `gpp.py` and set the `'software' -> 'mode'` parameter to `'minimal'`.
   - Make sure `'memory_subsystem' -> 'simulate'` is set to `True`. This will simulate the entire memory subsystem and activate more PMU counters.
   - Run the `gpp.py` script:
     ```sh
     $ python3 gpp.py
     ```
   - Login as 'root' (no password).
   - Check the available performance counters:
     ```sh
     $ perf list
     ```
     (This should display statistics related to the cache hierarchy, which are provided by VPSim's cache models).
   - Use one of the provided benchmarks to run 'perf':
     ```sh
     $ cd STREAM
     $ perf stat -e cycles,instructions,armv8_pmuv3/cpu_cycles/ ./stream_c.sve436906
     ```
   - This should print the selected event statistics after executing the benchmark.
   - To end the simulation, enter the following command in your simulated userspace:
     ```sh
     $ sesam quit
     ```

2. **Using 'sesam' program**:
   - Alternatively, the image ships with a convenient 'sesam' program, which can be used to control the simulator directly from userspace.
   - To collect simulator-level statistics during the execution of a specific benchmark, call 'sesam' with the 'benchmark' command, as follows:
     ```sh
     $ sesam benchmark ./my_app
     ```
   - At the end of the program's execution, VPSim prints statistics from all the simulated components (Caches, NoC, CPUs, etc.)
     **NOTE:** Each time you run "sesam benchmark ./my_app", the resulted statistics captured during execution are automatically dumped to the host machine in the associated './bin/.<paltform_name>' directory
   - To end the simulation, enter the following command in your simulated userspace:
     ```sh
     $ sesam quit
     ```

# Loading files into the virtual platform
The host machine (PC running VPSim) is accessible from the virtual platform via address 192.168.0.2. Knowing this, you can transfer files from host machine to virtual platform and vice versa in several ways:
- Copying the files using SSH:
  (run on virtual platform)
  ```sh
  $ scp username@192.168.0.2:/my/file .
  ```
- Mounting a Network filesystem served by the host:
  (run on virtual platform)
  ```sh
  $ mount -t nfs 192.168.0.2:/srv/nfs/my_dir /mnt/my_libs
  ```
  **NOTE:** this requires an NFS server to be setup on your host machine. (https://help.ubuntu.com/community/SettingUpNFSHowTo#NFS_server)
