#!/usr/bin/python3
# encoding: utf-8

import os
import re
import sys
import concurrent.futures as futures
from pylib.env import set_debug, is_debug
from pylib.printer import iterate_print
from pylib.proc import read_per_line, print_per_line
from pylib.transformer import str_to_dict
from pylib.dec import handlers
import pickle

dir = os.path.dirname(os.path.realpath(__file__))


class Base:

    def __init__(self):
        self.info_by_vms = {}
        self.vagrant_global_info = {}
        self.vagrant_global_info_keys = ['id', 'name', 'provider', 'state', 'directory']

    def get_vms(self):
        if hasattr(self, 'vms'):
            return self.vms
        list = str(os.popen("vboxmanage list vms | awk '{print $1}' | sed -r 's/\"//g'").read()).splitlines()
        list = [vm for vm in list if vm not in ['<inaccessible>']]
        self.vms = list
        return list

    def get_groups(self):
        if hasattr(self, 'groups'):
            return self.groups
        self.groups = str(os.popen('vboxmanage list groups').read()).replace('"', '').splitlines()
        return self.groups

    def get_info_by_groups(self):
        if hasattr(self, 'info_by_groups'):
            return self.info_by_groups
        info_by_groups = {group: {} for group in self.get_groups()}
        info_by_groups['not_valid'] = {}

        def __put_vm_to_group(vm):
            info_vm = self.get_vm_info(vm)
            group = info_vm['group']
            if group in info_by_groups:
                info_by_groups[group][vm] = info_vm
            else:
                info_by_groups['not_valid'][vm] = info_vm

        with futures.ThreadPoolExecutor(max_workers=4) as ex:
            ex.map(__put_vm_to_group, self.get_vms())
        self.info_by_groups = info_by_groups
        return info_by_groups

    def get_running_vms(self):
        if hasattr(self, 'running_vms'):
            return self.running_vms
        self.running_vms = str(os.popen("vboxmanage list runningvms | awk '{print $1}' | sed -r 's/\"//g'").read()).splitlines()
        return self.running_vms

    def find_group_of_vm(self, vm):
        return re.sub(r'Groups:[\s]*', '', str(os.popen("vboxmanage showvminfo %s | grep Groups:" % vm).read())).strip()

    def print_vm_info(self, iter_count, vm, info={}):
        info = self.get_vm_info(vm) if not info else info
        print('%s%s:' % ((iter_count - 1) * 4 * " ", vm))
        for _info_key in ['group', 'state', 'ip', 'hardware', 'vagrant', 'config_file', 'storage_file', 'shared_dir',
                          'port_forwarding']:
            iterate_print(iter_count, 4 * " ", _info_key, info.get(_info_key, ''))
        print('\n')

    def try_get_vagrant_id(self, vm):
        if self.get_vm_info(vm).get('vagrant', False):
            vagrant_vm = self.get_vagrant_global_info().get(vm, {})
            if vagrant_vm and vagrant_vm['id']:
                return vagrant_vm['id']
        return None

    def get_group_vm_rels(self):
        if hasattr(self, 'group_vm_rels'):
            return self.group_vm_rels
        vm_group_rel = {}
        rs = []
        for vm in self.get_vms():
            r, w = os.pipe()
            c = os.fork()
            if c:
                rs.append(r)
            else:
                p = (vm, self.find_group_of_vm(vm))
                os.write(w, pickle.dumps(p))
                os.close(w)
                sys.exit(0)
        for r in rs:
            vm, group = pickle.loads(os.read(r, 1000))
            if group in vm_group_rel:
                vm_group_rel[group].append(vm)
            else:
                vm_group_rel[group] = [vm]
            os.close(r)
        self.group_vm_rels = vm_group_rel
        return self.group_vm_rels

    def get_systemd_vms(self):
        if hasattr(self, 'systemd_vms'):
            return self.systemd_vms
        self.systemd_vms = str(os.popen("sudo systemctl list-units | grep autostart_vm@ | awk '{print $1}'")
                               .read()).splitlines()
        return self.systemd_vms

    def get_vagrant_vms(self):
        if hasattr(self, 'vagrant_vms'):
            return self.vagrant_vms
        self.vagrant_vms = {}
        with os.popen('vagrant global-status | egrep -w \'^[a-z0-9]{7} \' | awk \'{print $1" "$2}\'') as p:
            for line in str(p.read()).splitlines():
                items = line.split()
                self.vagrant_vms[items[1]] = items[0]
        return self.vagrant_vms

    def get_vagrant_global_info(self):
        if hasattr(self, 'vagrant_global_info'):
            return self.vagrant_global_info
        info_start = False
        for line in read_per_line('vagrant global-status'):
            if re.compile(r'[-]*').match(line).group():
                info_start = True
                continue
            if not line:
                break
            if info_start:
                items = line.split()
                if items:
                    box_info = {
                        'id': items[0],
                        'name': items[1],
                        'provider': items[2],
                        'state': items[3],
                        'directory': items[4],
                    }
                    for key in ['id', 'name', 'provider', 'state', 'directory']:
                        self.vagrant_global_info.setdefault(key, {})
                        self.vagrant_global_info[key][box_info[key]] = box_info
        return self.vagrant_global_info

    def get_vm_info(self, vm):
        if vm in self.info_by_vms:
            return self.info_by_vms[vm]
        info_vm = {'vm': vm}
        info_vm['shared_dir'] = []
        info_vm['storage_file'] = []
        info_vm['port_forwarding'] = {}
        info_vm['hardware'] = {}
        info_vm['ip'] = {}
        for nic_num in range(10):
            value = str(os.popen(
                "VBoxManage guestproperty get \"%s\" /VirtualBox/GuestInfo/Net/%s/V4/IP | awk '{ print $2 }'" % (
                    vm, nic_num)).read()).strip()
            if value == 'value':
                break
            else:
                info_vm['ip']['NIC(%s)' % nic_num] = value
        for line in read_per_line("VBoxManage showvminfo %s" % vm):
            line_raw = str(line)
            if "Number of CPUs" in line_raw:
                info_vm['hardware']['cpu'] = line_raw.split(':')[1].strip()
            if "Memory size" in line_raw:
                info_vm['hardware']['ram'] = line_raw.split(':')[1].strip()
            if "Config file" in line_raw:
                info_vm['config_file'] = re.sub(r'Config file:[\s]*', '', line_raw)
            if any(key_word in line_raw for key_word in ['vdi', 'vmdk']):
                storage_info = re.sub(r'[a-zA-Z\s]*\([\d]+.[\s]*[\d]+\):[\s]*', '', line_raw)
                storage_info = re.sub(r'\(UUID: [0-9a-zA-Z-]*\)', '', storage_info)
                info_vm['storage_file'].append(storage_info)
            if "State:" in line_raw:
                state = re.sub(r'[0]{2,}', '', re.sub(r'State:[\s]*', '', line_raw))
                state = state.replace('.)', ')') if state.endswith('.)') else state
                info_vm['state'] = state
            if re.search(r'NIC[\s]*[\d]*[\s]*Rule', line_raw):
                d_key, d = str_to_dict(re.sub(r'NIC[\s]*[\d]*[\s]*Rule\([\d]*\):[\s]*', '', line_raw),
                                       key_by_value_of='name')
                info_vm['port_forwarding'][d_key] = d
            if "Groups:" in line_raw:
                info_vm['group'] = re.sub(r'Groups:[\s]*', '', line_raw)
            if "Name" in line_raw and "Host path" in line_raw:
                guest_dir = line_raw.split(',')[0].split(':')[1].replace('\'', '').strip()
                host_path = line_raw.split(',')[1].split(':')[1].replace('\'', '').strip().split()[0]
                mod = line_raw.split(',')[2].strip()
                info_vm['shared_dir'].append('%s: %s <- %s' % (mod, guest_dir, host_path))
                if "vagrant" in line_raw:
                    v_info = self.get_vagrant_global_info() # self.get_vagrant_global_info(key_by=['name', 'directory'])
                    # 优先用vagrant目录做关联，比较靠谱，vagrant的vm_name（由vm_define定义, 默认为'default'）与virtualbox的vbox_name不一定一致
                    info_vm['vagrant'] = v_info.get(host_path, v_info.get(vm, {}))

        self.info_by_vms[vm] = info_vm
        return self.info_by_vms[vm]


