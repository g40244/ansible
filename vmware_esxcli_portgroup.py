#! /usr/bin/env python
# -*- coding: utf-8 -*-

from ansible.module_utils.basic import *

def main():
    module = AnsibleModule(
        dict(
            name=dict(required=True),
            vSwitch=dict(required=True),
            vlan=dict(default='0'),
            security=dict(type='dict'),
            shaping=dict(type='dict'),
            failover=dict(type='dict'),
            state=dict(choises=['present', 'absent'], default='present')
        )
    )

    name = module.params['name']
    vswitch = module.params['vSwitch']
    vlan = module.params['vlan']
    security = module.params['security']
    shaping = module.params['shaping']
    failover = module.params['failover']
    state = module.params['state']
    changed = False

    stdcmd = 'esxcli network vswitch standard portgroup'

    if state == 'present':
        rc, stdout, stderr = module.run_command(stdcmd + ' list | grep \'' + name + '\'', use_unsafe_shell=True)
        if rc == 1:
            rc, stdout, stderr = module.run_command(stdcmd + ' add -v \'' + vswitch + '\' -p \'' + name + '\'', use_unsafe_shell=True)
            if rc != 0:
                module.fail_json(
                    msg='[Error] add command "' + stdcmd + ' add -v \'' + vswitch + '\' -p \'' + name + '\'' + '" is failed.'
                )
            changed = True
        else:
            rc, stdout, stderr = module.run_command(stdcmd + ' list | grep \'' + name + '\' | awk \'{sub("' + name + '", ""); print}\' | sed \'s/  */ /g\' | awk \'{$(NF)="";$(NF-1)="";print}\'', use_unsafe_shell=True)
            now_vswitch = stdout[:-3]
            if now_vswitch != vswitch:
                rc, stdout, stderr = module.run_command(stdcmd + ' remove -v \'' + now_vswitch + '\' -p \'' + name + '\'', use_unsafe_shell=True)
                if rc != 0:
                    module.fail_json(
                        msg='[Error] remove command "' + stdcmd + ' remove -v \'' + now_vswitch + '\' -p \'' + name + '\'' + '"is failed.'
                    )
                rc, stdout, stderr = module.run_command(stdcmd + ' add -v \'' + vswitch + '\' -p \'' + name + '\'', use_unsafe_shell=True)
                if rc != 0:
                    module.fail_json(
                        msg='[Error] add command "' + stdcmd + ' add -v \'' + vswitch + '\' -p \'' + name + '\'' + '" is failed.'
                    )
                changed = True
        
        rc, stdout, stderr = module.run_command(stdcmd + ' list | grep \'' + name + '\' | sed \'s/  */ /g\' | awk \'{print $(NF)}\'', use_unsafe_shell=True)
        now_vlan = stdout[:-1]
        if now_vlan != vlan:
            rc, stdout, stderr = module.run_command(stdcmd + ' set -p \'' + name + '\' -v ' + vlan, use_unsafe_shell=True)
            if rc != 0:
                module.fail_json(
                    msg='[Error] set command "' + stdcmd + ' set -p \'' + name + '\' -v ' + vlan + '" is failed.'
                )
            changed = True
        
        rc, stdout, stderr = module.run_command(stdcmd + ' policy security get -p \'' + name + '\' | awk -F \': \' \'{print $2}\'', use_unsafe_shell=True)
        stdout_lines = stdout.splitlines()
        now_promiscuous = stdout_lines[0]
        now_mac = stdout_lines[1]
        now_forged = stdout_lines[2]
        now_override_p = stdout_lines[3]
        now_override_m = stdout_lines[4]
        now_override_f = stdout_lines[5]
        cmdopt = ''
        if security is not None:
            if 'promiscuous' in security:
                if security['promiscuous'].lower() == 'allow':
                    if now_promiscuous != 'true' or now_override_p == 'false':
                        cmdopt += ' -o true'
                elif security['promiscuous'].lower() == 'deny':
                    if now_promiscuous != 'false' or now_override_p == 'false':
                        cmdopt += ' -o false'
                else:
                    module.fail_json(
                        msg='[Error] security.promiscuous'
                    )
            if 'mac_change' in security:
                if security['mac_change'].lower() == 'allow':
                    if now_mac != 'true' or now_override_m == 'false':
                        cmdopt += ' -m true'
                elif security['mac_change'].lower() == 'deny':
                    if now_mac != 'false' or now_override_m == 'false':
                        cmdopt += ' -m false'
                else:
                    module.fail_json(
                        msg='[Error] security.mac_change'
                    )
            if 'forged_transmits' in security:
                if security['forged_transmits'].lower() == 'allow':
                    if now_forged != 'true' or now_override_f == 'false':
                        cmdopt += ' -f true'
                elif security['forged_transmits'].lower() == 'deny':
                    if now_forged != 'false' or now_override_f == 'false':
                        cmdopt += ' -f false'
                else:
                    module.fail_json(
                        msg='[Error] security.forged_transmits'
                    )
            if 'promiscuous' not in security and 'mac_change' not in security and 'forged_transmits' not in security:
                module.fail_json(
                    msg='[Error] security require promiscuous or mac_change or forged_transmits'
                )
        else:
            if now_override_p != 'false' or now_override_m != 'false' or now_override_f != 'false':
                cmdopt += ' -u'
        if cmdopt != '':
            rc, stdout, stderr = module.run_command(stdcmd + ' policy security set -p \'' + name + '\'' + cmdopt, use_unsafe_shell=True)
            if rc != 0:
                module.fail_json(
                    msg='[Error] set command "' + stdcmd + ' policy security set -p \'' + name + '\'' + cmdopt + '" is failed.'
                )
            changed = True
        
        rc, stdout, stderr = module.run_command(stdcmd + ' policy shaping get -p \'' + name + '\' | awk -F \': \' \'{print $2}\'', use_unsafe_shell=True)
        stdout_lines = stdout.splitlines()
        now_state = stdout_lines[0]
        now_override_s = stdout_lines[4]
        if shaping is not None:
            if 'state' in shaping:
                if shaping['state'].lower() == 'enabled':
                    if now_state != 'true' or now_override_s == 'false':
                        if 'avg_bandwidth' in shaping and 'peak_bandwidth' in shaping and 'burst_size' in shaping:
                            rc, stdout, stderr = module.run_command(stdcmd + ' policy shaping set -p \'' + name + '\' -e true' + ' -b ' + str(shaping['avg_bandwidth'] // 1000) + ' -k ' + str(shaping['peak_bandwidth'] // 1000) + ' -t ' + str(shaping['burst_size'] // 128), use_unsafe_shell=True)
                            if rc != 0:
                                module.fail_json(
                                    msg='[Error] set command "' + stdcmd + ' policy shaping set -p \'' + name + '\' -e true' + ' -b ' + str(shaping['avg_bandwidth'] // 1000) + ' -k ' + str(shaping['peak_bandwidth'] // 1000) + ' -t ' + str(shaping['burst_size'] // 128) + '" is failed.'
                                )
                            changed = True
                        else:
                            module.fail_json(
                                msg='[Error] If you change shaping state disable to enable or override, you have to define avg_bandwidth, peak_bandwidth, burst_size.'
                            )
                    else:
                        rc, stdout, stderr = module.run_command(stdcmd + ' policy shaping get -p \'' + name + '\' | grep -v Enabled | awk -F \': \' \'{print $2}\' | awk \'{print $1}\'', use_unsafe_shell=True)
                        stdout_lines = stdout.splitlines()
                        now_avg = stdout_lines[0]
                        now_peak = stdout_lines[1]
                        now_burst = stdout_lines[2]
                        cmdopt = ''
                        if 'avg_bandwidth' in shaping:
                            if int(now_avg) != shaping['avg_bandwidth'] // 1000:
                                cmdopt += ' -b ' + str(shaping['avg_bandwidth'] // 1000)
                        if 'peak_bandwidth' in shaping:
                            if int(now_peak) != shaping['peak_bandwidth'] // 1000:
                                cmdopt += ' -k ' + str(shaping['peak_bandwidth'] // 1000)
                        if 'burst_size' in shaping:
                            if int(now_burst) != shaping['burst_size'] // 128:
                                cmdopt += ' -t ' + str(shaping['burst_size'] // 128)
                        if cmdopt != '':
                            rc, stdout, stderr = module.run_command(stdcmd + ' policy shaping set -p \'' + name + '\'' + cmdopt, use_unsafe_shell=True)
                            if rc != 0:
                                module.fail_json(
                                    msg='[Error] set command "' + stdcmd + ' policy shaping set -p \'' + name + '\'' + cmdopt + '" is failed.'
                                )
                            changed = True
                elif shaping['state'].lower() == 'disabled':
                    if now_state != 'false' or now_override_s == 'false':
                        rc, stdout, stderr = module.run_command(stdcmd + ' policy shaping set -p \'' + name + '\' -e false', use_unsafe_shell=True)
                        if rc != 0:
                            module.fail_json(
                                msg='[Error] set command "' + stdcmd + ' policy shaping set -p \'' + name + '\' -e false' + '" is failed.'
                            )
                        changed = True
                else:
                    module.fail_json(
                        msg='[Error] shaping.state' 
                    )
            else:
                module.fail_json(
                    msg='[Error] shaping.state is required.'
                )
        else:
            if now_override_s != 'false':
                rc, stdout, stderr = module.run_command(stdcmd + ' policy shaping set -p \'' + name + '\' -u', use_unsafe_shell=True)
                if rc != 0:
                    module.fail_json(
                        msg='[Error] set command "' + stdcmd + ' policy shaping set -p \'' + name + '\' -u' + '" is failed.'
                    )
                changed = True

        rc, stdout, stderr = module.run_command(stdcmd + ' policy failover get -p \'' + name + '\' | awk -F \': \' \'{print $2}\'', use_unsafe_shell=True)
        stdout_lines = stdout.splitlines()
        now_loadbalance = stdout_lines[0]
        now_faildetect = stdout_lines[1]
        now_notifysw = stdout_lines[2]
        now_failback = stdout_lines[3]
        now_active = ','.join(sorted(stdout_lines[4].split(', ')))
        now_standby = ','.join(sorted(stdout_lines[5].split(', ')))
        now_unuse = ','.join(sorted(stdout_lines[6].split(', ')))
        now_override_lb = stdout_lines[7]
        now_override_fd = stdout_lines[8]
        now_override_ns = stdout_lines[9]
        now_override_fb = stdout_lines[10]
        now_override_ul = stdout_lines[11]
        cmdopt = ''
        if failover is not None:  
            if 'load_balancing' in failover:
                if now_loadbalance.lower() != failover['load_balancing'] or now_override_lb == 'false':
                    if failover['load_balancing'] == 'srcmac':
                        cmdopt += ' -l mac'
                    elif failover['load_balancing'] == 'srcport':
                        cmdopt += ' -l portid'
                    else:
                        if failover['load_balancing'] not in ['explicit', 'iphash']:
                            module.fail_json(
                                msg='[Error] failover.load_balancing'
                            )
                        cmdopt += ' -l ' + failover['load_balancing']
            if 'failure_detection' in failover:
                if now_faildetect.lower() != failover['failure_detection'] or now_override_fd == 'false':
                    if failover['failure_detection'] not in ['link', 'beacon']:
                        module.fail_json(
                            msg='[Error] failover.failure_detection'
                        )
                    cmdopt += ' -f ' + failover['failure_detection']
            if 'notify_switches' in failover:
                if failover['notify_switches'].lower() == 'yes':
                    if now_notifysw != 'true' or now_override_ns == 'false':
                        cmdopt += ' -n true'
                elif failover['notify_switches'].lower() == 'no':
                    if now_notifysw != 'false' or now_override_ns == 'false':
                        cmdopt += ' -n false'
                else:
                    module.fail_json(
                        msg='[Error] failover.notify_switches'
                    )
            if 'failback' in failover:
                if failover['failback'].lower() == 'yes':
                    if now_failback != 'true' or now_override_fb == 'false':
                        cmdopt += ' -b true'
                elif failover['failback'].lower() == 'no':
                    if now_failback != 'false' or now_override_fb == 'false':
                        cmdopt += ' -b false'
                else:
                    module.fail_json(
                        msg='[Error] failover.failback'
                    )
            if 'active_link' in failover and failover['active_link'] is not None:
                active_link = ','.join(sorted(failover['active_link']))
                if now_active != active_link or now_override_ul == 'false':
                    cmdopt += ' -a ' + active_link
            else:
                if now_active != "" or now_override_ul == 'false':
                    cmdopt += ' -a ""'
            if 'standby_link' in failover and failover['standby_link'] is not None:
                standby_link = ','.join(sorted(failover['standby_link']))
                if now_standby != standby_link or now_override_ul == 'false':
                    cmdopt += ' -s ' + standby_link
            else:
                if now_standby != "" or now_override_ul == 'false':
                    cmdopt += ' -s ""'
        else:
            if now_override_lb != 'false' or now_override_fd != 'false' or now_override_ns != 'false' or now_override_fb != 'false' or now_override_ul != 'false':
                cmdopt += ' -u'
        if cmdopt != '':
            rc, stdout, stderr = module.run_command(stdcmd + ' policy failover set -p \'' + name + '\'' + cmdopt, use_unsafe_shell=True)
            if rc != 0:
                module.fail_json(
                    msg='[Error] set command "' + stdcmd + ' policy failover set -p \'' + name + '\'' + cmdopt + '" is failed.'
                )
            changed = True

    elif state == 'absent':
        rc, stdout, stderr = module.run_command(stdcmd + ' list | grep \'' + name + '\'', use_unsafe_shell=True)
        if rc != 1:
            rc, stdout, stderr = module.run_command(stdcmd + ' remove -v \'' + now_vswitch + '\' -p \'' + name + '\'', use_unsafe_shell=True)
            if rc != 0:
                module.fail_json(
                    msg='[Error] remove command "' + stdcmd + ' remove -v \'' + now_vswitch + '\' -p \'' + name + '\'' + '" is failed.'
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
