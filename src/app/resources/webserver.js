{
    "_comment" : "cloud_service.service_name == virtual_machine.service_name",
    "cloud_service" : {
        "service_name" : "yifu-test-service-name",
        "label" : "yifu-test-label",
        "location" : "China East"
    },
    "virtual_machine" : {
        "service_name" : "yifu-test-service-name",
        "deployment_name" : "yifu-test-deployment-name",
        "deployment_slot" : "production",
        "label" : "yifu-test-label",
        "role_name" : "yifu-test-role-name",
        "system_config" : {
            "host_name" : "yifu-test-host-name",
            "user_name" : "yifu-test-user-name",
            "user_password" : "Yifu-Test-User-Password"
        },
        "os_virtual_hard_disk" : {
            "source_image_name" : "webserver",
            "media_link" : "https://ossvhds.blob.core.chinacloudapi.cn/ossvhds/captured-webservice-os-2015-01-13.vhd"
        }
    }
}