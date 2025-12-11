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

import time
import os
import subprocess
import re
import threading
import shutil
import copy
from datetime import datetime

from concurrent.futures import ThreadPoolExecutor, as_completed

_Ex=ThreadPoolExecutor(1)

def getSystem():
    return _all_known_sys[-1]

def SetMaxThreads(mt):
    global _Ex
    _Ex = ThreadPoolExecutor(max_workers=mt)

_ActF=[]

def IterReadySystems():
    global _ActF
    t=copy.copy(_ActF)
    _ActF=[]
    return map(lambda x: x.result(), as_completed(t))

class _TUnit:
    def __init__(self,unit=1):
        self.unit=unit
        self.value=1
    def __mul__(self,other):
        if isinstance(other,int) :
            k=_TUnit()
            k.value=other*self.value
            k.unit=self.unit
            return k
        else:
            raise Exception("Can only multiply time unit by an integer")
    def __rmul__(self,other):
        return self * other
    def __add__(self, other):
        if isinstance(other,_TUnit):
            k=_TUnit()
            k.value=self.toint()+other.toint()
            return k
        else:
            raise Exception("Cannot add integer without unit.")
    def toint(self):
        return self.value*self.unit

#use picoseconds as base unit.
ps=_TUnit()
ns = 1000*ps
us = 1000*ns
ms = 1000*us

#### Compute attributes automatically
_Formulas={

     "Arm": {
         "stop_on_first_core_done": lambda cpu: False,
         "gdb_enable": lambda cpu: False,
         "quantum": lambda cpu: list(filter(lambda x:x.name=="quantum",cpu.gp().config))[0].children[0],
     },

     "Arm64": {
         "stop_on_first_core_done": lambda cpu: False,
         "gdb_enable": lambda cpu: False,
         "quantum": lambda cpu: list(filter(lambda x:x.name=="quantum",cpu.gp().config))[0].children[0],
     },

    "Memory": {
         "load_elf": lambda mem: True if hasattr(mem,"elf_file") and mem.elf_file else False,
         "elf_file": lambda mem: '',
         "dmi_enable": lambda mem: True,
         "channels": lambda mem: 1,
         "channel_width": lambda mem: 8,
     },

     "Interconnect": {
         "is_mesh": lambda inter: False,
         "mesh_x": lambda inter: 0,
         "mesh_y": lambda inter: 0,
         "router_latency": lambda inter: 0,
     },

}

# compute size of memory mapped elements
for _type in ["Memory", "ItCtrl", "Rtc", "Uart", "SmartUart"]:
    if _type not  in _Formulas:
        _Formulas[_type]={}
    _Formulas[_type]["size"]=lambda mme: mme.end_address-mme.base_address+1
    _Formulas[_type]["cycle_duration"] = lambda mme: 1*ns
    _Formulas[_type]["read_cycles"] = lambda mme: 0
    _Formulas[_type]["write_cycles"] = lambda mme: 0


CurrentDomain=0
def newAddressDomain():
    global CurrentDomain
    CurrentDomain+=1


_ve=os.getenv("VPSIM_PATH")

if not _ve:
    raise Exception("Please put the path to VPSim in the $VPSIM_PATH environment variable.")

os.chdir(os.path.split(_ve)[0])

_all_known_sys=[]
_autn={}

class _pt:
    def __init__(self, __pari, __nm):
        self.__pari=__pari
        self.__nm=__nm
    def __rshift__(self,__mukou):
        if (isinstance(__mukou, _pt)):
            self._ao(__mukou)
            __mukou._ai()
            return __mukou
        else:
            assert(isinstance(__mukou, _ssmip))
            p=__mukou()
            self._ao(p)
            return p
    def _ao(self,b):
        self.__pari.ao(self.__nm,b)
    def _ai(self):
        self.__pari.ai(self.__nm)
    def nm(self):
        return self.__nm
    def parn(self):
        return self.__pari.name

