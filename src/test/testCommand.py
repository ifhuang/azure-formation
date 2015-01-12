__author__ = 'Yifu Huang'

import commands

print commands.getstatusoutput('openssl req -x509 -nodes -days 365 -newkey rsa:1024 -keyout mycert.pem -out mycert.pem -batch')
print commands.getstatusoutput('openssl x509 -inform pem -in mycert.pem -outform der -out mycert.cer')