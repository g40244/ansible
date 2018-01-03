
#! /usr/bin/env python
# -*- coding: utf-8 -*-

from ansible.module_utils.basic import *
import os.path
import re

def main():
    module = AnsibleModule(
        dict(
            path=dict(required=True),
            prev=dict(required=True),
            current=dict(required=True),
            state=dict(required=True, choices=['present', 'absent'])
        )
    )
    path = module.params['path']
    prev = module.params['prev']
    current = module.params['current']
    state = module.params['state']

    if not re.findall('\n$', current):
        current += '\n'

    if not re.findall('\n$', prev):
        prev += '\n'

    if not os.path.exists(path):
        module.fail_json(msg='[Error] file '+ path +' is not found.')

    elif os.path.isdir(path):
        module.fail_json(msg='[Error] '+ path +' is directory.')

    elif os.path.islink(path):
        module.fail_json(msg='[Error] '+ path +' is link.')

    line = open(path).read()

    if state == 'present':
        if current in line:
            module.exit_json(changed=False)

        if not prev in line:
            module.fail_json(msg='[Error] prev lines is not found.')

        line = line.replace(prev, current)

    elif state == 'absent':
        if not current in line:
            if prev in line:
                module.exit_json(changed=False)
            else:
                module.fail_json(msg='[Error] current lines is not found.')

        line = line.replace(current, prev)

    f = open(path, 'w')
    f.write(line)
    f.close()

    module.exit_json(changed=True)

if __name__ == '__main__':
    main()