__author__ = 'Yifu Huang'

MYSQL_HOST = 'localhost'
MYSQL_USER = 'azureformation'
MYSQL_PWD = 'azureformation'
MYSQL_DB = 'azureformation'

Config = {
    "mysql": {
        "connection": 'mysql://%s:%s@%s/%s' % (MYSQL_USER, MYSQL_PWD, MYSQL_HOST, MYSQL_DB)
    },
    "scheduler": {
        "job_store": "mysql",
        "job_store_url": 'mysql://%s:%s@%s/%s' % (MYSQL_USER, MYSQL_PWD, MYSQL_HOST, MYSQL_DB)
    },
    "azure": {
        "certBase": "/home/if/If/azure-formation/src/azureformation/certificates"
    },
}
