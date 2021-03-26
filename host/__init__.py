from platform import system
from subprocess import check_output, getoutput, CalledProcessError
from os import getenv
from sys import argv
import re
import psutil

space_regexp = '\s{2,}'

def __get_wmic_property__(component="", property="", nic=False, node=f'/NODE:"{getenv("computername")}"'):
    '''
    Uses subprocess to query WMIC for information.\n
    Parameters:\n
    :component (str): Which WMI component to query.\n
    :property (str): Which property of a WMI component to get.\n
    __get_wmic_property__(`component`, `property`) -> str
    '''
    if component=="" or property=="":
        print("Component and Property cannont be empty!")
        return None
    elif system() != "Windows":
        return f"Windows Management Istrumentation is not available on {system()}"
    else:
        if nic:
            cmd = f"WMIC {str(node)} {str(component)} GET {str(property)} | FINDSTR /i /v \"{str(property)} WAN RAS TAP TAP-Windows Generic\""    
        else:
            cmd = f"WMIC {str(node)} {str(component)} GET {str(property)} | FINDSTR /i /v {str(property)}"
        value = check_output(cmd, shell=True).decode().replace(str(property), "")
        for a in argv:
            if '--debug=true' == a.lower():
                print(cmd)
                print(value)
        return value

def __conv_size__(size=0.0):
    '''
    Dynamically covert the size of a float to the correct unit.\n
    Paramerters:\n
    :size (float): Size in bytes.\n
    __conv_size__(size) -> str
    '''
    size = float(size)
    conv = 1024.0
    unit = {
        0: "KB",
        1: "MB",
        2: "GB",
        3: "TB",
        4: "PB",
        5: "EB",
        6: "ZB",
        7: "YB"
    }
    loop = 0
    while size >= 1024:
        size = size/1024
        loop += 1
    return f"{size:.2f} {unit[loop]}"