@handlers
class GroupCMD(Base):
    def __init__(self, args):
        Base.__init__(self)
        self.cmd = args[0]
        self.args = args[1:]

    # usage: vm group all
    def do_all(self):
        for group in self.get_groups():
            print(group)

    # usage: vm group info ${group}
    def do_info(self):
        self.group = '/' + self.args[0]
        if self.group in self.get_groups():
            print("%s:" % self.group)
            for vm, info in self.get_info_by_groups()[self.group].items():
                self.print_vm_info(2, vm, info)
            print("\n")
        else:
            print('group:\'%s\' not found' % self.group)

    # usage: vm group vms ${group}
    def do_vms(self):
        self.group = '/' + self.args[0]
        if self.group in self.get_group_vm_rels():
            iterate_print(0, 4 * " ", self.group, self.get_group_vm_rels()[self.group])
            print('\n')
        else:
            print('group:\'%s\' not found' % self.group)

@handlers
class VmCMD(Base):
    def __init__(self, args):
        Base.__init__(self)
        self.cmd = args[0]
        self.args = args[1:]

    # usage: vm init ${vm} ...
    def do_init(self):
        default = 'vagrant-node'
        self.vms = ['vagrant-' + name for name in self.args] if self.args else [default]
        for vm in self.vms:
            os.popen('rm -rf %s' % ('./' + vm))
            os.popen('cp -r %s ./%s' % (dir + '/' + default, vm))
            os.popen('cd ./%s && mv vmconfig_template.yml vmconfig.yml' % vm)

    # usage: vm start ${vm} ...
    def do_start(self):
        self.vms = self.args
        for vm in self.vms:
            if vm in self.get_vms():
                if vm in self.get_vagrant_vms():
                    print_per_line('vagrant up %s' % self.get_vagrant_vms()[vm])
                else:
                    os.popen('vboxmanage startvm %s --type headless' % vm)

    # usage: vm stop ${vm} ...
    def do_stop(self):
        self.vms = self.args
        for vm in self.vms:
            if vm in self.get_vms():
                if vm in self.get_vagrant_vms():
                    print_per_line('vagrant halt %s' % self.get_vagrant_vms()[vm])
                else:
                    os.popen('vboxmanage controlvm %s poweroff' % vm)

    # usage: vm enable ${vm} ...
    def do_enable(self):
        self.vms = self.args
        for vm in self.vms:
            if vm in self.get_vms():
                os.popen('sudo systemctl enable autostart_vm@%s' % vm)

    # usage: vm disable ${vm} ...
    def do_disable(self):
        self.vms = self.args
        for vm in self.vms:
            if vm in self.get_vms():
                os.popen('sudo systemctl disable autostart_vm@%s' % vm)

    # usage: vm rm ${vm} ...
    def do_rm(self):
        self.vms = self.args
        for vm in self.vms:
            if vm in self.get_vms():
                if self.get_vm_info(vm).get('vagrant', False):
                    vagrant_vm = self.get_vagrant_global_info().get(vm, {})
                    if vagrant_vm and vagrant_vm['id']:
                        print_per_line('vagrant halt %s' % vagrant_vm['id'])
                        print_per_line('vagrant destroy -f %s' % vagrant_vm['id'])
                print_per_line('vboxmanage controlvm %s poweroff' % vm)
                print_per_line('vboxmanage unregistervm %s --delete' % vm)
            else:
                print('vm:%s not found' % self.vm)

    # usage: vm info ${vm} => show info of one vm
    def do_info(self):
        self.vm = self.args[0]
        if self.vm in self.get_vms():
            self.print_vm_info(iter_count=1, vm=self.vm)
        else:
            print('vm:\'%s\' not found' % self.vm)

    # usage: vm all => list all vms
    def do_all(self):
        for vm in self.get_vms():
            print(vm)

    # usage: vm running
    def do_list_running_vms(self):
        for vm in self.get_running_vms():
            print(vm)



if __name__ == '__main__':
    # if not str(os.popen('which vagrant').read()):
    #     return {}
    # if '--debug' in func_args:
    #     func_args.remove('--debug')
    #     print(is_debug())
    #     set_debug(True)
    #     print(is_debug())
    if 'group' == sys.argv[1]:
        g = GroupCMD(sys.argv[2:]).handle()
    else:
        g = VmCMD(sys.argv[1:]).handle()
