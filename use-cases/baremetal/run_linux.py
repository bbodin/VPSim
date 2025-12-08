#!/usr/bin/env python3

"""
Copyright (C) 2024 Commissariat à l'énergie atomique et aux énergies alternatives (CEA)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0 

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import os
# Check if VPSIM_HOME is set
vpsim_home = os.environ.get("VPSIM_HOME")
if not vpsim_home:
    raise EnvironmentError("Environment variable VPSIM_HOME is not set.")
os.environ["VPSIM_PATH"] = f"{vpsim_home}/bin/vpsim"

import sys
sys.path.insert(0, f"{vpsim_home}/Python/Libs/")
sys.path.insert(0, f"{vpsim_home}/Python/Platforms/")




gpp_home = os.path.join(os.environ['VPSIM_HOME'], 'GPP')

def generate_conf(root, kernel, disk, outputdir, name) :

    local_conf = {
        'platform_name': 'RUN_LINUX_USECASE',
        'device_tree_template': os.path.join(gpp_home, 'dt', 'gpp.dts.template'),

        'cpu': {
            'cores': 4,
            'cores_per_cluster': 1,
            'gic': {
                'version': 3,
                'distributor_base': 0x1010000,
                'distributor_size': 0x10000,
                'redistributor_base': 0x1080000,
                'redistributor_size': 0x1000000,
            },
            'cpu_clusters': [
                # CPUs in cluster, NoC position (X,Y)
                ([0], (0,0)),
                ([1], (1,0)),
                ([2], (0,1)),
                ([3], (1,1)),
            ],
            'quantum': 65535,
            'conversion_factor': 3.0, # example: cpu_frequency = 3.0 GHz & IPC = 1
        },

        'ram': [
            {
                'base':   0x40000000,
                'size':  0x100000000
            }
        ],

        'uarts': [
            {
                'type': 'pl011',
                'name': 'uart0',
                'base': 0x08000000,
                'irq': 11
            }
        ],

        'block': [
            {
            'name': 'block0',
            'base': 0xa100000,
            'size': 0x1000,
            'irq': 40,
            'image': disk,
            },
        ],

        'net': [
            {
                'name': 'net0',
                'base': 0xa200000,
                'size': 0x1000,
                'irq': 42,
                'ip': '192.168.0.0/24',
                #'hostfwd_ssh_port': 2222, # Decomment this to Host-forward Port to access VM via SSH.
            },
        ],

        'rtc': {
            'base': 0xb000000,
            'size': 0x1000,
            'irq': 44
        },


        'software': {
        'mode': 'full', # minimal
        'rootfs' : {
            'path' :   root,
        },
        'dtb': {
            'path': os.path.join(gpp_home, 'dt', 'gpp.dtb'),
        },

        'kernel': {
            'path': kernel,
            'bootargs': 'console=ttyAMA0 earlycon root=/dev/vda1 uio_pdrv_genirq.of_id=generic-uio ip=dhcp',
        },

        'entry': None # Set this to entry PC when in custom mode.
        },

        'memory_subsystem': {
            'simulate': True,
            'focus_on_roi': True,
            'enable_coherence': True,
            'cache': {
                'l1-data': {
                    'size': 64*1024, # Bytes
                    'line-size': 64, # Bytes
                    'associativity': 4,
                    'latency-ns': 0,
                },
                'l1-instructions': {
                    'size': 64*1024, # Bytes
                    'line-size': 64, # Bytes
                    'associativity': 4,
                    'latency-ns': 0,
                },
                'l2': {
                    'size': 1024*1024, # Bytes
                    'line-size': 64, # Bytes
                    'associativity': 8,
                    'latency-ns': 1,
                    'inclusion-l1': 'NINE', # Can be Exclusive, Inclusive, or NINE
                },
                'l3': {
                    'line-size': 64, # Bytes
                    'associativity': 16, # Bytes
                    'latency-ns': 2,
                    'home-node-size': 2048*1024,
                    'inclusion-l2': 'Exclusive', # Can be Exclusive, Inclusive, or NINE

                    # SLC interleaving is enabled by default
                    # L3 cache line size is the default interleaving step
                    # interleave_step = 0 will disable SLC interleaving
                    'interleave_step' : 64,

                    'home-nodes': [
                        # Base address, size, NoC position (X,Y)
                        (0x40000000, 0x40000000, (0,0)),
                        (0x80000000, 0x40000000, (1,0)),
                        (0xc0000000, 0x40000000, (0,1)),
                        (0x100000000,0x40000000, (1,1)),
                    ],
                },
            },
            'noc': {
                'x-nodes': 2,
                'y-nodes': 2,
                'diagnosis' : False,
                'with-contention' : True,
                'contention-interval-ns' : 10,
                'buffer-size-flits' : 1,
                'flit-size': 8,
                'router-latency-ns': 0.34,
                'link-latency-ns': 0.34,
                'virtual-channels' : 1,
            },
            'off-chip-memory': {
                'read-latency-ns': 20,
                'write-latency-ns': 1,

                # Memory interleaving is enabled by default
                # The default memory interleave step is equal to L3 line size
                # interleave_step = 0 will disable Memory interleaving
                'interleave_step' : 64,

                # For now we only support the same width for all memories
                'channel-width': 16, # bytes
                'channels': 8,
                'memory-controllers': [
                    # base address, size, noc position
                    (0x40000000, 0x80000000, (0,0)),
                    (0xC0000000, 0x80000000, (1,0)),
                ],
            },
        },

        'monitoring' : {
            'sesam_monitor_addr': 0x17000000,
            'sesam_monitor_log_directory' : "./",
            'gdb_port': None,
            'vpsim_log_level' : None, # This is the log level of VPSIM
            'vpsim_stats_file' : None, # This is the location of any vpsim log file
            'qemu_execution_trace_file' : None # This is the location of the Qemu execution trace file
        }
    }
    
    
    # About log and log files
    local_conf['monitoring']['vpsim_log_level'] = "0"

    if outputdir and name :
        log_dir =   os.path.abspath(outputdir)
        trace_file =  log_dir  + "/" + name +  "_trace.log"
        stats_file =  log_dir  + "/" + name +  "_stats.log"

        local_conf['monitoring']['sesam_monitor_log_directory'] = log_dir
        local_conf['monitoring']['vpsim_stats_file'] = stats_file
        local_conf['monitoring']['qemu_execution_trace_file'] = trace_file
    else :
        local_conf['monitoring']['sesam_monitor_log_directory'] = "./"
        local_conf['monitoring']['qemu_execution_trace_file'] = None
        local_conf['monitoring']['vpsim_stats_file'] = None


    return local_conf

import argparse
import os
import sys

def validate_file(path: str, label: str) -> str:
    """Return absolute path if valid, else exit with an error."""
    abs_path = os.path.abspath(path)
    if not os.path.isfile(abs_path):
        print(f"Error: {label} file '{abs_path}' does not exist or is not a file.",
              file=sys.stderr)
        sys.exit(1)
    if not os.access(abs_path, os.R_OK):
        print(f"Error: {label} file '{abs_path}' is not readable.",
              file=sys.stderr)
        sys.exit(1)
    print(f"{label} file '{abs_path}' is valid.")
    return abs_path

def parse_arguments() -> dict:
    parser = argparse.ArgumentParser(description="Simulate a kernel + disk + boot ELF.")
    parser.add_argument('--kernel', required=True, help='Path to the kernel file')
    parser.add_argument('--root', required=True, help='Path to the root file')
    parser.add_argument('--disk',   required=True, help='Path to the disk image')
    parser.add_argument('--outputdir', required=False, help='Directory for output files')
    parser.add_argument('--name',      required=False, help='Prefix name for output files')

    args = parser.parse_args()

    # Validate all 3 required files
    root_file = validate_file(args.root, "Root")
    kernel_file = validate_file(args.kernel, "Kernel")
    disk_file   =  validate_file(args.disk,   "Disk")

    return {
        "root": root_file,
        "kernel": kernel_file,
        "disk": disk_file,
        "outputdir": args.outputdir,
        "name": args.name
    }



if __name__ == '__main__':

    arguments = parse_arguments ()
    
    conf = generate_conf(**arguments)


        

    from armv8_platform import FullSystem
    sys = FullSystem(conf)
    # Run simulation
    _ = sys.build(simulate=True,wait=True,silent=False,)