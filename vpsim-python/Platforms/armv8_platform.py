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

from vpsim import System, Memory, Interconnect, ns, Param, BlobLoader, ElfLoader, SystemCTarget, RemoteTarget
from vpsim import ModelProvider, ModelProviderCpu, ModelProviderDev, ModelProviderParam1, ModelProviderParam2
from vpsim import PL011Uart, XuartPs, Monitor, PythonDevice, Cache, NoCMemoryController, CacheController, CacheIdController, CoherentInterconnect
from vpsim import SystemCCosim, IOAccessCosim, NoCDeviceController
import getpass, os, math
from datetime import datetime
import threading
import dt

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
            self.dt = dt.DevTree(conf['platform_name'],conf['device_tree_template'])


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
            dt.c_arm64(dt_conf, self.dt.getref())

class NodeCluster:
    '''
    Generate a self-contained cluster with cores, private L1, and L2.
    '''
    def __init__(self, conf, index):
        self.clus_cores = conf['cpu']['cores_per_cluster']
        # bus to connect L1 instrcution caches to L2
        self.InterInst = CoherentInterconnect('InterInstr_%s'%index,
                                              latency=0*ns,
                                              n_cache_in=conf['cpu']['cores_per_cluster'],
                                              n_cache_out=0,
                                              n_home_in=0,
                                              n_home_out=1,
                                              n_mmapped=0,
                                              n_device=0, #IOA
                                              flitSize=0,
                                              memory_word_length=0,
                                              is_coherent=conf['memory_subsystem']['enable_coherence'],
                                              is_mesh = False,
                                              noc_stats_per_initiator_on = False,
                                              mesh_x = 0,
                                              mesh_y = 0,
                                              with_contention = False,
                                              router_latency = 0,
                                              link_latency = 0,
                                              contention_interval = 0,
                                              buffer_size = 0,
                                              virtual_channels = 0)

        self.InterData = CoherentInterconnect('InterData_%s'%index,
                                              latency=0*ns,
                                              n_cache_in = conf['cpu']['cores_per_cluster'],
                                              n_cache_out = conf['cpu']['cores_per_cluster'],
                                              n_home_in=1,
                                              n_home_out=1,
                                              n_mmapped=0,
                                              n_device=0, #IOA
                                              flitSize=0,
                                              memory_word_length=0,
                                              is_coherent=conf['memory_subsystem']['enable_coherence'],
                                              is_mesh = False,
                                              noc_stats_per_initiator_on = False,
                                              mesh_x = 0,
                                              mesh_y = 0,
                                              with_contention = False,
                                              router_latency = 0,
                                              link_latency = 0,
                                              contention_interval = 0,
                                              buffer_size = 0,
                                              virtual_channels = 0)

        # Create L1 caches
        self.L1Caches = []
        l1index = index*self.clus_cores
        for i in range(self.clus_cores):
            L1Cache = Cache('dcacheL1_%s'%l1index,
                            latency=conf['memory_subsystem']['cache']['l1-data']['latency-ns'],
                            size=conf['memory_subsystem']['cache']['l1-data']['size'], # bytes
                            line_size=conf['memory_subsystem']['cache']['l1-data']['line-size'], # bytes
                            associativity=conf['memory_subsystem']['cache']['l1-data']['associativity'],
                            repl_policy='LRU',
                            writing_policy='WBack',
                            allocation_policy='WAllocate',
                            local=True,
                            id=1+100*(1+l1index),
                            level=1,
                            cpu=i,
                            is_home=False)
            # set optional parameters
            L1Cache.is_coherent = conf['memory_subsystem']['enable_coherence']
            L1Cache.levels_number   = 3
            L1Cache.inclusion_lower = conf['memory_subsystem']['cache']['l2']['inclusion-l1']
            self.L1Caches.append(L1Cache)
            l1index += 1

        # Create the L2 cache
        self.L2Cache = Cache('dcacheL2_%s'%index,
                        latency=conf['memory_subsystem']['cache']['l2']['latency-ns'],
                        size=conf['memory_subsystem']['cache']['l2']['size'], # bytes
                        line_size=conf['memory_subsystem']['cache']['l2']['line-size'], # bytes
                        associativity=conf['memory_subsystem']['cache']['l2']['associativity'],
                        repl_policy='LRU',
                        writing_policy='WBack',
                        allocation_policy='WAllocate',
                        local=False,
                        id=2+100*(1+index),
                        level=2,
                        cpu=index, # useless if local is false
                        is_home=False)
        self.L2Cache.home_base_address = conf['ram'][0]['base']
        self.L2Cache.home_size = conf['ram'][0]['size']
        # set optional parameters
        self.L2Cache.l1i_simulate = True
        self.L2Cache.is_coherent = conf['memory_subsystem']['enable_coherence']
        self.L2Cache.levels_number    = 3
        self.L2Cache.inclusion_higher = conf['memory_subsystem']['cache']['l2']['inclusion-l1']
        self.L2Cache.inclusion_lower  = conf['memory_subsystem']['cache']['l3']['inclusion-l2']

        # connections inside a cluster
        for i in range(self.clus_cores):
            # connect L1 data caches to data interconnect
            self.L1Caches[i]("out_data") >> self.InterData("cache_in_%s"%i)
            self.InterData("cache_out_%s"%i) >> self.L1Caches[i]("in_invalidate")
            # connection to L1 instruction caches via InterInst("cache_in_%s"%i) in caller class
        # connect L2 caches to interconnects
        self.InterInst("home_out_0") >> self.L2Cache("in_instruction")
        self.InterData("home_out_0") >> self.L2Cache("in_data")
        self.L2Cache("out_invalidate") >> self.InterData("home_in_0")

