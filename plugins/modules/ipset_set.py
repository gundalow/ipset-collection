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
module: ipset_set
short_description: Create or delete ipset sets
description:
  - Requires the ipset binary to be installed on the host running the module
  - Creates or removes ipsets
version_added: 2.10
author:
  - Andrea Tartaglia (@shaps)
requirements:
  - ipset binary
options:
  set_name:
    description:
      - The name of the set
    type: str
    required: true
  set_type:
    description:
      - The set type
    type: str
  set_timeout:
    description:
      - The default timeout of the set
    type: str
  state:
    description:
      - The action to be performed.
    default: present
    choices: ['present','absent']
    type: str
'''

EXAMPLES = '''
- name: Create blacklist set
  ipset_set:
    set_name: blacklist
    set_type: 'hash:net'
    timeout: 1209600
    state: present

- name: Delete blacklist set
  ipset_set:
    set_name: blacklist
    state: absent
'''

RETURN = '''
'''

from ansible.module_utils.basic import AnsibleModule


def set_exists(module):
    ipset_bin = module.get_bin_path('ipset', required=True)
    test_cmd = [ipset_bin, 'create', '-!', module.params.get('set_name'), module.params.get('set_type'), 'timeout', module.params.get('set_timeout')]
    rc, stdout, stderr = module.run_command(test_cmd)

    return bool(rc)


def main():
    argument_spec = dict(
        state=dict(choices=['present', 'absent'], default="present"),
        set_name=dict(required=True, type='str'),
        set_type=dict(type='str'),
        set_timeout=dict(required=True, type='str'),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        required_if=[
            ('state', 'present', ['set_name', 'set_type']),
            ('state', 'absent', ['set_name'])
        ],
        supports_check_mode=True
    )
    ipset_bin = module.get_bin_path('ipset', required=True)

    if module.params.get('state') == 'present':
        cmd = [ipset_bin, '-!', 'create', module.params.get('set_name'), module.params.get('set_type'), 'timeout', module.params.get('set_timeout')]
        if not set_exists(module):
            if module.check_mode:
                module.exit_json(changed=set_exists(module))
            rc, stdout, stderr = module.run_command(cmd, check_rc=True)
            module.exit_json(stdout=stdout, stderr=stderr, rc=rc, changed=True)
        else:
            module.exit_json(changed=False, msg="Set %s already exists" % module.params.get('set_name'))
    if module.params.get('state') == 'absent':
        flush_cmd = [ipset_bin, '-!', 'flush', module.params.get('set_name')]
        destroy_cmd = [ipset_bin, '-!', 'destroy', module.params.get('set_name')]
        if set_exists(module):
            if module.check_mode:
                module.exit_json(changed=set_exists(module))
            flush_rc, flush_stdout, flush_stderr = module.run_command(flush_cmd, check_rc=True)
            if (flush_rc == 0):
                destroy_rc, destroy_stdout, destroy_stderr = module.run_command(destroy_cmd, check_rc=True)
            module.exit_json(stdout=destroy_stdout, stderr=destroy_stderr, rc=destroy_rc, changed=True)
        else:
            module.exit_json(changed=False, msg="%s already absent" % module.params.get('set_name'))


if __name__ == '__main__':
    main()
