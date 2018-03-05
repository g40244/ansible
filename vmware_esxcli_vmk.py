#! /usr/bin/env python
# -*- coding: utf-8 -*-

from ansible.module_utils.basic import *

def main():
    module = AnsibleModule(
        dict(
            name=dict(required=True),
            portgroup=dict(required=True),
            service_tag=dict(type='list'),
            mtu=dict(default='1500'),
            type=dict(choises=['dhcp', 'static', 'none']),
            ipv4=dict(),
            mask=dict(),
            gw=dict(default='0.0.0.0'),
            dhcpdns=dict(choises=['yes', 'no'], default='no'),
            state=dict(choises=['present', 'absent'], default='present')
        )
    )

    name = module.params['name']
    portgroup = module.params['portgroup']
    service_tag = module.params['service_tag']
    mtu = module.params['mtu']
    nwtype = module.params['type']
    ipv4 = module.params['ipv4']
    mask = module.params['mask']
    gw = module.params['gw']
    dhcpdns = module.params['dhcpdns']
    state = module.params['state']
    changed = False

    stdcmd = 'esxcli network ip interface'

    if state == 'present':
        rc, stdout, stderr = module.run_command(stdcmd + ' list | grep \'Name: ' + name + '\'', use_unsafe_shell=True)
        if rc == 1:
            rc, stdout, stderr = module.run_command(stdcmd + ' add -i \'' + name + '\' -p \'' + portgroup + '\'', use_unsafe_shell=True)
            if rc != 0:
                module.fail_json(
                    msg='[Error] add command "' + stdcmd + ' add -i \'' + name + '\' -p \'' + portgroup + '\'" is failed.'
                )
            changed = True
        else:
            rc, stdout, stderr = module.run_command(stdcmd + ' list | grep -e \'Name: ' + name + '\' -e Portgroup | grep -A 1 Name | awk -F \': \' \'{print $2}\'', use_unsafe_shell=True)
            stdout_lines = stdout.splitlines()
            now_portgroup = stdout_lines[1]
            if now_portgroup != portgroup:
                rc, stdout, stderr = module.run_command(stdcmd + ' remove -i \'' + name + '\'' , use_unsafe_shell=True)
                if rc != 0:
                    module.fail_json(
                        msg='[Error] remove command "' + stdcmd + ' remove -i \'' + name + '\'' + '" is failed.'
                    )
                rc, stdout, stderr = module.run_command(stdcmd + ' add -i \'' + name + '\' -p \'' + portgroup + '\'', use_unsafe_shell=True)
                if rc != 0:
                    module.fail_json(
                        msg='[Error] add command "' + stdcmd + ' add -i \'' + name + '\' -p \'' + portgroup + '\'" is failed.'
                    )
                changed = True

        if service_tag is not None:
            service_tag = sorted(service_tag)
            service_tag_list = ['VMotion', 'vSphereProvisioning', 'faultToleranceLogging', 'Management', 'vSphereReplication', 'vSphereReplicationNFC', 'VSAN', 'VSANWitness']
            rc, stdout, stderr = module.run_command(stdcmd + ' tag get -i \'' + name + '\' | awk -F \': \' \'{print $2}\'', use_unsafe_shell=True)
            now_service_tag = sorted(stdout[:-1].split(', '))
            if now_service_tag != service_tag:
                err_tag = [i for i in service_tag if i not in service_tag_list]
                if err_tag != []:
                    module.fail_json(
                        msg='[Error] service_tag contain error tags "' + ', '.join(err_tag) + '"'
                    )
                else:
                    for tag in list(set(service_tag) - set(now_service_tag)):
                        if tag != "":
                            rc, stdout, stderr = module.run_command(stdcmd + ' tag add -i \'' + name + '\' -t ' + tag, use_unsafe_shell=True)
                            if rc != 0:
                                module.fail_json(
                                    msg='[Error] add command "' + stdcmd + ' tag add -i \'' + name + '\' -t ' + tag + '" is failed.'
                                )
                    for tag in list(set(now_service_tag) - set(service_tag)):
                        if tag != "":
                            rc, stdout, stderr = module.run_command(stdcmd + ' tag remove -i \'' + name + '\' -t ' + tag, use_unsafe_shell=True)
                            if rc != 0:
                                module.fail_json(
                                    msg='[Error] remove command "' + stdcmd + ' tag remove -i \'' + name + '\' -t ' + tag + '" is failed.'
                                )
                    changed = True

        rc, stdout, stderr = module.run_command(stdcmd + ' list | grep -e \'Name: ' + name + '\' -e MTU | grep -A 1 Name | awk -F \': \' \'{print $2}\'', use_unsafe_shell=True)  
        stdout_lines = stdout.splitlines()
        now_mtu = stdout_lines[1]
        if now_mtu != mtu:
            rc, stdout, stderr = module.run_command(stdcmd + ' set -i \'' + name + '\' -m ' + mtu, use_unsafe_shell=True)
            if rc != 0:
                module.fail_json(
                    msg='[Error] set command "' + stdcmd + ' set -i \'' + name + '\' -m ' + mtu + '" is failed.'
                )
            changed = True
        
        if nwtype is not None:
            rc, stdout, stderr = module.run_command(stdcmd + ' ipv4 get | grep \'' + name + '\' | sed \'s/  */ /g\'', use_unsafe_shell=True)
            stdout_lines = stdout.split()
            now_ipv4 = stdout_lines[1]
            now_mask = stdout_lines[2]
            now_nwtype = stdout_lines[4].lower()
            now_gw = stdout_lines[5]
            now_dhcpdns = stdout_lines[6]
            cmdopt = ''
            if nwtype == 'dhcp':
                if now_nwtype != nwtype:
                    cmdopt += ' -t dhcp'
                if dhcpdns == 'yes' and now_dhcpdns != 'true':
                    cmdopt += ' -P true'
                elif dhcpdns == 'no' and now_dhcpdns != 'false':
                    cmdopt += ' -P false'
            if nwtype == 'none' and now_nwtype != nwtype:
                cmdopt += ' -t none'
            if nwtype == 'static':
                if ipv4 is None or mask is None:
                    module.fail_json(
                        msg='[Error] type static require ipv4 and mask.'
                    )
                if now_nwtype != nwtype or now_ipv4 != ipv4 or now_mask != mask or now_gw != gw:
                    cmdopt += ' -t static -I ' + ipv4 + ' -N ' + mask + ' -g ' + gw
            if cmdopt != '':
                rc, stdout, stderr = module.run_command(stdcmd + ' ipv4 set -i \'' + name + '\'' + cmdopt, use_unsafe_shell=True)
                if rc != 0:
                    module.fail_json(
                        msg='[Error] set command "' + stdcmd + ' ipv4 set -i \'' + name + '\'' + cmdopt + '" is failed.'
                    )
                changed = True

    elif state == 'absent':
        rc, stdout, stderr = module.run_command(stdcmd + ' list | grep \'Name: ' + name + '\'', use_unsafe_shell=True)
        if rc != 1:
            rc, stdout, stderr = module.run_command(stdcmd + ' remove -i \'' + name + '\'', use_unsafe_shell=True)
            if rc != 0:
                module.fail_json(
                    msg='[Error] remove command "' + stdcmd + ' remove -i \'' + name + '\'" is failed.'
                )
            changed = True
    
    else:
        module.fail_json(
            msg='[Error] state'
        )
    
    module.exit_json(
        changed=changed
    )

if __name__ == '__main__':
    main()
