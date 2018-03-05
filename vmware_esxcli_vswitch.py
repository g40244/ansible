#! /usr/bin/env python
# -*- coding: utf-8 -*-

from ansible.module_utils.basic import *

def main():
    module = AnsibleModule(
        dict(
            name=dict(required=True),
            mtu=dict(default='1500'),
            security=dict(type='dict'),
            shaping=dict(type='dict'),
            failover=dict(type='dict'),
            state=dict(choises=['present', 'absent'], default='present')
        )
    )

    name = module.params['name']
    mtu = module.params['mtu']
    security = module.params['security']
    shaping = module.params['shaping']
    failover = module.params['failover']
    state = module.params['state']
    changed = False

    stdcmd = 'esxcli network vswitch standard'

    if state == 'present':
        rc, stdout, stderr = module.run_command(stdcmd + ' list | grep \'Name: ' + name + '\'', use_unsafe_shell=True)
        if rc == 1:
            if mtu == '1500':
                port = '128'
            else:
                port = '1024'
            rc, stdout, stderr = module.run_command(stdcmd + ' add -v \'' + name + '\' -P ' + port, use_unsafe_shell=True)
            if rc != 0:
                module.fail_json(
                    msg='[Error] add command "' + stdcmd + ' add -v \'' + name + '\' -P ' + port + '" is failed.'
                )
            changed = True
        else:
            rc, stdout, stderr = module.run_command(stdcmd + ' list -v \'' + name + '\' | grep \'Configured Ports\' | awk -F \': \' \'{print $2}\'', use_unsafe_shell=True)
            now_port = stdout[:-1]
            change_port = False
            if mtu == '1500' and now_port != '128':
                change_port = True
                port = '128'
            elif mtu == '9000' and now_port != '1024':
                change_port = True
                port = '1024'
            if change_port:
                rc, stdout, stderr = module.run_command(stdcmd + ' remove -v \'' + name + '\'' , use_unsafe_shell=True)
                if rc != 0:
                    module.fail_json(
                        msg='[Error] remove command "' + stdcmd + ' remove -v \'' + name + '\'' + '" is failed.'
                    )
                rc, stdout, stderr = module.run_command(stdcmd + ' add -v \'' + name + '\' -P ' + port, use_unsafe_shell=True)
                if rc != 0:
                    module.fail_json(
                        msg='[Error] add command "' + stdcmd + ' add -v \'' + name + '\' -P ' + port + '" is failed.'
                    )
                changed = True

        rc, stdout, stderr = module.run_command(stdcmd + ' list -v \'' + name + '\' | grep MTU | awk -F \': \' \'{print $2}\'', use_unsafe_shell=True)
        now_mtu = stdout[:-1]
        if now_mtu != mtu:
            rc, stdout, stderr = module.run_command(stdcmd + ' set -v \'' + name + '\' -m ' + mtu, use_unsafe_shell=True)
            if rc != 0:
                module.fail_json(
                    msg='[Error] set command "' + stdcmd + ' set -v \'' + name + '\' -m ' + mtu + '" is failed.'
                )
            changed = True
        
        if security is not None:
            rc, stdout, stderr = module.run_command(stdcmd + ' policy security get -v \'' + name + '\' | awk -F \': \' \'{print $2}\'', use_unsafe_shell=True)
            stdout_lines = stdout.splitlines()
            now_promiscuous = stdout_lines[0]
            now_mac = stdout_lines[1]
            now_forged = stdout_lines[2]
            cmdopt = ''
            if 'promiscuous' in security:
                if security['promiscuous'].lower() == 'allow':
                    if now_promiscuous != 'true':
                        cmdopt += ' -p true'
                elif security['promiscuous'].lower() == 'deny':
                    if now_promiscuous != 'false':
                        cmdopt += ' -p false'
                else:
                    module.fail_json(
                        msg='[Error] security.promiscuous'
                    )
            if 'mac_change' in security:
                if security['mac_change'].lower() == 'allow':
                    if now_mac != 'true':
                        cmdopt += ' -m true'
                elif security['mac_change'].lower() == 'deny':
                    if now_mac != 'false':
                        cmdopt += ' -m false'
                else:
                    module.fail_json(
                        msg='[Error] security.mac_change'
                    )
            if 'forged_transmits' in security:
                if security['forged_transmits'].lower() == 'allow':
                    if now_forged != 'true':
                        cmdopt += ' -f true'
                elif security['forged_transmits'].lower() == 'deny':
                    if now_forged != 'false':
                        cmdopt += ' -f false'
                else:
                    module.fail_json(
                        msg='[Error] security.forged_transmits'
                    )
            if cmdopt != '':
                rc, stdout, stderr = module.run_command(stdcmd + ' policy security set -v \'' + name + '\'' + cmdopt, use_unsafe_shell=True)
                if rc != 0:
                    module.fail_json(
                        msg='[Error] set command "' + stdcmd + ' policy security set -v \'' + name + '\'' + cmdopt + '" is failed.'
                    )
                changed = True
            
        if shaping is not None:
            rc, stdout, stderr = module.run_command(stdcmd + ' policy shaping get -v \'' + name + '\' | grep Enabled | awk -F \': \' \'{print $2}\'', use_unsafe_shell=True)
            now_state = stdout[:-1]
            if 'state' in shaping:
                if shaping['state'].lower() == 'enabled':
                    if now_state != 'true':
                        if 'avg_bandwidth' in shaping and 'peak_bandwidth' in shaping and 'burst_size' in shaping:
                            rc, stdout, stderr = module.run_command(stdcmd + ' policy shaping set -v \'' + name + '\' -e true' + ' -b ' + str(shaping['avg_bandwidth'] // 1000) + ' -k ' + str(shaping['peak_bandwidth'] // 1000) + ' -t ' + str(shaping['burst_size'] // 128), use_unsafe_shell=True)
                            if rc != 0:
                                module.fail_json(
                                    msg='[Error] set command "' + stdcmd + ' policy shaping set -v \'' + name + '\' -e true' + ' -b ' + str(shaping['avg_bandwidth'] // 1000) + ' -k ' + str(shaping['peak_bandwidth'] // 1000) + ' -t ' + str(shaping['burst_size'] // 128) + '" is failed.'
                                )
                            changed = True
                        else:
                            module.fail_json(
                                msg='[Error] If you change shaping state disable to enable, you have to define avg_bandwidth, peak_bandwidth, burst_size.'
                            )
                    else:
                        rc, stdout, stderr = module.run_command(stdcmd + ' policy shaping get -v \'' + name + '\' | grep -v Enabled | awk -F \': \' \'{print $2}\' | awk \'{print $1}\'', use_unsafe_shell=True)
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
                            rc, stdout, stderr = module.run_command(stdcmd + ' policy shaping set -v \'' + name + '\'' + cmdopt, use_unsafe_shell=True)
                            if rc != 0:
                                module.fail_json(
                                    msg='[Error] set command "' + stdcmd + ' policy shaping set -v \'' + name + '\'' + cmdopt + '" is failed.'
                                )
                            changed = True
                elif shaping['state'].lower() == 'disabled':
                    if now_state != 'false':
                        rc, stdout, stderr = module.run_command(stdcmd + ' policy shaping set -v \'' + name + '\' -e false', use_unsafe_shell=True)
                        if rc != 0:
                            module.fail_json(
                                msg='[Error] set command "' + stdcmd + ' policy shaping set -v \'' + name + '\' -e false' + '" is failed.'
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

        if failover is not None:
            rc, stdout, stderr = module.run_command(stdcmd + ' policy failover get -v \'' + name + '\' | awk -F \': \' \'{print $2}\'', use_unsafe_shell=True)
            stdout_lines = stdout.splitlines()
            now_active = stdout_lines[4].split(', ')
            now_standby = stdout_lines[5].split(', ')
            now_unuse = stdout_lines[6].split(', ')
            now_uplink = sorted([i for i in (now_active + now_standby + now_unuse) if i])
            set_uplink = []
            if 'active_link' in failover and failover['active_link'] is not None:
                set_uplink += failover['active_link']
            if 'standby_link' in failover and failover['standby_link'] is not None:
                set_uplink += failover['standby_link']
            if 'unuse_link' in failover and failover['unuse_link'] is not None:
                set_uplink += failover['unuse_link']
            if now_uplink != sorted(set_uplink):
                for link in now_uplink:
                    rc, stdout, stderr = module.run_command(stdcmd + ' uplink remove -v \'' + name + '\' -u ' + link, use_unsafe_shell=True)
                    if rc != 0:
                        module.fail_json(
                            msg='[Error] remove command "' + stdcmd + ' uplink remove -v \'' + name + '\' -u ' + link + '" is failed.'
                        )
                for link in set_uplink:
                    rc, stdout, stderr = module.run_command(stdcmd + ' uplink add -v \'' + name + '\' -u ' + link, use_unsafe_shell=True)
                    if rc != 0:
                        module.fail_json(
                            msg='[Error] add command "' + stdcmd + ' uplink add -v \'' + name + '\' -u ' + link + '" is failed.'
                        )
                changed = True
            rc, stdout, stderr = module.run_command(stdcmd + ' policy failover get -v \'' + name + '\' | awk -F \': \' \'{print $2}\'', use_unsafe_shell=True)
            stdout_lines = stdout.splitlines()
            now_loadbalance = stdout_lines[0]
            now_faildetect = stdout_lines[1]
            now_notifysw = stdout_lines[2]
            now_failback = stdout_lines[3]
            now_active = ','.join(sorted(stdout_lines[4].split(', ')))
            now_standby = ','.join(sorted(stdout_lines[5].split(', ')))
            now_unuse = ','.join(sorted(stdout_lines[6].split(', ')))
            cmdopt = ''
            if 'load_balancing' in failover:
                if now_loadbalance.lower() != failover['load_balancing']:
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
                if now_faildetect.lower() != failover['failure_detection']:
                    if failover['failure_detection'] not in ['link', 'beacon']:
                        module.fail_json(
                            msg='[Error] failover.failure_detection'
                        )
                    cmdopt += ' -f ' + failover['failure_detection']
            if 'notify_switches' in failover:
                if failover['notify_switches'].lower() == 'yes':
                    if now_notifysw != 'true':
                        cmdopt += ' -n true'
                elif failover['notify_switches'].lower() == 'no':
                    if now_notifysw != 'false':
                        cmdopt += ' -n false'
                else:
                    module.fail_json(
                        msg='[Error] failover.notify_switches'
                    )
            if 'failback' in failover:
                if failover['failback'].lower() == 'yes':
                    if now_failback != 'true':
                        cmdopt += ' -b true'
                elif failover['failback'].lower() == 'no':
                    if now_failback != 'false':
                        cmdopt += ' -b false'
                else:
                    module.fail_json(
                        msg='[Error] failover.failback'
                    )
            if 'active_link' in failover and failover['active_link'] is not None:
                active_link = ','.join(sorted(failover['active_link']))
                if now_active != active_link:
                    cmdopt += ' -a ' + active_link
            else:
                if now_active != "":
                    cmdopt += ' -a ""'
            if 'standby_link' in failover and failover['standby_link'] is not None:
                standby_link = ','.join(sorted(failover['standby_link']))
                if now_standby != standby_link:
                    cmdopt += ' -s ' + standby_link
            else:
                if now_standby != "":
                    cmdopt += ' -s ""'
            if cmdopt != '':
                rc, stdout, stderr = module.run_command(stdcmd + ' policy failover set -v \'' + name + '\'' + cmdopt, use_unsafe_shell=True)
                if rc != 0:
                    module.fail_json(
                        msg='[Error] set command "' + stdcmd + ' policy failover set -v \'' + name + '\'' + cmdopt + '" is failed.'
                    )
                changed = True

    elif state == 'absent':
        rc, stdout, stderr = module.run_command(stdcmd + ' list | grep \'Name: ' + name + '\'', use_unsafe_shell=True)
        if rc != 1:
            rc, stdout, stderr = module.run_command(stdcmd + ' remove -v \'' + name + '\'', use_unsafe_shell=True)
            if rc != 0:
                module.fail_json(
                    msg='[Error] remove command "' + stdcmd + ' remove -v \'' + name + '\'" is failed.'
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
