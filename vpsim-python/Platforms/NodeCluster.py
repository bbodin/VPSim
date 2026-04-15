
from vpsim import System, Memory, Interconnect, ns, Param, BlobLoader, ElfLoader, SystemCTarget, RemoteTarget
from vpsim import ModelProvider, ModelProviderCpu, ModelProviderDev, ModelProviderParam1, ModelProviderParam2
from vpsim import PL011Uart, XuartPs, Monitor, PythonDevice, Cache, NoCMemoryController, CacheController, CacheIdController, CoherentInterconnect
from vpsim import SystemCCosim, IOAccessCosim, NoCDeviceController
import getpass, os, math
from datetime import datetime
import threading

from dt import DevTree, c_arm64, c_virtio, c_memory, c_pl11_uart, c_pl031

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
