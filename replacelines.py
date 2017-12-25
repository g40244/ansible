#! /usr/bin/env python
# -*- coding: utf-8 -*-

from ansible.module_utils.basic import *
import os.path
import re

def main():
    module = AnsibleModule(
        dict(
            path=dict(required=True),
            prev=dict(required=False, default=''),
            current=dict(required=True),
            state=dict(required=True, choices=['present', 'absent'])
        )
    )
    path = module.param['path']
    prev = module.param['prev']
    current = module.param['current']
    state = module.param['state']

    if not os.path.exists(path):
        module.fail_json(msg='[Error] file '+ path +' is not found.')
    elif os.path.isdir(path):
        module.fail_json(msg='[Error] '+ path +' is directory.')
    elif os.path.islink(path):
        module.fail_json(msg='[Error] '+ path +' is link.')

    line = open(path).read()
    
    if state == 'present':
        if not re.findall('\n$', current, re.MULTILINE):
            current += '\n'
    
        if re.findall(current, line, re.MULTILINE):
            module.exit_json(changed=False)
    
        prev = re.findall(prev, line, re.MULTILINE)
        if not prev:
            module.fail_json(msg='[Error] prev lines "'+ prev +'" is not found.')
        
        elif len(prev) != 1:
            module.fail_json(msg='[Error] prev lines "'+ prev +'" is multiple found.')
    
        prev = prev[0] + '\n'
        line = re.sub(prev, current, line)
    
    elif state == 'absent':
        if not re.findall('\n$', prev, re.MULTILINE):
            prev += '\n'
        
        if not re.findall('\n$', current, re.MULTILINE):
            current += '\n'
        
        if not re.findall(current, line, re.MULTILINE):
            if re.findall(prev, line, re.MULTILINE):
                module.exit_json(changed=False)
            
        line = re.sub(current, prev, line)
    
    module.exit_json(changed=True)
        
if __name__ == '__main__':
    main()