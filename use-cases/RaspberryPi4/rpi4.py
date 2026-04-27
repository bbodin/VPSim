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

from SimpleSystem import SimpleSystem

current_folder = os.path.join(os.path.dirname(__file__))
gpp_home = os.path.join(os.path.dirname(__file__), "..", 'GPP')
log_dir = current_folder


conf = {
    "platform_name": "RPI4",
    'device_tree_template': os.path.join(current_folder, 'default.dts.template'),
    "log_level" : 1,

    "cpu": {
        "cores": 2,
        "quantum": 1000,
        "conversion_factor": 3.0,
        "qemu_lib" : f"{vpsim_home}/lib/qemu/vpsim-qemu.so",
        "reset_pc" : 0x40000000, # memory base
    },

    "software": {
        'dtb': {
            'path': os.path.join(current_folder,  'default.dtb'),
        },

        "kernel": {
           'path': os.path.join(gpp_home, 'linux', 'linux-6.1.44'),
           'bootargs': 'console=ttyAMA0 earlycon root=/dev/vda uio_pdrv_genirq.of_id=generic-uio ip=dhcp',
        },
        "trace_file":  os.path.join(log_dir, 'trace.log'),
    },

    "monitoring": {
        "log_dir":  log_dir, # will be defined later
        "stats_file":  os.path.join(log_dir, 'stats.log'), # will be defined later
    },



    'gic': {
            'version': 3,
            'distributor_base': 0x1010000,
            'distributor_size': 0x10000,
            'redistributor_base': 0x1080000,
            'redistributor_size': 0x1000000,
            "irq_base": 0x0,
        },

    "devices": {
        "uart0": {"model": "pl011", "base":  0x08000000, "size": 0x1000, "irq": 11},
        "net0": {"model": "virtio-mmio", "base":  0xa200000, "size": 0x1000, "irq": 42},
        "rtc": {"model": "pl031", "base": 0xb000000, "size": 0x1000, "irq": 44},
        "pcie": {"model": "pcie", "base": 0x10000000, "size": 0, "irq": 3},




    },

    'blocks': [
        {
           'name': 'block0',
           'base': 0xa100000,
           'size': 0x1000,
           'irq': 40,
           'image': os.path.join(gpp_home, 'disk_images', "busybox.qcow2"),
      }
      ],
    


    "cache": {

        "l1i": {
                'size': 48*1024,
                'line-size': 64,
                'associativity': 3,
                'latency-ns': 1,
            },

        "l1d": {
                'size': 32*1024,
                'line-size': 64,
                'associativity': 2,
                'latency-ns': 1,
            },
        "l2": {
                'size': 1024*1024,
                'line-size': 64,
                'associativity': 16,
                'latency-ns': 10,
                'inclusion-l1': 'Inclusive',
            },
    },
    "memory": {
        "base": 0x40000000,
        "size": 0x100000000,
        'read-latency-cycles': 100,
        'write-latency-cycles': 30,
        'interleave_step': 64,
        'channel-width': 16,
        'channels': 1,
    }
}

if __name__ == '__main__':
    # Build the config
    sys = SimpleSystem(conf)
    # Run simulation
    _ = sys.build(simulate=True,wait=True,silent=False,)