class _ssmip:
    def __init__(self, __nm, na, __prntsys=None,):
        if __prntsys is None:
            if len(_all_known_sys) < 1:
                raise Exception("Cannot assign IP %s(%s) to a system. \
                    Please specify System instance in last argument to constructor."
                    % (__nm, self.__class__.__name__))
            __prntsys=_all_known_sys[-1]
        self.__prntsys=__prntsys
        #self.__oldsettr = self.setattr
        #self.setattr = self.__newsettr
        self.__kpu={}
        self.__kpi={}
        self.__kpo={}
        self.__c=0
        self._ka=[]
        self._ko=[]
        self._sa={}
        self.__prntsys.psh(self)
        self.name=__nm
        self.domain=CurrentDomain
        for k in na:
            setattr(self,k,na[k])
    def gp(self): return self.__prntsys

    def ai(self, n):
        assert(len(self.__kpi)<self._mi or self._mi<0)
        p=self.__kpu[n]
        del self.__kpu[n]
        self.__kpi[n]=p


    def go(self):
        return self.__kpo

    def ao(self, n, b):
        assert(len(self.__kpo)<self._mo or self._mo<0)
        p=self.__kpu[n]
        del self.__kpu[n]
        self.__kpo[n]=p
        assert(isinstance(b,_pt))
        p.b=b

    def nn(self):
        self.__c+=1
        return "p%s" % (self.__c)

    def __rshift__(self, otherthing):
        if isinstance(otherthing, _ssmip):
            return self.__call__() >> otherthing()
        else:
            assert(isinstance(otherthing, _pt))
            return self.__call__() >> otherthing

    def __call__(self, _ptnm=None):
        if not _ptnm:
            _ptnm=self.nn()
        if _ptnm not in self.__kpu:

            #if len(__kpu)<self.__mo or self.__mo<0:
                self.__kpu[_ptnm]  = _pt(self, _ptnm)
        assert(isinstance(self.__kpu[_ptnm], _pt))
        return self.__kpu[_ptnm]



    def __newsettr(self, __an, __av):
        if __an not in self._ka and __an not in self._ko:
            raise AttributeError("IP %s has no attribute %s" % (self.__class__.__name__,__an))
        if type(__av) == bool:
            __av= 0 if __av==False else 1
        self._sa[__an]=str(__av)
        self.__oldsettr(__an,__av)
        return __av


class Param:
    def __init__(self, name, *values, **attrs):
        self.name=name
        self.attrs=attrs
        self.children=values

    def toXml(self):
        return "<%s%s>%s</%s>" % (
                self.name, " ".join(map(lambda k: " %s=\"%s\""%(k,self.attrs[k]),self.attrs)),
                    ''.join(map(lambda c: "%s"%(c if not isinstance(c, _TUnit) else c.toint()) \
                        if not isinstance(c,Param) else c.toXml(),self.children) ), self.name )




