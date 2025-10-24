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

gpp_home = os.path.join(os.environ['VPSIM_HOME'], 'GPP')

conf = {
    'platform_name': 'GPP_VP',
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
            'base': 0x09000000,
            'irq': 11
        }
    ],

    'net': [
        {
            'name': 'net0',
            'base': 0xa200000,
            'size': 0x1000,
            'irq': 42,
            'ip': '192.168.0.0/24',
        },
    ],

    'rtc': {
        'base': 0xb000000,
        'size': 0x1000,
        'irq': 44
    },

    'sesam_monitor_addr': 0x17000000,

    'software': {
       'mode': 'minimal',

       'kernel': {
           'path': os.path.join(os.path.dirname(os.path.abspath(__file__)),"kernel_hello_world.elf"),
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

    'gdb_port': None,
}


import argparse
import sys

default_image = os.path.join(os.path.dirname(os.path.abspath(__file__)),"kernel_hello_world.elf")

def parse_arguments() -> dict:
    parser = argparse.ArgumentParser(description="Process an image and optionally a debug file.")
    parser.add_argument('--image', required=False, help='Path to the image file')
    parser.add_argument('--debug', required=False, help='Path to the debug file')

    args = parser.parse_args()

    image_file = os.path.abspath(args.image) if args.image else default_image
    debug_file = os.path.abspath(args.debug)  if args.debug else None

    if image_file :
        if not os.path.isfile(image_file):
            print(f"Error: Image file '{image_file}' does not exist or is not a file.", file=sys.stderr)
            sys.exit(1)
        if not os.access(image_file, os.R_OK):
            print(f"Error: Image file '{image_file}' is not readable.", file=sys.stderr)
            sys.exit(1)
        print(f"Image file '{image_file}' is valid.")

    return {"image": image_file, "debug": debug_file}

def print_stats_table(data, *, path_sep="/", missing="–"):
    """
    Pretty-prints a nested-dict of segments as an ASCII table.
    - Columns = top-level segments (e.g., 'globalLog', 'another', ...)
    - Rows    = metric paths found anywhere under each segment
               (e.g., 'cpu_0/executed_instructions', 'dcacheL1_0/hits', ...)

    Values are expected to be either:
      • dict (recurse), or
      • tuples like (value, unit) where unit may be ''.

    Parameters
    ----------
    data : dict
        Top-level mapping: {segment_name: segment_dict, ...}
    path_sep : str
        Separator used when joining nested keys into a metric path.
    missing : str
        Placeholder for missing cells.

    Notes
    -----
    - Preserves key order where possible (Python 3.7+ dicts keep insertion order).
    - Formats tuple values as "value unit" (unit omitted if empty).
    """
    from math import isfinite

    def _is_leaf(x):
        return not isinstance(x, dict)

    def _fmt_value(v):
        if isinstance(v, tuple) and len(v) == 2:
            val, unit = v
            # format numbers nicely; leave others as-is
            if isinstance(val, float):
                # keep reasonable precision without trailing zeros
                s = f"{val:.6g}"
            else:
                s = str(val)
            return f"{s} {unit}".rstrip()
        # Fallback: stringify
        return str(v)

    def _flatten(dct, prefix=""):
        rows = []
        for k, v in dct.items():
            key = f"{prefix}{path_sep}{k}" if prefix else k
            if isinstance(v, dict):
                rows.extend(_flatten(v, key))
            else:
                rows.append((key, v))
        return rows

    # 1) Collect column names (segments) in insertion order
    segments = list(data.keys())

    # 2) For each segment, flatten to {metric_path: value}
    seg_maps = []
    for seg in segments:
        segval = data.get(seg, {})
        if isinstance(segval, dict):
            flat = _flatten(segval)
        else:
            # if not a dict, treat the segment itself as a single leaf
            flat = [(seg, segval)]
        seg_maps.append({k: v for k, v in flat})

    # 3) Compute unified ordered list of metric paths.
    #    Start with the first segment's order, then append unseen keys from others in their order.
    seen = set()
    row_keys = []
    for sm in seg_maps:
        for k in sm.keys():
            if k not in seen:
                seen.add(k)
                row_keys.append(k)

    # 4) Build a 2D table: header + rows
    header = ["Metric"] + segments

    # Convert cell values to strings (formatted); fill missing
    rows = []
    for rk in row_keys:
        row = [rk]
        for sm in seg_maps:
            val = sm.get(rk, None)
            row.append(_fmt_value(val) if val is not None else missing)
        rows.append(row)

    # 5) Compute column widths
    col_widths = [0] * len(header)
    for ci, h in enumerate(header):
        col_widths[ci] = max(col_widths[ci], len(h))
    for r in rows:
        for ci, cell in enumerate(r):
            col_widths[ci] = max(col_widths[ci], len(str(cell)))

    # 6) Helpers to render lines
    def hline(ch="-", cross="+"):
        parts = [cross]
        for w in col_widths:
            parts.append(ch * (w + 2))
            parts.append(cross)
        return "".join(parts)

    def fmt_row(vals):
        cells = []
        for ci, v in enumerate(vals):
            s = str(v)
            pad = col_widths[ci] - len(s)
            cells.append(f" {s}{' ' * pad} ")
        return "|" + "|".join(cells) + "|"

    # 7) Render table
    print(hline("-","+") )
    print(fmt_row(header))
    print(hline("=","+") )
    for r in rows:
        print(fmt_row(r))
    print(hline("-","+") )


if __name__ == '__main__':

    arguments = parse_arguments ()

    conf["software"]["kernel"]["path"] = os.path.abspath(arguments["image"])
    conf["log_dir"] = os.path.abspath(".")
    if arguments["debug"] :
        conf["log_file"] = os.path.abspath(arguments["debug"])
        conf["log_execution"] = True
    else :
        conf["log_execution"] = False

    from armv8_platform import FullSystem
    sys = FullSystem(conf)
    stats = sys.build(simulate=True,wait=True,silent=False,)
    from pprint import pprint
    print_stats_table(stats)