class Host():
    '''
    Class to represent a host systems specs.\n
    Methods:\n
    __init__(opsys=system()) -> Host\n
    get_cpu() -> str\n
    get_ram() -> str\n
    get_gpu() -> str\n
    get_nic() -> str\n
    get_mobo() -> str\n
    get_disk() -> str\n
    get_os() -> str\n
    get_hostname() -> str
    '''
    def __init__(self, opsys=system(), hostname=getenv('computername')):
        '''
        Create an instance of the class Host.\n
        Parameters:\n
        :opsys (str): Default is platform.system()\n
        :hostname (str): Hostname of the machine to run WMIC. Default is current hostname.\n
        __init__() -> Host
        '''
        self.os = opsys
        if self.os == "Windows":
            self.wmic = __get_wmic_property__
            self.node = f"/NODE:\"{hostname}\""

    def get_cpu(self, bare=False):
        '''
        Get the count and name of the CPU(s) installed in the system.\n
        Paramerters:\n
        :bare (bool): Set to True to use bare formatting.\n
        get_cpu() -> str
        '''
        if self.os != "Windows":
            return f"Windows Management Instrumentation is no available on {self.os}"
        val = __get_wmic_property__('cpu', 'name', node=self.node).replace('\r', '').strip().split('\n')
        for i in range(len(val)):
            val[i] = re.sub(space_regexp, '', val[i])
        if len(val) > 1:
            val = f"2x {val[0].replace('CPU ', '')}"
        else:
            val = f"   {val[0].replace('CPU ', '')}"
        if bare:
            val = re.sub(space_regexp, '', val.replace('(TM)', '').replace('(R)', '').replace('Intel ', '').replace('AMD ', ''))
            return val
        return f"CPU:\n{val}"

    def get_ram(self, val=psutil.virtual_memory().total/1024/1024, unit="GB"):
        '''
        Get the total amount of RAM installed in the system.\n
        Paramerters:\n
        :val (int): The total amout of memory. Has default value!!!\n
        :unit (str): Which unit to return the amout in. Default: GB\n
        get_ram() -> str
        '''
        if self.os != "Windows":
            return f"Windows Management Instrumentation is no available on {self.os}"
        val = int(__get_wmic_property__('OS', 'TotalVirtualMemorySize', node=self.node))//1024
        for g in range(1, 4097):
            gg = g * 1024
            if val > gg - 512 and val < gg + 511:
                if unit.upper() == "MB":
                    return f"RAM:\n   {gg} MB"
                elif unit.upper() == "GB":
                    return f"RAM:\n   {gg/1024} GB"

    def get_gpu(self, bare=False):
        '''
        Get the name and count of all GPU(s) in the system.\n
        Paramerters:\n
        :bare (bool): Set to True to use first GPU in a bare format.\n
        get_gpu() -> str
        '''
        if self.os != "Windows":
            return f"Windows Management Instrumentation is no available on {self.os}"
        val = __get_wmic_property__('PATH Win32_videoController', 'name', node=self.node).replace('\r', '').strip().split('\n')
        result = dict()
        for i in range(len(val)):
            val[i] = re.sub(space_regexp, '', val[i])
        for gpu in val:
            if gpu in result.keys():
                result[gpu] += 1
            else:
                result[gpu] = 1
        result_str = "GPU:\n"
        for k, v in result.items():
            if v == 1:
                result_str += f"   {k}\n"
            else:
                result_str += f"{v}x {k}\n"
        if bare:
            result_str = re.sub(space_regexp, '', result_str.split('\n')[1].replace('NVIDIA ', '') .replace('AMD ', '').replace('INTEL ', '').replace('Intel(R)', ''))
            return result_str
        return result_str[:-1]

    def get_nic(self):
        '''
        Get the name and count of all the NIC(s) in the system.\n
        Paramerters:\n
        None\n
        get_nic() -> str
        '''
        if self.os != "Windows":
            return f"Windows Management Instrumentation is no available on {self.os}"
        val = __get_wmic_property__('NIC', 'Name', True, node=self.node).replace('\r', '').strip().split('\n')
        result = dict()
        for i in range(len(val)):
            val[i] = re.sub(space_regexp, '', val[i])
        for nic in val:
            if nic in result.keys():
                result[nic] += 1
            else:
                result[nic] = 1
        result_str = "NIC:\n"
        for k, v in result.items():
            if v == 1:
                result_str += f"   {k}\n"
            else:
                result_str += f"{v}x {k}\n"
        return result_str[:-1]

    def get_mobo(self):
        '''
        Get the manufaturer and model of the motherboard.\n
        Paramerters:\n
        None\n
        get_mobo() -> str
        '''
        if self.os != "Windows":
            return f"Windows Management Instrumentation is no available on {self.os}"
        manufacturer = __get_wmic_property__('BaseBoard', 'Manufacturer', node=self.node).replace('\r', '').strip()
        val = __get_wmic_property__('BaseBoard', 'Product', node=self.node).replace('\r', '').strip().split('\n')
        for i in range(len(val)):
            val[i] = re.sub(space_regexp, '', val[i])
        val = val[i]
        return f"Motherboard:\n   {manufacturer}:\t{val}"

    def get_disk(self):
        '''
        Get the disk model, size and count of the disks installed in the system, excluding *generic* models.\n
        Paramerters:\n
        None\n
        get_disk() -> str
        '''
        if self.os != "Windows":
            return f"Windows Management Instrumentation is no available on {self.os}"
        model = __get_wmic_property__('DiskDrive', 'Model', True, node=self.node).replace('\r', '').strip().split('\n')
        size = __get_wmic_property__('DiskDrive', 'Size', node=self.node).replace('\r', '').strip().split('\n')
        result = dict()
        longet_model = 0
        for i in range(len(model)):
            if len(model[i]) > longet_model:
                longet_model = len(model[i])
        for i in range(len(model)):
            model[i] = re.sub(space_regexp, '', model[i])
            size[i] = str(__conv_size__(float(re.sub(space_regexp, '', size[i]))/(1024)))
            k = f"{model[i].ljust(longet_model+4)} {size[i]}"
            if k in result.keys():
                result[k] += 1
            else:
                result[k] = 1
        result_str = "Disks:\n"
        for k, v in result.items():
            if v == 1:
                result_str += f"   {k}\n"
            else:
                result_str += f"{v}x {k}\n"
        return result_str[:-1]

    def get_os(self):
        '''
        Get the name of the OS the application is running on.\n
        Paramerters:\n
        None\n
        get_os() -> str
        '''
        if self.os != "Windows":
            return f"Windows Management Instrumentation is no available on {self.os}"
        val = __get_wmic_property__('os', 'caption', node=self.node).replace('\r', '').strip().split('\n')
        for i in range(len(val)):
            val[i] = re.sub(space_regexp, '', val[i])
        if len(val) > 1:
            val = f"2x {val[0]}"
        else:
            val = f"{val[0]}"
        return f"OS:\n   {val}"

    def get_hostname(self):
        '''
        Get the hostname of the system the applications is running on.\n
        Parameteres:\n
        None\n
        get_hostname() -> str
        '''
        if self.os != "Windows":
            return f"Windows Management Instrumentation is no available on {self.os}"
        hostname = re.sub(space_regexp, '', __get_wmic_property__('computersystem', 'caption', node=self.node).replace('\r', '').replace('\n', ''))
        domainname = re.sub(space_regexp, '', __get_wmic_property__('computersystem', 'domain', node=self.node).replace('\r', '').replace('\n', ''))
        return f"Host:\n   {hostname}.{domainname}"

if __name__ == "__main__":
    if len(argv) >= 2:
        host = Host(hostname=str(argv[1]))
    else:
        host = Host()
    print(host.get_cpu())
    print(host.get_disk())
    print(host.get_gpu())
    print(host.get_hostname())
    print(host.get_mobo())
    print(host.get_nic())
    print(host.get_os())
    print(host.get_ram())