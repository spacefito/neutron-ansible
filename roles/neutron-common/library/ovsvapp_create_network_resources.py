#!/usr/bin/python
#
# (c) Copyright 2018 SUSE LLC
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#
from ansible.module_utils.basic import *

from networking_vsphere.utils import vim_objects
from oslo_serialization import jsonutils

VCENTER_DVS_RESOURCE_TYPE = 'DistributedVirtualSwitch'
VCENTER_DVPG_RESOURCE_TYPE = 'DistributedVirtualPortgroup'
VCENTER_DVS_MAX_PORTS = 30000


class VcenterManager(object):

    def __init__(self, credentials, check_mode=True):
        self.vcenter_user = credentials.get('vcenter_user')
        self.vcenter_password = credentials.get('vcenter_password')
        self.vcenter_ip = credentials.get('vcenter_ip')
        self.vcenter_port = credentials.get('vcenter_port', 443)
        self.check_mode = check_mode
        self.vcproxy = None
        self.vc_changed = False

    def create_dvs(self, dvsjson, datacenter_name, host_names):
        dvs = vim_objects.DistributedVirtualSwitch(
            dvs_name=dvsjson.get('name'),
            pnic_devices=dvsjson.get('pnic_devices'),
            max_mtu=dvsjson.get('max_mtu'),
            description=dvsjson.get('description'),
            max_ports=dvsjson.get('max_ports', VCENTER_DVS_MAX_PORTS),
            host_names=host_names,
            vcenter_user=self.vcenter_user,
            vcenter_password=self.vcenter_password,
            vcenter_ip=self.vcenter_ip,
            vcenter_port=self.vcenter_port,
            datacenter_name=datacenter_name)

        return self.create_resource_on_vc(VCENTER_DVS_RESOURCE_TYPE, dvs)

    def create_dvpg(self, dvpgjson):

        dvpg = vim_objects.DVSPortGroup(
            dvpgjson.get('name'),
            vlan_type=dvpgjson.get('vlan_type'),
            vlan_id=dvpgjson.get('vlan_id'),
            vlan_range_start=dvpgjson.get('vlan_range_start'),
            vlan_range_end=dvpgjson.get('vlan_range_end'),
            dvs_name=dvpgjson.get('dvs_name'),
            nic_teaming=dvpgjson.get('nic_teaming'),
            description=dvpgjson.get('description'),
            allow_promiscuous=dvpgjson.get('allow_promiscuous'),
            forged_transmits=dvpgjson.get('forged_transmits'),
            auto_expand=dvpgjson.get('auto_expand'),
            vcenter_user=self.vcenter_user,
            vcenter_password=self.vcenter_password,
            vcenter_ip=self.vcenter_ip,
            vcenter_port=self.vcenter_port)

        return self.create_resource_on_vc(VCENTER_DVPG_RESOURCE_TYPE, dvpg)

    def connect_to_vcenter(self):
        if self.check_mode:
            return

        self.vcproxy = vim_objects.VcenterProxy(
            "_",
            vcenter_ip=self.vcenter_ip,
            vcenter_user=self.vcenter_user,
            vcenter_password=self.vcenter_password,
            vcenter_port=self.vcenter_port)

        self.vcproxy.connect_to_vcenter()

    def create_resource_on_vc(self, resource_type, resource):
        self.vc_changed = False
        if self.check_mode:
            self.vc_changed = True
            return resource

        if not self.resource_exists(resource_type, resource):
            resource.connect_to_vcenter()
            resource.create_on_vcenter()
            self.vc_changed = True

        if self.resource_exists(resource_type, resource):
            return resource

    def resource_exists(self, resource_type, resource):
        if self.check_mode:
            return False
        return self.vcproxy.get_mob_by_name(resource_type, resource.name)

    def create_network_resource(self, resource_type, resource_config,
                                datacenter_name, host_names):

        if resource_type == VCENTER_DVS_RESOURCE_TYPE:
            return self.create_dvs(resource_config, datacenter_name,
                                   host_names)

        if resource_type == VCENTER_DVPG_RESOURCE_TYPE:
            return self.create_dvpg(resource_config)


