#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Andrea Tartaglia (andrea@braingap.uk)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ipset_entry
short_description: Create/remove/list entries in an ipset
description:
  - Requires the ipset binary to be installed on the host running the module
  - Adds, removes or lists entries in an ipset
version_added: 2.10
author:
  - Andrea Tartaglia (@shaps)
requirements:
  - ipset binary
options:
  set_name:
    description:
      - The name of the set where the network should be added/removed
    type: str
    required: true
  net:
    description:
      - The network to be added in the set C(set_name)
      - Not required when C(state) is set to C(list)
    type: str
  timeout:
    description:
      - How long the network should be in the set
    type: str
  state:
    description:
      - The action to be performed.
    default: present
    choices: ['present','absent','list']
    type: str
'''

EXAMPLES = '''
- name: Add 172.18.0.0/16 to blacklist ipset
  ipset_entry:
    set_name: blacklist
    net: 172.18.0.0/16
    timeout: 1209600
    state: present

- name: Remove 172.18.0.0/16 to blacklist ipset
  ipset_entry:
    set_name: blacklist
    net: 172.18.0.0/16
    timeout: 1209600
    state: absent
'''

RETURN = '''
nets:
  description: The list of networks in the specified set
  returned: when state == 'list'
  type: list
  sample: { nets: [{net: 202.43.76.0/22, timeout: '694995'}] }
'''

from ansible.module_utils.basic import AnsibleModule


def net_in_set(module):
    ipset_bin = module.get_bin_path('ipset')
    test_cmd = [ipset_bin, 'test', module.params.get('set_name'), module.params.get('net')]
    rc, stdout, stderr = module.run_command(test_cmd)
    if rc == 0:
        return True
    else:
        return False


def main():
    argument_spec = dict(
        state=dict(choices=['present', 'absent', 'list'], default="present"),
        set_name=dict(required=True, type='str'),
        net=dict(type='str'),
        timeout=dict(type='str'),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        required_if=[
            ('state', 'present', ['net']),
            ('state', 'absent', ['net'])
        ],
        supports_check_mode=True
    )
    ipset_bin = module.get_bin_path('ipset', required=True)

    if module.params.get('state') == 'present':
        cmd = [ipset_bin, "-!", 'add', module.params.get('set_name'), module.params.get('net')]
        if module.params.get('timeout'):
            cmd.extend(['timeout', module.params.get('timeout')])
        if not net_in_set(module):
            if module.check_mode:
                module.exit_json(changed=net_in_set(module))
            rc, stdout, stderr = module.run_command(cmd, check_rc=True)
            module.exit_json(stdout=stdout, stderr=stderr, rc=rc, changed=True)
        else:
            module.exit_json(changed=False, msg="%s already in set" % module.params.get('net'))
    if module.params.get('state') == 'absent':
        cmd = [ipset_bin, '-!', 'del', module.params.get('set_name'), module.params.get('net')]
        if net_in_set(module):
            if module.check_mode:
                module.exit_json(changed=net_in_set(module))
            rc, stdout, stderr = module.run_command(cmd, check_rc=True)
            module.exit_json(stdout=stdout, stderr=stderr, rc=rc, changed=True)
        else:
            module.exit_json(changed=False, msg="%s not in set" % module.params.get('net'))

    if module.params.get('state') == 'list':
        cmd = [ipset_bin, 'list', module.params.get('set_name')]
        rc, stdout, stderr = module.run_command(cmd, check_rc=True)
        nets = []
        for line in stdout.split('\n'):
            line_elements = line.split(' ')
            if len(line_elements) == 3:
                nets.append({'net': line_elements[0], 'timeout': line_elements[2]})
        module.exit_json(nets=nets)


if __name__ == '__main__':
    main()