class FullSystem(System):
    ''' Generate the full system '''
    def __init__(self, conf):
        System.__init__(self, conf['platform_name'])
        self.cluster = Armv8Cluster(conf)
        sysbus = self.cluster.sysbus
        provider = self.cluster.q
        
        if hasattr(self,"dt") :
            self.dt = self.cluster.dt

        # Create main memory
        ram_size=0
        ram_spaces = []
        for ram in conf['ram']:
            self.ram = Memory(
                base_address = ram['base'],
                size = ram['size'],
                dmi_enable = True)
            #sysbus.n_out_ports += 1
            #sysbus >> self.ram
            if not ram_spaces:
                for c in self.cluster.cores:
                    c.reset_pc=self.ram.base_address
            ram_size += ram['size']
            ram_spaces.append(self.ram)
            self.ram.channels=1
            self.ram.channel_width=8
            if hasattr(self,"dt") :
                dt.c_memory(ram,self.dt.getref())

        # Instruction caches
        for core in self.cluster.cores:
            core.icache_size = conf['memory_subsystem']['cache']['l1-instructions']['size']
            core.icache_line_size = conf['memory_subsystem']['cache']['l1-instructions']['line-size']
            core.icache_associativity = conf['memory_subsystem']['cache']['l1-instructions']['associativity']

        if conf['memory_subsystem']['simulate']:
            provider.notify_main_memory_access=True
            provider.simulate_icache=True
            # Create cosimulator
            main_memory=SystemCCosim(
                n_out_ports=len(self.cluster.cores)
            )
            if 'focus_on_roi' in conf['memory_subsystem']:
                provider.roi_only = main_memory.roi_only = conf['memory_subsystem']['focus_on_roi']
            # Create IOAccess Notifier
            nb_iodevs=0
            if ('IODevs' in conf['memory_subsystem']) and (len(conf['memory_subsystem']['IODevs'])>0):
                provider.notify_ioaccess=True
                nb_iodevs = len(conf['memory_subsystem']['IODevs'])
                ioaccess_notifier=IOAccessCosim(n_out_ports=nb_iodevs)
            else:
                provider.notify_ioaccess=False
            # Create NoC
            mem_noc=CoherentInterconnect('network_on_chip',
                                         latency=0*ns,
                                         n_cache_in=conf['cpu']['cores'] // conf['cpu']['cores_per_cluster'],
                                         n_cache_out=conf['cpu']['cores'] // conf['cpu']['cores_per_cluster'],
                                         n_home_in=len(conf['memory_subsystem']['cache']['l3']['home-nodes']),
                                         n_home_out=len(conf['memory_subsystem']['cache']['l3']['home-nodes']),
                                         n_mmapped=len(conf['ram']),
                                         n_device=nb_iodevs, #IOA
                                         flitSize=conf['memory_subsystem']['noc']['flit-size'],
                                         memory_word_length=conf['memory_subsystem']['off-chip-memory']['channel-width'] * conf['memory_subsystem']['off-chip-memory']['channels'],
                                         is_coherent = conf['memory_subsystem']['enable_coherence'],
                                         is_mesh = True,
                                         noc_stats_per_initiator_on = conf['memory_subsystem']['noc']['diagnosis'],
                                         mesh_x = conf['memory_subsystem']['noc']['x-nodes'],
                                         mesh_y = conf['memory_subsystem']['noc']['y-nodes'],
                                         with_contention = conf['memory_subsystem']['noc']['with-contention'],
                                         router_latency = conf['memory_subsystem']['noc']['router-latency-ns'],
                                         link_latency = conf['memory_subsystem']['noc']['link-latency-ns'],
                                         contention_interval = conf['memory_subsystem']['noc']['contention-interval-ns'],
                                         buffer_size = conf['memory_subsystem']['noc']['buffer-size-flits'],
                                         virtual_channels = conf['memory_subsystem']['noc']['virtual-channels'])
            # Memory Interleave default enabled
            if 'interleave_step' in conf['memory_subsystem']['off-chip-memory']:
                mem_noc.memory_interleave_length = conf['memory_subsystem']['off-chip-memory']['interleave_step']
            else:
                mem_noc.memory_interleave_length = conf['memory_subsystem']['cache']['l3']['line-size']
            # SLC Interleave default enabled
            if 'interleave_step' in conf['memory_subsystem']['cache']['l3']:
                slc_interleave_step = conf['memory_subsystem']['cache']['l3']['interleave_step']
            else:
                slc_interleave_step = conf['memory_subsystem']['cache']['l3']['line-size']
            mem_noc.slc_interleave_length = slc_interleave_step

            # Connect ioaccess notifier to NoC
            if nb_iodevs > 0 :
                id_iodev=0
                for iodev in conf['memory_subsystem']['IODevs']:
                    ioaccess_notifier('dma_port_%d'%id_iodev) >> mem_noc('device_%d'%id_iodev)
                    NoCDeviceController(iodev['name'],id_dev=id_iodev,x_id=iodev['x-pos'],y_id=iodev['y-pos'],noc=mem_noc.name)
                    id_iodev += 1

            # Create node clusters
            cpu_clusters = conf ['cpu']['cpu_clusters'] # list of (cpu ids, position) of all clusters
            # iterate on clusters
            for index, cluster_node in enumerate(cpu_clusters):
                cores_ids, (x, y) = cluster_node
                # create a cluster with cpus and caches
                Cluster = NodeCluster(conf, index)
                # connect cosimulator outputs to caches
                for cpu_in_clus, cpu in enumerate(cores_ids):
                    main_memory('data_port_%s'%cpu)  >> Cluster.L1Caches[cpu_in_clus]("in_data")
                    main_memory('fetch_port_%d'%cpu) >> Cluster.InterInst("cache_in_%s"%cpu_in_clus)
                # connect cluster caches to NoC
                Cluster.L2Cache("out_data") >> mem_noc("cache_in_%s"%index)
                mem_noc("cache_out_%s"%index) >> Cluster.L2Cache("in_invalidate")
                # create cluster controller
                CacheIdController(noc=mem_noc.name, cache=Cluster.L2Cache.name, x_id=x, y_id=y)

            # SLC Interleave default enabled
            interleaved_caches = len(conf['memory_subsystem']['cache']['l3']['home-nodes'])
            if slc_interleave_step==0: interleaved_caches = 0
            # iterate on home nodes
            for index, home_node in enumerate(conf['memory_subsystem']['cache']['l3']['home-nodes']):
                base, size, (x, y) = home_node
                llc = Cache('dcacheL3_%s'%index,
                    latency=conf['memory_subsystem']['cache']['l3']['latency-ns'],
                    size=conf['memory_subsystem']['cache']['l3']['home-node-size'], # bytes
                    line_size=conf['memory_subsystem']['cache']['l3']['line-size'], # bytes
                    associativity=conf['memory_subsystem']['cache']['l3']['associativity'],
                    repl_policy='LRU',
                    writing_policy='WBack',
                    allocation_policy='WAllocate',
                    local=False,
                    id=3+100*(1+index),
                    level=3,
                    cpu=index, #TODO, Useless parameter
                    is_home=True)
                # set optional parameters
                llc.is_coherent = conf['memory_subsystem']['enable_coherence']
                llc.levels_number = 3
                llc.inclusion_higher = conf['memory_subsystem']['cache']['l3']['inclusion-l2']
                llc.home_base_address=base
                llc.home_size=size
                llc.nb_interleaved_caches = interleaved_caches

                # connect home caches to NoC
                mem_noc("home_out_%s"%index) >> llc("in_data")
                llc("out_data") >> mem_noc("home_in_%s"%index)
                # create home controller
                CacheIdController(noc=mem_noc.name, cache=llc.name, x_id=x, y_id=y)
                CacheController(noc=mem_noc.name, size=size, base_address=base, x_id=x, y_id=y)

            for i, r in enumerate(ram_spaces):
                mem_noc("mmapped_out_%s"%i) >> r
                r.write_cycles=conf['memory_subsystem']['off-chip-memory']['write-latency-ns']
                r.read_cycles=conf['memory_subsystem']['off-chip-memory']['read-latency-ns']
                r.channel_width=conf['memory_subsystem']['off-chip-memory']['channel-width'] \
                           * conf['memory_subsystem']['off-chip-memory']['channels']

            for mem_ctrl in conf['memory_subsystem']['off-chip-memory']['memory-controllers']:
                b,sz,pos=mem_ctrl
                x,y=pos
                posId=y*mem_noc.mesh_x+x

                NoCMemoryController(
                    base_address=b,
                    size=sz,
                    x_id=x,
                    y_id=y,
                    noc=mem_noc.name)
        else:
            provider.notify_main_memory_access=False
            provider.simulate_icache=False
            for r in ram_spaces:
                sysbus.n_out_ports += 1
                sysbus >> r
            provider.notify_ioaccess=False
        sysbus.n_out_ports += 1

        monitor_arguments = {"size" : 4, "base_address" : conf["monitoring"]['sesam_monitor_addr'] }
        if conf['monitoring']['sesam_monitor_log_directory'] :
            monitor_arguments["log_directory"] = conf['monitoring']['sesam_monitor_log_directory']

        sysbus >> Monitor(**monitor_arguments)

        ModelProviderParam2(provider=provider.name,
            option='-m',
            value='%sM'%(ram_size/(1024*1024)))


        # Create UART controllers
        pl_exists = False
        for uart in conf['uarts']:
            typ=uart['type']
            if typ == 'cdns':
                sysbus.n_out_ports += 1
                sysbus >> XuartPs(uart['name'],
                    size=uart['size'],
                    poll_period=int(8./9600*1000000000)*ns,
                    channel="stdio",
                    interrupt_parent=provider.name,
                    irq_n=uart['irq'],
                    base_address=uart['base'])
                dt.c_cadence_uart(uart, self.dt.getref())
            elif typ == 'pl011':
                '''ModelProviderParam2(provider=provider.name,
                    option='-chardev',
                    value='socket,server,host=localhost,port=%s,mux=on,id=char0'%(
                        uart['port']))'''
                ModelProviderParam2(provider=provider.name,
                    option='-serial',
                    value='mon:stdio')
                    
                if hasattr(self,"dt") :
                    dt.c_pl11_uart(uart, self.dt.getref())
                uart=ModelProviderDev(uart['name'],provider=provider.name,
                    model='pl011',
                    base_address=uart['base'],
                    size=0x1000,
                    irq=uart['irq'])
                pl_exists = True

        if not pl_exists:
            ModelProviderParam2(provider=provider.name,
                option='-serial',
                value='none')

        # PCI-E host bridge inside QEMU
        pcie = ModelProviderDev(model='pcie', provider=provider.name, base_address=0x10000000, irq=3, size=0)

        # Now create block and network devices using VirtIO
        ## First map the container buses, then create the devices
        if 'net' in conf:
          for net in conf['net']:
            dev = ModelProviderDev(net['name'],
                provider=provider.name,
                model='virtio-mmio',
                base_address=net['base'],
                size=net['size'],
                irq=net['irq'])

            if hasattr(self,"dt") :
                dt.c_virtio(net, self.dt.getref())

            # if 'mac' not in net:
            #     net['mac']="54:54:00:12:34:58"
            # ModelProviderParam2(provider=provider.name,
            #     option='-device',
            #     value='virtio-net-device,netdev=%s,mac=%s' % (net['name'],net['mac']))

            # User mode network
            if 'tap' not in conf['net']:
                ModelProviderParam2(provider=provider.name,
                    option='-device',
                    value='virtio-net-device,netdev=%s' % (net['name']))
                if 'hostfwd_ssh_port' not in net:
                    ModelProviderParam2(provider=provider.name,
                        option='-netdev',
                        value='user,net=%s,id=%s' % (net['ip'],net['name']))
                else:
                    ModelProviderParam2(provider=provider.name,
                        option='-netdev',
                        value='user,net=%s,id=%s,hostfwd=tcp::%s-:22' % (net['ip'],net['name'],net['hostfwd_ssh_port']))

            # tap mode network
            if 'tap' in net:
                ModelProviderParam2(provider=provider.name,
                    option='-netdev',
                    value='tap,ifname=%s,id=%s,script=' % (net['name'],net['name']))

                if 'host_if' in net['tap']:
                    def netconfig(host_if, guest_if):
                        for line in (("""brctl addbr br1
                         ip addr flush dev """+host_if+"""
                         brctl addif br1 """+host_if+"""
                         tunctl -t """+guest_if+""" -u `whoami`
                         brctl addif br1 """+guest_if+"""
                         ifconfig """ + guest_if + """ up
                         ifconfig br1 192.168.0.1 netmask 255.255.255.0 up
                         ip route add 192.168.0.0/24 via 192.168.0.1 dev """+guest_if+"""
                         """)) .split('\n'):
                             try:
                                 os.system(line)
                             except:
                                 pass
                    host_if = net['tap']['host_if']
                    guest_if = net['name']
                    netconfig(host_if,guest_if)
                else:
                    def netconfig(nm,ip):
                        for line in (("""
                         ip tuntap add dev """+nm+""" mode tap user """+getpass.getuser()+"""
                         ip link set """+nm+""" up
                         ip addr add """+ip+""" dev """+nm+"""
                         """)) .split('\n'):
                             try:
                                 os.system(line)
                             except:
                                 pass
                    netconfig(net['name'],net['tap']['ip'])


        if 'block' in conf:
            for b in conf['block']:
                dt.c_virtio(b, self.dt.getref())
                block = ModelProviderDev(b['name'],
                    provider=provider.name,
                    model='virtio-mmio',
                    base_address=b['base'],
                    size=b['size'],
                    irq=b['irq'])
                ModelProviderParam2(provider=provider.name,
                    option='-device',
                    value='virtio-blk-device,drive=%s' % block.name)
                ModelProviderParam2(provider=provider.name,
                    option='-drive',
                    value='file=%s,id=%s' % (b['image'],block.name))


        if 'cdrom' in conf:
            ModelProviderParam2('CD-ROM-SLOT',
                provider=provider.name,
                option='-device',
                value='virtio-scsi-device,id=scsi0')

            for cd in conf['cdrom']:
                c = ModelProviderDev(provider=provider.name,
                    model='virtio-mmio',
                    base_address=cd['base'],
                    size=0x1000,
                    irq=cd['irq'])

                cd['size']=0x1000
                dt.c_virtio(cd, self.dt.getref())

                ModelProviderParam2(provider=provider.name,
                        option='-device',
                        value='scsi-cd,drive=%s' % c.name)
                ModelProviderParam2(provider=provider.name,
                        option='-drive',
                        value="file=%s,id=%s,if=none,media=cdrom" % (cd['image'],c.name))

        if 'unused_spaces' in conf:
            for unused in conf['unused_spaces']:
                sysbus.n_out_ports += 1
                sysbus >> Memory(
                    base_address = unused['base'],
                    size = unused['size'],
                    dmi_enable = False)

        # SystemC target subsystems
        if 'systemc' in conf:
          for systemc in conf['systemc']:
            sysbus.n_out_ports += 1
            sysbus >> SystemCTarget(
                systemc['name'],
                base_address=systemc['base'],
                size=systemc['size'],
                interrupt_parent=provider.name)
            dt.c_systemc_output_port(systemc, self.dt.getref())

        # Remote target subsystems
        if 'remote' in conf:
            for remote in conf['remote']:
                sysbus.n_out_ports += 1
                sysbus >> RemoteTarget(
                    remote['name'],
                    base_address=remote['base'],
                    size=remote['size'],
                    interrupt_parent=provider.name,
                    irq_n=remote['irq'],
                    channel=remote['name'],
                    irq_channel=remote['name']+'_irq')

        # User-defined Python devices
        if 'pydevs' in conf:
          for pydev in conf['pydevs']:
            sysbus.n_out_ports += 1
            sysbus >> PythonDevice(\
                pydev['name'],
                base_address=pydev['base'],
                size=pydev['size'],
                interrupt_parent=provider.name,
                py_module_name=pydev['module'],
                param_string=pydev['config'],)

        if 'fw_cfg_addr' in conf:
            ModelProviderDev(provider=provider.name,
                    model='fw_cfg',
                    base_address=conf['fw_cfg_addr'],
                    size=0x18,
                    irq=0)
            dt.c_fw_cfg({'base':conf['fw_cfg_addr']},self.dt.getref())

        if 'rtc' in conf:
            ModelProviderDev(provider=provider.name,
                model='pl031',
                base_address=conf['rtc']['base'],
                size=0x1000,
                irq=conf['rtc']['irq'])
            conf['rtc']['size']=0x1000
            
            if hasattr(self,"dt") :
                dt.c_pl031(conf['rtc'], self.dt.getref())

        if 'flash' in conf:
            for i,fl in enumerate(conf['flash']):
                ModelProviderDev(provider=provider.name,
                    model='cfi_flash_%s'%i,
                    base_address=fl['base'],
                    size=0,
                    irq=fl['size'])
                if 'img' in fl:
                    ModelProviderParam2(provider=provider.name,
                        option='-drive',
                        value='file=%s,if=pflash,aio=threads,format=raw' % fl['img'])

        # Platform should be fully constructed now, load binary images !
        if conf['software']['mode'] in ['custom', 'full'] :
            def load(sw_part):
                load_addr=sw_part['addr']
                success=False
                for space in ram_spaces:
                    base=space.base_address
                    size=space.size
                    if load_addr >= base and load_addr < base+size:
                        # load image here
                        BlobLoader(
                            target_memory=space.name,
                            file=sw_part['path'],
                            offset=load_addr-base)
                        success=True
                        break
                return success

            if 'bin' in conf['software']:
                for bin in conf['software']['bin']:
                    assert(load(bin))
            if 'elf' in conf['software']:
                for elf in conf['software']['elf']:
                    ElfLoader(path=elf)
        elif conf['software']['mode']  == 'minimal':
            pass
        else :
            raise Exception("Software mode should be one of: minimal or full")

        if 'dtb' in conf['software'] and conf['software']['dtb'] is not None:
            ModelProviderParam2(provider=provider.name, option='-dtb', value=conf['software']['dtb']['path'])
        if 'rootfs' in conf['software']:
            ModelProviderParam2(provider=provider.name, option='-initrd', value=conf['software']['rootfs']['path'])
        ModelProviderParam2(provider=provider.name, option='-kernel', value=conf['software']['kernel']['path'])
        if 'bootargs' in conf['software']['kernel']:
            ModelProviderParam2(provider=provider.name, option='-append', value=conf['software']['kernel']['bootargs'])

        dateTime = datetime.now().isoformat(timespec='seconds')
        working_dir='.%s%s--%s' % (self.name, dateTime, threading.current_thread().ident)

        stats_file = None
        execution_trace = None 
        logging_value = "disable"

        if conf["monitoring"]["vpsim_log_level"] :
            logging_value = "enable"
            if int(conf["monitoring"]["vpsim_log_level"]) :
                logging_value = int(conf["monitoring"]["vpsim_log_level"]) 
        
        if conf["monitoring"]["vpsim_stats_file"] :
            stats_file = conf["monitoring"]["vpsim_stats_file"]
            
        if conf["monitoring"]["qemu_execution_trace_file"] :
            execution_trace = conf["monitoring"]["qemu_execution_trace_file"]

        self.addParam(Param("log_level",logging_value))

        if (stats_file) :
            self.addParam(Param("stats_file", stats_file))


        # Generate device tree
        
        if hasattr(self,"dt") :
            self.dt.make()

        # Export sysbus for extensions
        self.sysbus = sysbus

    def getSystemBus(self):
        return self.sysbus
