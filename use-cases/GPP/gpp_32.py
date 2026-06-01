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

from armv8_platform import FullSystem

gpp_home = os.path.join(os.path.dirname(__file__), "..", 'GPP')

conf = {
    'platform_name': 'GPP_32_USECASE',
    'device_tree_template': os.path.join(gpp_home, 'dt', 'gpp.dts.template'),

    'cpu': {
        'cores': 32,
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
            # Filled automatically hereafter (lines 180-191)
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
           'image': os.path.join(gpp_home, 'disk_images', "busybox.qcow2"),
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
       'mode': 'minimal',
       'dtb': {
           'path': os.path.join(gpp_home, 'dt', 'gpp.dtb'),
       },
       'kernel': {
           'path': os.path.join(gpp_home, 'linux', 'linux-6.1.44'),
           'bootargs': 'console=ttyAMA0 earlycon root=/dev/vda uio_pdrv_genirq.of_id=generic-uio ip=dhcp',
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
                'latency-ns': 4, # f = 1.5 GHz
                'inclusion-l1': 'NINE', # Can be Exclusive, Inclusive, or NINE
            },
            'l3': {
                'line-size': 64, # Bytes
                'associativity': 16, # Bytes
                'latency-ns': 10,
                'home-node-size': 2048*1024,
                'inclusion-l2': 'Exclusive', # Can be Exclusive, Inclusive, or NINE

                # SLC interleaving is enabled by default
                # L3 cache line size is the default interleaving step
                # interleave_step = 0 will disable SLC interleaving
                'interleave_step' : 64,

                'home-nodes': [
                    # Base address, size, NoC position (X,Y)
                    # Filled automatically hereafter (lines 194-214)
                ],
            },
        },
        'noc': {
            'x-nodes': 6,
            'y-nodes': 6,
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
                (0x40000000, 0x40000000, (2,0)),
                (0x80000000, 0x40000000, (3,0)),
                (0xC0000000, 0x40000000, (2,5)),
                (0x100000000, 0x40000000, (3,5)),
            ],
        },
        'IODevs': [
            {
                'name' : 'nvme0',
                'x-pos': 0,
                'y-pos': 1,
            },
            {
                'name' : 'nvme1',
                'x-pos': 0,
                'y-pos': 2,
            },
        ],
    },

    'monitoring' : {
        'sesam_monitor_addr': 0x17000000,
        'sesam_monitor_log_directory' : "./",
        'gdb_port': None,
        'vpsim_log_level' : 3, # This is the log level of VPSIM
        'vpsim_stats_file' : None, # This is the location of any vpsim log file
        'qemu_execution_trace_file' : None # This is the location of the Qemu execution trace file
    }
}

if __name__ == '__main__':

    # Filling the clusters
    x_nodes = conf['memory_subsystem']['noc']['x-nodes']
    y_nodes = conf['memory_subsystem']['noc']['y-nodes']
    cpu_id = 0

    for i in range(x_nodes):
        for j in range(y_nodes):
            if (i==0 and j==0) or (i==0 and j==5) or (i==5 and j==0) or (i==5
                    and j==5):
                continue
            if cpu_id < conf['cpu']['cores']:
                conf['cpu']['cpu_clusters'].append( ([cpu_id], (i, j)) )
                cpu_id += 1

    # Filling the home nodes
    n_cores = conf['cpu']['cores']
    hn_cores = 32
    total_ram_size = conf['ram'][0]['size']
    ram_base = conf['ram'][0]['base']
    hn_addr = ram_base
    hn_size = total_ram_size // hn_cores
    hn_list = conf['memory_subsystem']['cache']['l3']['home-nodes']

    for i in range(x_nodes):
        for j in range(y_nodes):
            if (i==0 and j==0) or (i==0 and j==5) or (i==5 and j==0) or (i==5
                    and j==5):
                continue
            if total_ram_size >= hn_size:
                hn_list.append( (hn_addr, hn_size, (i,j)) )
                hn_addr += hn_size
                total_ram_size -= hn_size

    # assign remaining address slice to first HN
    bs, sz, node = hn_list[-1]
    hn_list[-1] = (bs, sz + total_ram_size, node)

    # Build the config
    sys = FullSystem(conf)
    # Run simulation
    _ = sys.build(simulate=True,wait=True,silent=False,)