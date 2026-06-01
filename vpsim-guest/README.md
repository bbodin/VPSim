# SESAM userspace utility
This software tool communicates with the Monitor component and therefore also has full control over the simulator. In the second instance, the user space software tool is part of the executed software flow and has access to the simulated environment. Below is a list of the most useful commands within `sesam` command:
- `benchmark`: enter precise simulation mode to benchmark an application. When this mode is active, VPSim will simulate all memory accesses in a timed and more precise manner, making the simulation slower. Entering the Monitor again ends the benchmarking region and displays many statistics on the benchmark’s execution (Number of instructions, data accesses, bus accesses, cache misses, etc.).
- `show`: show the current status of a component in the platform.
- `quit`: quit the userspace and end simulation

# With the source code of this software, the user can customize this tool
- You can build sesam binary utility with simple `make`.
    - **NOTE:** You need an aarch64 gcc cross-compiler to build `sesam` that will be executed on ARM-based platform on the guest machine
- Replace /bin/sesam in userspace with the provided "sesam" binary.
- Type the following command once in userspace (should only be necessary with the 'minimal' image):
    ```sh
    $ echo 0x17000000 > /etc/config_sesam 
    ```
    - **NOTE**: 0x17000000 corresponds to the entry 'sesam_monitor_addr' configured in gpp.py script
    
- You should now be able to get the output of the benchmark command from the stdout of "sesam":
    ```sh
    $ sesam benchmark ./my_app > stats.txt
    ```
