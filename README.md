<!--

 (c) Copyright 2018 SUSE LLC

 Licensed under the Apache License, Version 2.0 (the "License"); you may
 not use this file except in compliance with the License. You may obtain
 a copy of the License at

 http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 License for the specific language governing permissions and limitations
 under the License.

-->
NEUTRON-ANSIBLE:
===============
Playbooks:
=========

neutron-create-ovsvapp-resources.yml
------------------------------------
This playbook is used to create the required network resources on
the vCenter server.

### Executing the playbook from cli ###

   1. Edit the pass_through.yml file to define required variables.

   2. Edit the required network_resource_config files under the input model.

   3. Run preprocessor.

   4. Run the playbook:
        ```
        cd ~/scratch/ansible/next/ardana/ansible
        ansible-playbook neutron-create-ovsvapp-resources.yml-i hosts/verb_hosts
        ```

### Playbook details ###
   The playbook may be executed as long as the required variables are defined.

   When executing the playbook using the input model, the following variables
   need to be defined in pass_through.yml files:

- **global.vmware.username**: name to be used to connect to the vCenter server.

- **global.vmware.password**: password to be used to connect to the vCenter server.

- **global.vmware.ip**: ip address to be used to connect to the vCenter server.

- **global.vmware.port**: tcp port to be used to connect to vCenter server.

- **global.vmware.cert_check**: True or False. Used to indicate weather or
    not server certificate check should be skipped when making connections to
    the vCenter server.

- **global.vmware.vc_net_resources**: path to a text file in json
    format which describes the network resources to be created on the vCenter
    server.

- **network_resources_config file format**: The network_resource_config is a
    json formatted text file. The network resources are defined under the
    _network_properties_ as  list of _switches_ or _portGroups_ configurations.
    The datacenter name and list of hostnames to be used are defined in the
    root node of the file, like so:
    ```
    {"datacenter_name": "DatacenterExampleNmae",
     "host_names" : [ "192.168.0.100.21", "192.168.100.22"]

    "network_properties": {
      "switches": [...list of switch configurations],
      "portGroups": [...list of portGroup configurations]
      }
    }
    ```
    In turn, every switch and portGroup  configuration is itself a json data
    structure.