class System:
    def __init__(self, name):
        self.__ips=[]
        self.name=name
        self.config = []
        _all_known_sys.append(self)
        newAddressDomain()

    def psh(self,ip):
        self.__ips.append(ip)

    def addParam(self, param):
        if not isinstance(param,Param):
            raise TypeError("addParam() expects a Param object.")

        self.config.append(param)

    def build(self, fmts=["xml"], output=True, simulate=False, wait=True, silent=True, outstream='', timeout_sec=None):
        buildsets={}
        for f in fmts:
            buildsets[f]=[]
            buildsets[f].append(self.begin(f))
            buildsets[f].append(self.beginPlatform(f, self.name))
            buildsets[f].append(self.beginIps(f))
            _nfid=0

            for ip in self.__ips:
                buildsets[f].append(self.beginIp(f,ip.__class__.__name__,ip.name))
                for a in ip._ka:
                    if hasattr(ip,a):
                       v=getattr(ip,a)
                    else:
                       v=_Formulas[ip.__class__.__name__][a](ip)
                    if type(v) == bool:
                       v= 1 if v else 0
                    elif isinstance(v,_TUnit):
                       v=v.toint()

                    buildsets[f].append(self.attr(f, a, v))
                buildsets[f].append(self.endIp(f, ip.__class__.__name__))
            buildsets[f].append(self.endIps(f))

            #### port bindings
            buildsets[f].append(self.beginLinks(f))
            for ip in self.__ips:
                o=ip.go()
                if len(o) > 0:
                    for k in o:
                        p = o[k]
                        buildsets[f].append(
                            self.link(f, ip.name, p.nm(), p.b.parn(), p.b.nm()))
            buildsets[f].append(self.endLinks(f))
            buildsets[f].append(self.endPlatform(f))
            buildsets[f].append(self.beginParams(f))
            for par in self.config:
                buildsets[f].append(self.param(f,par))
            buildsets[f].append(self.endParams(f))
            buildsets[f].append(self.end(f))

            if output:
                if type(output) == str:
                    fn=output
                else:
                    fn='%s.%s'%(self.name,f)
                with open(fn,'w') as of:
                    of.write('\n'.join(buildsets[f]))

            if simulate:
                if wait:
                    return self.__simulate(buildsets[f], silent, outstream,timeout_sec).stats
                else:
                    self.__fut=_Ex.submit(self.__simulate, buildsets[f], silent, outstream,timeout_sec)
                    _ActF.append(self.__fut)

    def done(self):
        return self.__fut.done()

    def waitStats(self):
        return self.__fut.result().stats

    def __simulate(self, bs, silent, outstream, timeout_sec=None):
        dateTime = datetime.now().isoformat(timespec='seconds')
        working_dir='.%s%s--%s' % (self.name, dateTime, threading.current_thread().ident)
        os.makedirs(working_dir,exist_ok=True)
        with open(os.path.join(os.path.split(_ve)[0], working_dir,'tmp.xml'),'w') as tmp:
            for t in bs:
                tmp.write(t+'\n')
        if silent:
            if outstream:
                outdev=open(outstream, 'w')
            else:
                outdev=subprocess.DEVNULL
        else: outdev=None

        try:
            print (f"working_dir is {working_dir}")
            print ("Running command:",[_ve, '--run', 'tmp.xml'])
            p=subprocess.Popen([_ve, '--run', 'tmp.xml'],
                cwd=working_dir,stdout=outdev,stderr=outdev, )
        except subprocess.SubprocessError:
            print("ERROR while running subprocess")

        start_time = time.time()
        while True:
            ret = p.poll()
            if ret is not None:
                # process finished
                break
            if timeout_sec is not None and (time.time() - start_time) > timeout_sec:
                print(f"TIMEOUT: VPSIM simulation exceeded {timeout_sec} seconds. Terminating...")
                p.terminate()
                try:
                    p.wait(5)
                except subprocess.TimeoutExpired:
                    p.kill()
                print("VPSIM simulation timed out")
            time.sleep(0.1)


        # try:
        #     p.wait()
        # except KeyboardInterrupt:
        #     print("forwarding term signal to child.")
        #     p.terminate()

        self.stats={}
        for logf in [f for f in os.listdir(working_dir) if os.path.splitext(f)[1]==".log"]:
            # print "parsing %s " % logf
            with open(os.path.join(working_dir,logf),'r') as log:
                for line in log.readlines():
                    t = re.match("\\[Stats\\]\\s+\\((\\S+)\\)\\s+(\\S+)\\s+(\\S+)\\s*(\\S*)",line)
                    if t:
                        if t.group(1) not in self.stats:
                            self.stats[t.group(1)]={}
                        self.stats[t.group(1).strip()][t.group(2).strip()]=(eval(t.group(3).strip()),t.group(4).strip())
                        # print "%s.%s = %s %s" % (t.group(1), t.group(2), t.group(3), t.group(4))
            #os.unlink(os.path.join(working_dir,logf))
        #shutil.rmtree(working_dir)
        return self

    def begin(self, fmt):
        if fmt == 'xml':
            return "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<vpsim source=\"python\">"
        else:
            raise TypeError("Cannot handle format: %s" % fmt)

    def end(self, fmt):
        if fmt == 'xml':
            return "</vpsim>"
        else:
            raise TypeError("Cannot handle format: %s" % fmt)

    def beginPlatform(self, fmt, name):
        if fmt == 'xml':
            return "<platform name=\"%s\">"%name
        else:
            raise TypeError("Cannot handle format: %s" % fmt)

    def beginIp(self, fmt, typeN, instN):
        if fmt == 'xml':
            return "\t\t<%s name=\"%s\">"%(typeN,instN)
        else:
            raise TypeError("Cannot handle format: %s" % fmt)

    def beginIps(self, fmt):
        if fmt == 'xml':
            return "\t<ips>"
        else:
            raise TypeError("Cannot handle format: %s" % fmt)


    def beginParams(self, fmt):
        if fmt == 'xml':
            return "<simulation>"
        else:
            raise TypeError("Cannot handle format: %s" % fmt)

    def endParams(self, fmt):
        if fmt == 'xml':
            return "</simulation>"
        else:
            raise TypeError("Cannot handle format: %s" % fmt)

    def beginLinks(self, fmt):
        if fmt == 'xml':
            return "\t<links>"
        else:
            raise TypeError("Cannot handle format: %s" % fmt)

    def endLinks(self, fmt):
        if fmt == 'xml':
            return "\t</links>"
        else:
            raise TypeError("Cannot handle format: %s" % fmt)

    def endIp(self, fmt, name):
        if fmt == 'xml':
            return "\t\t</%s>" % name
        else:
            raise TypeError("Cannot handle format: %s" % fmt)

    def endIps(self, fmt):
        if fmt == 'xml':
            return "\t</ips>"
        else:
            raise TypeError("Cannot handle format: %s" % fmt)


    def endPlatform(self, fmt):
        if fmt == 'xml':
            return "</platform>"
        else:
            raise TypeError("Cannot handle format: %s" % fmt)

    def attr(self, fmt, key,val):
        if fmt == 'xml':
            return "\t\t\t<%s>%s</%s>" % (key,val,key)
        else:
            raise TypeError("Cannot handle format: %s" % fmt)

    def param(self, fmt, p):
        if fmt == 'xml':
            return p.toXml()
        else:
            raise TypeError("Cannot handle format: %s" % fmt)

    def link(self, fmt, iip,ip, oip, op):
        if fmt == 'xml':
            return "\t\t<link><from port=\"%s\">%s</from><to port=\"%s\">%s</to></link>"%(
                 ip,iip,op,oip)

        else:
            raise TypeError("Cannot handle format: %s" % fmt)



