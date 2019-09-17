
import os

# default: copy the (dummy) vagrant-node folder to current dir
def folder_template_provider(vms):
    default_folder_name = 'vagrant-node'
    vms = ['vagrant-' + name for name in vms] if vms else [default_folder_name]
    for vm in vms:
        cmd = '(rm -rf %s || true ) && cp -r %s ./%s && mv ./%s/vmconfig_template.yml ./%s/vmconfig.yml'
        os.popen(cmd % ('./' + vm, default_folder_name + '/' + default_folder_name, vm, vm, vm))



# clone a git repo to current path, which holds your vagrant template and scripts
def git_repo_template_provider(vms):
    default_folder_name = 'vagrant-node'
    vms = ['vagrant-' + name for name in vms] if vms else [default_folder_name]
    for vm in vms:
        cmd = 'git clone git@gitlab.aj:ajjiangxin/node.git && mv node %s && cp %s/properties_template.yml %s/properties.yml'
        os.popen(cmd % (vm, vm, vm))



# a method to init vagrantfile on current path (where vman executes)
default_provider = folder_template_provider
init_vagrant_vms = git_repo_template_provider
