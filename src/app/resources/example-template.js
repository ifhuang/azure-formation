{
    "_comment" : "cloud_service.service_name == virtual_machines[i].service_name",
    "storage_account" : {
        "service_name" : "yifu0storage",
        "description" : "yifu-test-description",
        "label" : "yifu-test-label",
        "location" : "China East"
    },
    "cloud_service" : {
        "service_name" : "yifu-test-service-name",
        "label" : "yifu-test-label",
        "location" : "China East"
    },
    "virtual_machines" : [
        {
            "service_name" : "yifu-test-service-name",
            "deployment_name" : "yifu-test-deployment-name",
            "deployment_slot" : "production",
            "label" : "yifu-test-label",
            "role_name" : "yifu-test-role-name",
            "system_config" : {
                "os_family" : "Linux",
                "host_name" : "yifu-test-host-name",
                "user_name" : "yifu-test-user-name",
                "user_password" : "Yifu-Test-User-Password"
            },
            "os_virtual_hard_disk" : {
                "source_image_name" : "b549f4301d0b4295b8e76ceb65df47d4__Ubuntu-14_04_1-LTS-amd64-server-20141125-en-us-30GB",
                "media_link_base" : "blob.core.chinacloudapi.cn",
                "media_link_container" : "ossvhds"
            },
            "network_config" : {
                "configuration_set_type" : "NetworkConfiguration",
                "input_endpoints" : [
                    {
                        "name" : "ssh",
                        "protocol" : "tcp",
                        "port" : "22",
                        "local_port" : "22"
                    },
                    {
                        "name" : "http",
                        "protocol" : "tcp",
                        "port" : "80",
                        "local_port" : "80"
                    }
                ]
            },
            "role_size" : "Small"
        },
        {
            "service_name" : "yifu-test-service-name",
            "deployment_name" : "yifu-test-deployment-name",
            "deployment_slot" : "production",
            "label" : "yifu-test-label-2",
            "role_name" : "yifu-test-role-name-2",
            "system_config" : {
                "os_family" : "Windows",
                "host_name" : "yifutest2",
                "user_name" : "yifutestuser2",
                "user_password" : "Yifu-Test--2"
            },
            "os_virtual_hard_disk" : {
                "source_image_name" : "0c5c79005aae478e8883bf950a861ce0__Windows-Server-2012-Essentials-20141204-enus",
                "media_link_base" : "blob.core.chinacloudapi.cn",
                "media_link_container" : "ossvhds"
            },
            "network_config" : {
                "configuration_set_type" : "NetworkConfiguration",
                "input_endpoints" : [
                    {
                        "name" : "http",
                        "protocol" : "tcp",
                        "port" : "80",
                        "local_port" : "80"
                    }
                ]
            },
            "role_size" : "Small"
        }
    ]
}