ka=[]
mo=-1
mi=-1
code=""
t="""
class %s(_ssmip):
    def __init__(self,name=None,sys=None,**X):
        if name is None:
            name=self.__class__.__name__+str(_autn[self.__class__.__name__])
            _autn[self.__class__.__name__]+=1%s
        _ssmip.__init__(self,name,X,sys)
        self._ka=%s
        self._mo=%s
        self._mi=%s


  """
for _l in subprocess.check_output([_ve,'--dump-components'],stderr=subprocess.STDOUT).decode().split('\n'):

    g=_l.split()
    if len(g):
        if g[0] == "begin_component":
            classname=g[1]
        elif g[0] == "optional_attr":
            ka.append(g[1])
            if len(g) < 3  :
                code+="""\n        setattr(self,\"%s\",\"%s\")"""%(g[1],'')
            else :
                code+="""\n        setattr(self,\"%s\",\"%s\")"""%(g[1],g[2])
        elif g[0] == "required_attr":
            ka.append(g[1])
        elif g[0] == "in_ports":
            mi=int(g[1])
        elif g[0] == "out_prts":
            mo=int(g[1])
        elif g[0] == "end_component":
            #print(t%(classname,code,ka,mo,mi))
            exec(t%(classname,code,ka,mo,mi))
            _autn[classname]=0
            ka=[]
            mo,mi=-1,-1
            code=""

