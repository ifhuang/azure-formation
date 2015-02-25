__author__ = 'Yifu Huang'

from azure.servicemanagement import (
    WindowsConfigurationSet,
    LinuxConfigurationSet,
    OSVirtualHardDisk,
    ConfigurationSet,
    ConfigurationSetInputEndpoint
)
import datetime

# template name in virtual_environment
T_P = 'provider'
T_SA = 'storage_account'
T_SA_SN = 'service_name'
T_SA_D = 'description'
T_SA_LA = 'label'
T_SA_LO = 'location'
T_SA_UB = 'url_base'
T_C = 'container'
T_CS = 'cloud_service'
T_CS_SN = 'service_name'
T_CS_LA = 'label'
T_CS_LO = 'location'
T_D = 'deployment'
T_D_DN = 'deployment_name'
T_D_DS = 'deployment_slot'
T_L = 'label'
T_RN = 'role_name'
T_I = 'image'
T_I_T = 'type'
T_I_N = 'name'
T_SC = 'system_config'
T_SC_OF = 'os_family'
T_SC_HN = 'host_name'
T_SC_UN = 'user_name'
T_SC_UP = 'user_password'
T_NC = 'network_config'
T_NC_CST = 'configuration_set_type'
T_NC_IE = 'input_endpoints'
T_NC_IE_N = 'name'
T_NC_IE_PR = 'protocol'
T_NC_IE_LP = 'local_port'
T_R = 'remote'
T_R_PROV = 'provider'
T_R_PROT = 'protocol'
T_R_IEN = 'input_endpoint_name'
T_RS = 'role_size'
# os family name
WINDOWS = 'Windows'
LINUX = 'Linux'
# remote parameter name
RP_N = 'name'
RP_DN = 'displayname'
RP_HN = 'hostname'
RP_PR = 'protocol'
RP_PO = 'port'
RP_UN = 'username'
RP_PA = 'password'


class Template:

    def __init__(self, virtual_environment):
        self.virtual_environment = virtual_environment

    def get_system_config(self):
        sc = self.virtual_environment[T_SC]
        # check whether virtual machine is Windows or Linux
        if sc[T_SC_OF] == WINDOWS:
            system_config = WindowsConfigurationSet(computer_name=sc[T_SC_HN],
                                                    admin_password=sc[T_SC_UP],
                                                    admin_username=sc[T_SC_UN])
            system_config.domain_join = None
            system_config.win_rm = None
        else:
            system_config = LinuxConfigurationSet(sc[T_SC_HN],
                                                  sc[T_SC_UN],
                                                  sc[T_SC_UP],
                                                  False)
        return system_config

    def get_os_virtual_hard_disk(self):
        i = self.virtual_environment[T_I]
        sa = self.virtual_environment[T_SA]
        c = self.virtual_environment[T_C]
        now = datetime.datetime.now()
        blob = '%s-%s-%s-%s-%s-%s-%s.vhd' % (i[T_I_N],
                                             str(now.year), str(now.month), str(now.day),
                                             str(now.hour), str(now.minute), str(now.second))
        media_link = 'https://%s.%s/%s/%s' % (sa[T_SA_SN],
                                              sa[T_SA_UB],
                                              c,
                                              blob)
        os_virtual_hard_disk = OSVirtualHardDisk(i[T_I_N], media_link)
        return os_virtual_hard_disk

    def get_network_config(self, service):
        cs = self.virtual_environment[T_CS]
        nc = self.virtual_environment[T_NC]
        network_config = ConfigurationSet()
        network_config.configuration_set_type = nc[T_NC_CST]
        input_endpoints = nc[T_NC_IE]
        assigned_endpoints = service.get_assigned_endpoints(cs[T_CS_SN])
        for input_endpoint in input_endpoints:
            port = int(input_endpoint[T_NC_IE_LP])
            # avoid duplicate endpoint under same cloud service
            while str(port) in assigned_endpoints:
                port = (port + 1) % 65536
            assigned_endpoints.append(str(port))
            network_config.input_endpoints.input_endpoints.append(
                ConfigurationSetInputEndpoint(
                    input_endpoint[T_NC_IE_N],
                    input_endpoint[T_NC_IE_PR],
                    str(port),
                    input_endpoint[T_NC_IE_LP]
                )
            )
        return network_config

    def get_cloud_service_name(self):
        return self.virtual_environment[T_CS][T_CS_SN]

    def get_deployment_slot(self):
        return self.virtual_environment[T_D][T_D_DS]

    def get_deployment_name(self):
        return self.virtual_environment[T_D][T_D_DN]

    def get_virtual_machine_name(self):
        return self.virtual_environment[T_RN]

    def get_virtual_machine_label(self):
        return self.virtual_environment[T_L]

    def get_virtual_machine_size(self):
        return self.virtual_environment[T_RS]

    def get_remote_provider_name(self):
        return self.virtual_environment[T_R][T_R_PROV]

    def get_remote_port_name(self):
        return self.virtual_environment[T_R][T_R_IEN]

    def get_remote_paras(self, name, hostname, port):
        r = self.virtual_environment[T_R]
        sc = self.virtual_environment[T_SC]
        remote = {
            RP_N: name,
            RP_DN: r[T_R_IEN],
            RP_HN: hostname,
            RP_PR: r[T_R_PROT],
            RP_PO: port,
            RP_UN: sc[T_SC_UN],
            RP_PA: sc[T_SC_UP]
        }
        return remote

    def get_image_type(self):
        return self.virtual_environment[T_I][T_I_T]

    def get_image_name(self):
        return self.virtual_environment[T_I][T_I_N]