ANSIBLE_METADATA = {
    'metadata_version': '0.1',
    'status': ['beta'],
    'supported_by': 'SUSE'
}

DOCUMENTATION = '''
---
module: ovsvapp_create_dvs

short_description: Creates Distributed Virtual Switch on vCenter

version_added: "1.9.4"

description:
    - "Connects to vCenter server with the given credentials and creates a
       Distributed Virtual Switch"

options:
    resource_type:
        description:
            - Type of resource to create: DistributedVirtualSwitch |
              DistributedVirtualPortgroup

    vcenter_user:
        description:
            - User name used to connect to vCenter
        required: true

    vcenter_password:
        description:
            - Password used to connect to vCenter
        required: true

    vcenter_ip:
        description:
            - IP address used to connect to vCenter
        required: true

    vcenter_port:
        description:
            - TCP port used to connect to vCenter
        required: false

    datacenter_name:
        description:
            - Name of vCenter data center where DVS are to be created.
        required: true

    host_names:
        description:
            - List of list of vMware hosts (ESXi) which will be added to DVS

    resource_config:
        description:
            - Dictionary containing the resource configuration


author:
    - Adolfo Duarte (@fitoduarte)
'''

EXAMPLES = '''
# Create  DVS
- name: Create DVS on datacenter
  ovsvapp_create_network_resources:
    resource_type: "dvs'"
    vcenter_user: "SomeUserName"
    vcenter_password: "Password"
    vcenter_ip: "127.0.0.1"
    vcenter_port: 443
    datacenter_name: "SomeDataCenter"
    host_names: [ "192.168.0.1", "192.168.0.3", "some.host.name"]
    resource_config:    {
                "type": "dvSwitch",
                "name": "TRUNK",
                "pnic_devices": [],
                "max_mtu": "1500",
                "description": "TRUNK DVS for ovsvapp.",
                "max_ports": 30000
               }

# Create DVPG
- name: Create DVPG on datacenter
  ovsvapp_create_network_resources:
    resource_type: "dvpg"
    vcenter_user: "SomeUserName"
    vcenter_password: "Password"
    vcenter_ip: "127.0.0.1"
    vcenter_port: 443
    datacenter_name: "SomeDataCenter"
    resource_config: {
        "name": "TRUNK-PG",
        "vlan_type": "trunk",
        "vlan_range_start": "1",
        "vlan_range_end": "4094",
        "dvs_name": "TRUNK",
        "nic_teaming": null,
        "allow_promiscuous": true,
        "forged_transmits": true,
        "auto_expand": true,
        "description": "TRUNK port group. Configure as trunk for vlans 1-4094."
       }
'''


def run_module():
    module_args = dict(
        resource_type=dict(type='str', required=True),
        vcenter_user=dict(type='str', required=True),
        vcenter_password=dict(type='str', required=True),
        vcenter_ip=dict(type='str', required=True),
        vcenter_port=dict(type='int', default=443),
        datacenter_name=dict(type='str', default=None),
        host_names=dict(type='list'),
        resource_config=dict(type='dict', default={})
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    resource_type = module.params.get('resource_type')

    result = {}

    credentials = {k: module.params[k]
                   for k in ['vcenter_user', 'vcenter_password',
                             'vcenter_ip', 'vcenter_port']}

    manager = VcenterManager(credentials, module.check_mode)
    manager.connect_to_vcenter()
    resource = manager.create_network_resource(
        resource_type,
        module.params.get('resource_config'),
        module.params.get('datacenter_name'),
        module.params.get('host_names'))

    result[resource_type] = jsonutils.to_primitive(resource,
                                                   max_depth=1,
                                                   convert_instances=True)
    result['changed'] = manager.vc_changed

    if result[resource_type]:
        module.exit_json(**result)

    module.fail_json(msg='Failed to create network resource of type {}'
                     .format(resource_type), **result)


if __name__ == '__main__':
    run_module()