- **DVS switch configuration format**:
    ```
    {
        "type": "dvSwitch",
        "name": "NameOf the trunk",
        "pnic_devices": [],
        "max_mtu": "1500",
        "description": "TRUNK DVS for ovsvapp.",
        "max_ports": 30000
    }
    ```

    - "type" is the string 'dvSwitch' for Distributed Virtual Switches.

    - "name" is the name which will be given to the DVS.

    - "pnic_devices" is the
       list of physical nics which will be attached to the DVS. For example
       [ "vmnic1", "vmnic2" ]

    - "max_mtu": mtu of the DVS.

    - "description": an arbritrary string.

    - "max_ports": maximum number of ports on DVS.

 - **DVPG portGroup configurations format**:
    ```
    {
       "name": "TRUNK-PG",
       "vlan_type": "trunk",
       "vlan_id" : "20",
       "vlan_range_start": "1",
       "vlan_range_end": "4094",
       "dvs_name": "TRUNK",
       "nic_teaming": {
                       "network_failover_detection": true,
                       "notify_switches": true,
                       "load_balancing": true,
                       "active_nics": ["vmnic1", "vmnic2"]
                      },
       "allow_promiscuous": true,
       "forged_transmits": true,
       "auto_expand": true,
       "description": "TRUNK port group. Configure as trunk for vlans 1-4094. Default nic_teaming selected."
    }
    ```

    - "name": is the name of the portGroup.

    - "vlan_id": if the vlan_type is 'vlan', it is the vlan id which will be
      configured for the portGroup. If vlan_type is 'trunk', it has no effect.

    - "vlan_type":  'trunk' or  'vlan'.

    - "vlan_range_start":  if vlan_type is 'trunk', this will be used as the
      start of the vlan range the trunk will carry. If vlan_type is 'vlan', it
      has no effect.

    - "vlan_range_end": if vlan_type is 'trunk', this will be used as the end
      of the vlan range the trunk will carry. If vlan_type is 'vlan', it
      has no effect.

    - "dvs_name": the name of the DVS that will be associated with the
      portGroup.

    - "nic_teaming": a json data structure which describes the nic teaming to
      be used by the portGroup.

      - "network_failover_detection": if true the network failover detection
         will use "Beacon probing"(checkBeacon=True). If false it will use link
         status only (checkBeacon=False)

      - "load_balancing": one of the following load balancing algorithms:

             'loadbalance_srcid',

             'loadbalance_ip',

             'loadbalance_srcmac',

             'loadbalance_loadbased',

             'failover_explicit'

      - "active_nics": a list of names for the nics to be used in the
        portGroup. Usually of the form: ["vmnic1", "vmnic2"]

    - "allow_promiscuous": true/false

    - "forged_transmits": true/false

    - "auto_expand": true/false

    - "description": an arbitrary string to be used as description

     For a more through explanation of these properties, consult the Vmware
     documentation on Distributed Virtual Port Groups.


 - **Full resource_config file example**:
   ```
    {"datacenter_name": "DC1",
      "host_names": [
        "192.168.100.21",
        "192.168.100.222"
      ],
      "network_properties": {
        "switches": [
          {
            "type": "dvSwitch",
            "name": "TRUNK",
            "pnic_devices": [],
            "max_mtu": "1500",
            "description": "TRUNK DVS for ovsvapp.",
            "max_ports": 30000
          },
          {
            "type": "dvSwitch",
            "name": "MGMT",
            "pnic_devices": [
              "vmnic1"
            ],
            "max_mtu": "1500",
            "description": "MGMT DVS for ovsvapp. Uses 'vmnic0' to connect to OpenStack Management network",
            "max_ports": 30000
          },
          {
            "type": "dvSwitch",
            "name": "GUEST",
            "pnic_devices": [
              "vmnic1",
              "vmnic2"
            ],
            "max_mtu": "1500",
            "description": "GUEST DVS for ovsvapp. Uses 'vmnic1' and 'vmnic2' to connect to the OpenStack tenant (GUEST) network",
            "max_ports": 30000
          },
          {
            "type": "dvSwitch",
            "name": "ESX-CONF",
            "pnic_devices": [
              "vmnic1"
            ],
            "max_mtu": "1500",
            "description": "TRUNK port for ovsvapp. Uses 'vmnic0' to connect to the ESX configuration network.",
            "max_ports": 30000
          }
        ],
        "portGroups": [
          {
            "name": "TRUNK-PG",
            "vlan_type": "trunk",
            "vlan_range_start": "1",
            "vlan_range_end": "4094",
            "dvs_name": "TRUNK",
            "nic_teaming": null,
            "allow_promiscuous": true,
            "forged_transmits": true,
            "auto_expand": true,
            "description": "TRUNK port group. Configure as trunk for vlans 1-4094. Default nic_teaming selected."
          },
          {
            "name": "MGMT-PG",
            "dvs_name": "MGMT",
            "nic_teaming": null,
            "description": "MGMT port group. Configured as type 'access' (vlan with vlan_id = 0, default). Default nic_teaming. Promiscuous false, forged_transmits default"
          },
          {
            "name": "GUEST-PG",
            "dvs_name": "GUEST",
            "vlan_type": "trunk",
            "vlan_range_start": 100,
            "vlan_range_end": 200,
            "nic_teaming": null,
            "allow_promiscuous": true,
            "forged_transmits": true,
            "auto_expand": true,
            "description": "GUEST port group. Configure for vlans 100 through 200."
          },
          {
            "name": "ESX-CONF-PG",
            "dvs_name": "ESX-CONF",
            "nic_teaming": null,
            "description": "ESX-CONF port group. Configured as type 'access' (vlan with vlan_id = 0, default)."
          }
        ]
      }
    }


