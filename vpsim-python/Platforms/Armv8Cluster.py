
from vpsim import System, Memory, Interconnect, ns, Param, BlobLoader, ElfLoader, SystemCTarget, RemoteTarget
from vpsim import ModelProvider, ModelProviderCpu, ModelProviderDev, ModelProviderParam1, ModelProviderParam2
from vpsim import SystemCCosim, IOAccessCosim, NoCDeviceController
import os

from dt import DevTree, c_arm64, c_virtio, c_memory, c_pl11_uart, c_pl031

VPSIM_HOME = os.getenv('VPSIM_HOME')

model_provider = {
    'name': 'qemuslave',
    'path': os.path.join(VPSIM_HOME,'lib','qemu','vpsim-qemu.so'),
}


class Armv8Cluster:
    '''
    Generate a self-contained ARM-v8 cluster with N cores, and a GIC.
    '''
    def __init__(self, conf):
        # Load a QEMU into SESAM
        self.q = ModelProvider(model_provider['name'])
        self.q.path = model_provider['path']
        self.q.io_poll_period=1000

        if 'quantum' in conf['cpu']:
            self.q.quantum = conf['cpu']['quantum']

        if 'conversion_factor' in conf['cpu']:
            self.q.conversion_factor = conf['cpu']['conversion_factor']

        # Initialize QEMU
        ModelProviderParam2(provider=self.q.name, option='--accel', value='tcg,thread=single')
        ModelProviderParam2(provider=self.q.name, option='-icount', value='0')
        ModelProviderParam1(provider=self.q.name, option='-nographic')
        ModelProviderParam2(provider=self.q.name, option='-machine', value='qslave')
        ModelProviderParam2(provider=self.q.name, option='-monitor', value='none')
        ModelProviderParam1(provider=self.q.name, option='-semihosting')

        if 'device_tree_template' in conf :
            self.dt = DevTree(conf['platform_name'],conf['device_tree_template'])
            assert(self.dt)
        else :
            print ("Warning no device tree, bare metal mode only.")


        if 'qemu_execution_trace_file' in conf["monitoring"] and conf["monitoring"]['qemu_execution_trace_file']:
            trace_file = conf["monitoring"]['qemu_execution_trace_file']
            ModelProviderParam2(provider=self.q.name, option='-d', value='mmu,in_asm,int,guest_errors')
            ModelProviderParam2(provider=self.q.name, option='-D', value=trace_file)

        if conf["monitoring"]['gdb_port'] is not None:
            ModelProviderParam1(provider=self.q.name, option='-S',)
            ModelProviderParam2(provider=self.q.name, option='-gdb',
                value='tcp::%s' % conf['gdb_port'])

        n_cores = conf['cpu']['cores']
        self.cores = []
        ModelProviderParam2(provider=self.q.name,option='-smp',value=n_cores)
        ModelProviderParam2(provider=self.q.name, option='-cpu', value='max')

        # Initialize the interconnect in SESAM
        self.sysbus = Interconnect('system_bus', n_in_ports=0,n_out_ports=0,latency=2*ns)

        # Instantiate all CPUs within QEMU and connect them to sysbus
        for i in range(n_cores):
            cpu=ModelProviderCpu('cpu_%s'%i,model='max' + '-arm-cpu',id=i)
            cpu.reset_pc = conf['software']['entry'] if conf['software']['mode']=='custom' else 0
            cpu.secure = False
            cpu.start_powered_off = (i > 0)
            cpu.quantum = 1000 # actually fixed to 0xffff in QEMU
            cpu.provider=self.q.name
            self.cores.append(cpu)
            self.sysbus.n_in_ports += 1
            cpu >> self.sysbus

        # Device tree
        dt_conf = {
            'cores': conf['cpu']['cores'],
            'cores_per_cluster': conf['cpu']['cores_per_cluster'],
            'cpu_clusters': conf['cpu']['cpu_clusters'],
        }

        # Initialize the GIC regions within QEMU
        if conf['cpu']['gic']['version'] == 3:
            gicv3_dist = ModelProviderDev( \
                provider=self.q.name,
                model='gicv3_dist',
                base_address=conf['cpu']['gic']['distributor_base'],
                size=conf['cpu']['gic']['distributor_size'],
                irq=0)

            gicv3_redist = ModelProviderDev( \
                provider=self.q.name,
                model='gicv3_redist',
                base_address=conf['cpu']['gic']['redistributor_base'],
                size=conf['cpu']['gic']['redistributor_size'],
                irq=n_cores)

            dt_conf['gic']='v3'
        elif conf['cpu']['gic']['version'] == 2:
            gicv2_dist = ModelProviderDev( \
                provider=self.q.name,
                model='gicv2_dist',
                base_address=conf['cpu']['gic']['distributor_base'],
                size=conf['cpu']['gic']['distributor_size'],
                irq=0)

            gicv2_cpu = ModelProviderDev( \
                provider=self.q.name,
                model='gicv2_cpu',
                base_address=conf['cpu']['gic']['cpu_if_base'],
                size=conf['cpu']['gic']['cpu_if_size'],
                irq=0)

            gicv2_hyp = ModelProviderDev( \
                provider=self.q.name,
                model='gicv2_hyp',
                base_address=conf['cpu']['gic']['vctrl_base'],
                size=conf['cpu']['gic']['vctrl_size'],
                irq=0)

            gicv2_vcpu = ModelProviderDev( \
                provider=self.q.name,
                model='gicv2_vcpu',
                base_address=conf['cpu']['gic']['vcpu_base'],
                size=conf['cpu']['gic']['vcpu_size'],
                irq=0)

            dt_conf['gic']='v2'
        else:
            Exception("Unknown GIC version (must be 2 or 3).")

        for c in conf['cpu']['gic']:
            dt_conf[c] = conf['cpu']['gic'][c]

        if hasattr(self,"dt") :
            c_arm64(dt_conf, self.dt.getref())