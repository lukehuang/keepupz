# Keepupz

[![Build Status](http://192.168.8.238:8080/job/ISPM/job/keepupz/job/master/badge/icon)](http://192.168.8.238:8080/job/ISPM/job/keepupz/job/master/)

## ICMP keep alive server for zabbix

### Environ

View docker-compose.yml

__Variables__ | __Description__
--- | ---
`CONSUMER_TASKS` | Number of tasks to consume the queue and write to Zabbix.
`ZBX_SERVER` | Zabbix server ip address.
`ZBX_USERNAME` | Zabbix server username.
`ZBX_PASSWORD` | Zabbix server password.
`ZBX_TEMPLATE` | Zabbix monitoring template name to insert the host in.
`ZBX_HOSTGROUP` | Zabbix monitoring hostgroup name to insert the host in.
`ZBX_ALLOWED_NETWORKS` | Comma separated CIDRs of networks allowed to be monitored (Ex.: 192.168.8.35/32,192.168.8.42/30).
`ZBX_SENDER_KEY` | Zabbix item name
`ZBX_SERVER_TIMEOUT` | In seconds. Used for tests. Set this to a small value.

### .env
This file has the `DOCKER_HTTP_TIMEOUT`. For production. Set this to a value greater then the pause between received pings.

### docker-compose.yml
For development, set the volume to your `code` dir. The Dockerfile will copy the code to the containner.

### Makefile
- `make build-image` - build the image.

- `make test` - run the python tests
