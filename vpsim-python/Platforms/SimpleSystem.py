from Armv8Cluster import Armv8Cluster
from NodeCluster import NodeCluster

from vpsim import System, Memory, Interconnect, ns, Param, BlobLoader, ElfLoader, SystemCTarget, RemoteTarget
from vpsim import ModelProvider, ModelProviderCpu, ModelProviderDev, ModelProviderParam1, ModelProviderParam2
from vpsim import PL011Uart, XuartPs, Monitor, PythonDevice, Cache, NoCMemoryController, CacheController, CacheIdController, CoherentInterconnect
from vpsim import SystemCCosim, IOAccessCosim, NoCDeviceController
import getpass, os, math
from datetime import datetime
import threading

from dt import generate_devicetree

class SimpleSystem(System):

    def __init__(self, conf):
        super().__init__(conf['platform_name'])

        self.smp = conf["cpu"]["cores"]

        self.cpus = []
        self.icache = []
        self.dcache = []
        self.cosim_il1 = []

        qemu_lib = conf["cpu"]["qemu_lib"]
        trace_file = conf["software"]["trace_file"]

        qemu_parameters=f"""
            -nographic
            -semihosting
            --accel tcg,thread=single
            -icount 0
            -machine qslave
            -monitor none
            -smp {self.smp}
            -cpu max
            -m 4096.0M
            -serial mon:stdio
            -device virtio-net-device,netdev=net0
            -netdev user,net=192.168.0.0/24,id=net0
            """

        if "kernel" in conf["software"] :
            kernel_image = conf["software"]["kernel"]["path"]
            qemu_parameters += f" -kernel {kernel_image}\n"
            if 'bootargs' in conf['software']['kernel']:
                bootargs = conf['software']['kernel']['bootargs']
                qemu_parameters += f" -append \"{bootargs}\"\n"

        if "dtb" in conf["software"] :
            dtb = conf["software"]["dtb"]["path"]
            qemu_parameters += f" -dtb {dtb}\n"


        # ================= QEMU =================
        provider_name = ModelProvider(
            "qemuslave",
            conversion_factor=conf["cpu"]["conversion_factor"],
            quantum=conf["cpu"]["quantum"],
            roi_only=conf["cpu"].get("roi_only", 1),
            domain=1,
            path=qemu_lib,
            io_poll_period=conf["cpu"].get("io_poll_period", 1000),
            notify_main_memory_access=conf["cpu"].get("notify_main_memory_access", 1),
            simulate_icache=1,
            notify_ioaccess=conf["cpu"].get("notify_ioaccess", 0),
            qemu_parameters=qemu_parameters
        ).name



        if 'blocks' in conf:
            for b in conf['blocks']:
                block = ModelProviderDev(b['name'],
                    provider=provider_name,
                    model='virtio-mmio',
                    base_address=b['base'],
                    size=b['size'],
                    irq=b['irq'])

                ModelProviderParam2(provider=provider_name,
                    option='-device',
                    value='virtio-blk-device,drive=%s' % block.name)
                ModelProviderParam2(provider=provider_name,
                    option='-drive',
                    value='file=%s,id=%s' % (b['image'],block.name))


        # ================= DEVICES =================
        for name, dev in conf["devices"].items():
            print (dev)
            ModelProviderDev(
                name,
                domain=1,
                model=dev["model"],
                base_address=dev["base"],
                size=dev["size"],
                irq=dev["irq"],
                provider="qemuslave"
            )

        # ---- GIC from config ----
        ModelProviderDev(
            "gic_dist",
            domain=1,
            model="gicv3_dist",
            base_address=conf["gic"]["distributor_base"],
            size=conf["gic"]["distributor_size"], 
            irq=conf["gic"]["irq_base"],
            provider="qemuslave"
        )

        ModelProviderDev(
            "gic_redist",
            domain=1,
            model="gicv3_redist",
            base_address=conf["gic"]["redistributor_base"],
            size=conf["gic"]["redistributor_size"], 
            irq=self.smp,
            provider="qemuslave"
        )

        # ================= CPUs + L1 =================
        for i in range(self.smp):

            cpu = ModelProviderCpu(
                f"cpu_{i}",
                domain=1,
                model="max-arm-cpu",
                reset_pc=conf["cpu"]["reset_pc"],
                provider="qemuslave",
                id=i,
                quantum=conf["cpu"]["quantum"],
                secure=0, 
                start_powered_off=i > 0,
                icache_size=conf["cache"]["l1i"]["size"],
                icache_associativity=conf["cache"]["l1i"]["associativity"],
                icache_line_size=conf["cache"]["l1i"]["line-size"]
            )
            self.cpus.append(cpu)

            # ---- L1I ----
            ic = Cache(
                f"icacheL1_{i}",
                domain=1,
                size=conf["cache"]["l1i"]["size"],
                latency=conf["cache"]["l1i"]["latency-ns"],
                line_size=conf["cache"]["l1i"]["line-size"],
                associativity=conf["cache"]["l1i"]["associativity"],
                repl_policy=conf["cache"]["l1i"].get("repl_policy", "LRU"),
                writing_policy=conf["cache"]["l1i"].get("writing_policy", "WBack"),
                allocation_policy=conf["cache"]["l1i"].get("allocation_policy", "WAllocate"),
                cpu=i,
                local=1,
                id=100 + i,
                level=1,
                levels_number=1,
                is_home=0,
                is_coherent=1,
                inclusion_higher="NINE",
                inclusion_lower="NINE"
            )

            # ---- L1D ----
            dc = Cache(
                f"dcacheL1_{i}",
                domain=1,
                size=conf["cache"]["l1d"]["size"],
                latency=conf["cache"]["l1d"]["latency-ns"],
                line_size=conf["cache"]["l1d"]["line-size"],
                associativity=conf["cache"]["l1d"]["associativity"],
                repl_policy=conf["cache"]["l1d"].get("repl_policy", "LRU"),
                writing_policy=conf["cache"]["l1d"].get("writing_policy", "WBack"),
                allocation_policy=conf["cache"]["l1d"].get("allocation_policy", "WAllocate"),
                cpu=i,
                local=1,
                id=200 + i,
                level=1,
                levels_number=2,
                is_home=0,
                is_coherent=1,
                inclusion_higher="NINE",
                inclusion_lower="NINE"
            )

            self.icache.append(ic)
            self.dcache.append(dc)

            # ---- CoSim IL1 ----
            self.cosim_il1.append(
                CoherentInterconnect(
                    f"Inter_CoSim_iL1_{i}",
                    domain=1,
                    latency=0,
                    n_cache_in=1,
                    n_cache_out=0,
                    n_home_in=0,
                    n_home_out=1,
                    n_mmapped=0,
                    n_device=0,
                    flitSize=0,
                    memory_word_length=0,
                    is_mesh=0,
                    mesh_x=0,
                    mesh_y=0,
                    with_contention=0,
                    contention_interval=0,
                    buffer_size=0,
                    virtual_channels=0,
                    router_latency=0,
                    link_latency=0,
                    noc_stats_per_initiator_on=0,
                    is_coherent=1
                )
            )

        # ================= L2 =================
        self.l2 = Cache(
            "cacheL2_0",
            domain=1,
            size=conf["cache"]["l2"]["size"],
            latency=conf["cache"]["l2"]["latency-ns"],
            line_size=conf["cache"]["l2"]["line-size"],
            associativity=conf["cache"]["l2"]["associativity"],
            repl_policy=conf["cache"]["l2"].get("repl_policy", "LRU"),
            writing_policy=conf["cache"]["l2"].get("writing_policy", "WBack"),
            allocation_policy=conf["cache"]["l2"].get("allocation_policy", "WAllocate"),
            cpu=-1,
            local=0,
            id=300,
            level=2,
            l1i_simulate=1,
            levels_number=2,
            is_home=0,
            is_coherent=1,
            inclusion_lower=conf["cache"]["l2"].get("inclusion-l1", "Inclusive"),
            inclusion_higher="NINE"
        )

        # ================= INTERCONNECTS =================
        self.bus = Interconnect(
            "system_bus",
            domain=1,
            latency=2000,
            n_in_ports=self.smp,
            n_out_ports=1
        )

        self.iL1L2 = CoherentInterconnect(
            "Inter_L1I_L2",
            domain=1,
            latency=0,
            n_cache_in=self.smp,
            n_cache_out=0,
            n_home_in=0,
            n_home_out=1,
            n_mmapped=0,
            n_device=0,
            flitSize=0,
            memory_word_length=0,
            is_mesh=0,
            mesh_x=0,
            mesh_y=0,
            with_contention=0,
            contention_interval=0,
            buffer_size=0,
            virtual_channels=0,
            router_latency=0,
            link_latency=0,
            noc_stats_per_initiator_on=0,
            is_coherent=1
        )

        self.dL1L2 = CoherentInterconnect(
            "Inter_L1D_L2",
            domain=1,
            latency=0,
            n_cache_in=self.smp,
            n_cache_out=self.smp,
            n_home_in=1,
            n_home_out=1,
            n_mmapped=0,
            n_device=0,
            flitSize=0,
            memory_word_length=0,
            is_mesh=0,
            mesh_x=0,
            mesh_y=0,
            with_contention=0,
            contention_interval=0,
            buffer_size=0,
            virtual_channels=0,
            router_latency=0,
            link_latency=0,
            noc_stats_per_initiator_on=0,
            is_coherent=1
        )

        self.cosim_d = self.cosim_il1

        self.cosim = SystemCCosim(
            "SystemCCosim0",
                                 roi_only=1,
                                 domain=1,
                                 n_out_ports=self.smp
        )

        # ================= MEMORY =================
        self.mem = Memory(
            "Memory0",
            domain=1,
            size=conf["memory"]["size"],
            base_address=conf["memory"]["base"],
            cycle_duration=conf["memory"].get("cycle_duration", 1000),
            read_cycles=conf["memory"]["read-latency-cycles"],
            write_cycles=conf["memory"]["write-latency-cycles"],
            channel_width=conf["memory"]["channel-width"]
        )

        self.mon = Monitor(
            "Monitor0",
            log_directory=conf["monitoring"]["log_dir"],
            size=4,
            domain=1,
            base_address=conf["monitoring"].get("base_address", 385875968)
        )

        # ================= CONNECTIONS =================

        for cpu in self.cpus:
            cpu >> self.bus

        self.bus >> self.mon

        # ---- Instruction path ----
        for i in range(self.smp):
            self.cosim(f'fetch_port_{i}') >> self.cosim_il1[i]('cache_in_0')
            self.cosim_il1[i]('home_out_0') >> self.icache[i]('in_data')
            self.icache[i]('out_data') >> self.iL1L2(f'cache_in_{i}')

        self.iL1L2('home_out_0') >> self.l2('in_instruction')

        # ---------------- Data path ----------------
        for i in range(self.smp):
            self.cosim(f'data_port_{i}') >> self.dcache[i]('in_data')
            self.dcache[i]('out_data') >> self.dL1L2(f'cache_in_{i}')

        self.dL1L2('home_out_0') >> self.l2('in_data')

        self.l2('out_data') >> self.mem('p1')

        # ---- Coherence: L2 -> L1D invalidate path ----

        # L2 sends invalidations to the interconnect
        self.l2('out_invalidate') >> self.dL1L2('home_in_0')

        # Interconnect forwards invalidations to each L1D
        for i in range(self.smp):
            self.dL1L2(f'cache_out_{i}') >> self.dcache[i]('in_invalidate')
        
        if "log_level" in conf :
          self.addParam(Param("log_level",conf["log_level"]))

        if "monitoring" in conf  and  "stats_file" in conf["monitoring"] : 
          self.addParam(Param("stats_file", conf["monitoring"]["stats_file"]))

        # Generate device tree config

        conf_dt = {}
        conf_dt['platform_name'] = conf['platform_name']
        conf_dt['cpu'] = {
                'cores': conf['cpu']['cores'],
                'cores_per_cluster': conf['cpu']['cores'],
                'cpu_clusters': [ (list(range(conf['cpu']['cores'])), (0, 0))],
        }

        conf_dt['cpu']['gic'] = conf['gic']

        conf_dt['ram'] = [conf['memory']]
        conf_dt['uarts'] = []
        conf_dt['net'] = []
        conf_dt['block'] = []
        conf_dt['cdrom'] = []

        for name, dev in conf.get('devices', {}).items():
            model = dev['model']

            if model == 'pl011':
                conf_dt['uarts'].append({
                    'name': name,
                    'type': 'pl011',
                    'base': dev['base'],
                    'irq': dev['irq'],
                    'size': dev['size'], 
                })

            elif model == 'virtio-mmio':
                conf_dt['net'].append({
                    'name': name,
                    'base': dev['base'],
                    'irq': dev['irq'],
                    'size':dev['size'], 
                })

            elif model == 'pl031':
                conf_dt['rtc'] = {
                    'base': dev['base'],
                    'irq': dev['irq'],
                    'size': dev['size'], 
                }
            elif model == 'pcie':
                pass
            else :
                print (f"Unsupported device {model}!!")
                exit(1)

        # -------------------------------------------------
        # Block device (already almost correct)
        # -------------------------------------------------
        if 'blocks' in conf:
            conf_dt['block'] = []
            for b in conf['blocks'] :
                conf_dt['block'] . append ({
                    'name': b['name'],
                    'base': b['base'],
                    'irq': b['irq'],
                    'size':  b['size'],  
                    'image': b.get('image')
                })

        if 'device_tree_template' in conf :
            output_file = generate_devicetree(conf['device_tree_template'], conf_dt)
            if "dtb" in conf["software"] :
                dtb = conf["software"]["dtb"]["path"]
                if output_file != dtb :
                    print ("ERROR: the generated device tree binary is not the same as the file refered to qemu arguments.")
                    exit(1)
