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

class DevTree(object):
    def __init__(self, name, template):
        self.name = name
        self.dt = {'cluster':[],'cpu':[],'dev':[],'top':[]}
        if template[- len('.dts.template'):]!='.dts.template':
          raise Exception("DTS template should have a .dts.template extension.")
        with open(template) as inDt:
            self.templ=inDt.read()
        self.templName=template
    def make(self):
        outB=self.templName[: - len('.dts.template')]
        outS = outB + '.dts'
        outB += '.dtb'
        dt=self.dt
        devtree=self.templ%(
            self.name,
            "\n".join(dt['cluster']),
            "\n".join(dt['cpu']),
            "\n".join(dt['dev']),
            "\n".join(dt['top']))
        with open(outS,'w') as dtsf:
            dtsf.write(devtree)
        os.system('dtc -q -Idts -Odtb -o %s %s'% (outB,outS))
    def getref(self):
        return self.dt

def _g(val):
   if type(val)==str:
       return int(val,16)
   return val

def c_arm64(conf, dt):
    for cluster_index, cluster_node in enumerate(conf['cpu_clusters']):
        cores_ids= cluster_node[0]
        dt['cluster'].append("""
            cluster%s {""" % (cluster_index))
        for core_per_clus, cpu in enumerate(cores_ids):
            dt['cluster'].append(
                """\t\t\t\tcore%s {
                    cpu = <&cpu%s>;
                };""" % (core_per_clus, cpu))
        dt['cluster'].append("""\t\t\t};""")
    for i in range(conf['cores']):
        dt['cpu'].append("""
        cpu%s: cpu@%s {
            compatible = "arm,armv8";
            reg = <%s>;
            device_type = "cpu";
            enable-method = "psci";
            clocks = <0x1 0x0 0x0>;
        };""" % (i,i,i if i < 0x10 else 0x100*(i//0x10)+(i-0x10*(i//0x10))))
    dt['top'].append("""
    timer {
        compatible = "arm,armv8-timer";
        interrupts = <0x1 0xd 0xf08 0x1 0xe 0xf08 0x1 0xb 0xf08 0x1 0xa 0xf08>;
        interrupt-parent=<0x2>;
    };
    """)
    if conf['gic'] == 'v2':
        dt['dev'].append("""
        interrupt-controller@%s {
            compatible = "arm,cortex-a15-gic";
            #interrupt-cells = <0x3>;
            #address-cells = <0x0>;
            interrupt-controller;
            reg = <%s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s>;
            interrupts = <0x1 0x9 0xff04>;
            clocks = <0x1 0x1 0x198>;
            clock-names = "clk";
            phandle = <0x2>;
        };
        """%(hex(conf['distributor_base'])[2:],
            hex(_g(conf['distributor_base'])>>32),
            hex(_g(conf['distributor_base'])&0xFFFFFFFF),

            hex(_g(conf['distributor_size'])>>32),
            hex(_g(conf['distributor_size'])&0xFFFFFFFF),

            hex(_g(conf['cpu_if_base'])>>32),
            hex(_g(conf['cpu_if_base'])&0xFFFFFFFF),

            hex(_g(conf['cpu_if_size'])>>32),
            hex(_g(conf['cpu_if_size'])&0xFFFFFFFF),

            hex(_g(conf['vctrl_base'])>>32),
            hex(_g(conf['vctrl_base'])&0xFFFFFFFF),

            hex(_g(conf['vctrl_size'])>>32),
            hex(_g(conf['vctrl_size'])&0xFFFFFFFF),

            hex(_g(conf['vcpu_base'])>>32),
            hex(_g(conf['vcpu_base'])&0xFFFFFFFF),

            hex(_g(conf['vcpu_size'])>>32),
            hex(_g(conf['vcpu_size'])&0xFFFFFFFF),

        ))

    else:

        dt['dev'].append("""
        gic: interrupt-controller@%s {
            compatible = "arm,gic-v3";
            #interrupt-cells = <0x3>;
            #address-cells = <2>;
            #size-cells = <2>;
            interrupt-controller;
            reg = <%s %s %s %s>,
                    <%s %s %s %s>;
            interrupts = <0x1 0x9 0xff04>;
            clocks = <0x1 0x1 0x198>;
            clock-names = "clk";
            phandle = <0x2>;
            its: gic-its@9510000 {
                compatible = "arm,gic-v3-its";
                msi-controller;
                reg = <%s %s 0 0x200000>;
                phandle = <0x90>;
            };
        };
        """%(hex(conf['distributor_base'])[2:],
             hex(_g(conf['distributor_base'])>>32),
             hex(_g(conf['distributor_base'])&0xFFFFFFFF),

             hex(_g(conf['distributor_size'])>>32),
             hex(_g(conf['distributor_size'])&0xFFFFFFFF),

             hex(_g(conf['redistributor_base'])>>32),
             hex(_g(conf['redistributor_base'])&0xFFFFFFFF),

             hex(_g(conf['redistributor_size'])>>32),
             hex(_g(conf['redistributor_size'])&0xFFFFFFFF),

             hex((_g(conf['distributor_base'])+0x500000)>>32),
             hex((_g(conf['distributor_base'])+0x500000)&0xFFFFFFFF),) )



def c_virtio(conf, dt):
    dt['dev'].append("""
        virtIO@%s {
            compatible = "virtio,mmio";
            reg = <%s %s %s %s>;
            interrupts = <0x0 %s 0x4>;
        };
    """%(hex(conf['base'])[2:],
         hex(_g(conf['base'])>>32),
         hex(_g(conf['base'])&0xFFFFFFFF),
         hex(0x1000>>32),
         hex(0x1000&0xFFFFFFFF),
         conf['irq']))

def c_python_device(conf, dt):
    dt['dev'].append(conf['dtnode'])

def c_pl11_uart(conf, dt):
    dt['dev'].append("""
        serial@%s {
          compatible = "arm,pl011", "arm,primecell";
          reg = <%s %s %s %s>;
          status = "okay";
          interrupts = <0x0 %s 0x4>;
          clocks = <&pclk>, <&uartclk>;
          clock-names = "uartclk", "apb_pclk";
        };
    """ % (
         hex(conf['base'])[2:],
         hex(_g(conf['base'])>>32),
         hex(_g(conf['base'])&0xFFFFFFFF),
         hex(0x1000>>32),
         hex(0x1000&0xFFFFFFFF),
         conf['irq'])
    )

def c_memory(conf, dt):
    dt['top'].append("""
    memory@%s {
        device_type = "memory";
        reg = <%s %s %s %s>;
    };
    """ % (hex(conf['base'])[2:],
            hex(_g(conf['base'])>>32),
            hex(_g(conf['base'])&0xffffffff),
            hex(_g(conf['size'])>>32),
            hex(_g(conf['size'])&0xffffffff)))

def c_cadence_uart(conf, dt):
    dt['dev'].append("""
        serial@%s {
            compatible = "cdns,uart-r1p12", "xlnx,xuartps";
            status = "okay";
            reg = < %s %s %s %s >;
            interrupts = < 0x00 %s 0x04 >;
            clock-names = "uart_clk", "pclk";
            clocks = < 0x05 0x05 >;
            device_type = "serial";
            port-number = < 0x00 >;
        };
    """ % (
         hex(conf['base'])[2:],
         hex(_g(conf['base'])>>32),
         hex(_g(conf['base'])&0xFFFFFFFF),
         hex(0x1000>>32),
         hex(0x1000&0xFFFFFFFF),
         conf['irq'])
    )


def c_systemc_output_port(conf, dt):
    dt['dev'].append(conf['dtnode'])

def c_cosim_out_port(conf, dt):
    dt['dev'].append(conf['dtnode'])

def c_fw_cfg(conf, dt):
    dt['dev'].append("""fw-cfg@%s {
            compatible = "qemu,fw-cfg-mmio";
            reg = <%s %s %s %s>;
        };""" % (
                hex(conf['base'])[2:],
                hex(_g(conf['base'])>>32),
                hex(_g(conf['base'])&0xFFFFFFFF),
                hex(0xa>>32),
                hex(0xa&0xFFFFFFFF)
        ))

def c_pl031(conf, dt):
    dt['dev'].append("""
        rtc@%s {
            compatible = "arm,pl031", "arm,primecell";
            reg = <%s %s %s %s>;
            interrupts = <0x0 %s 0x4>;
            clocks = <&pclk>;
            clock-names = "apb_pclk";
        };
    """ % (
            hex(conf['base'])[2:],
            hex(_g(conf['base'])>>32),
            hex(_g(conf['base'])&0xFFFFFFFF),
            hex(0x1000>>32),
            hex(0x1000&0xFFFFFFFF),
            conf['irq'])
    )
