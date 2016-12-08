### Keepupz
[![Build Status](https://snap-ci.com/ISPM/keepupz/branch/master/build_image)](https://snap-ci.com/ISPM/keepupz/branch/master)

# icmp keep alive server for zabbix

## Environ vars
- CONSUMER_TASKS
	Number of tasks to consume the queue and write to Zabbix

- ZBX_SERVER
	Zabbix server ip address

- ZBX_USERNAME
	Zabbix server username

- ZBX_PASSWORD
	Zabbix server password

- ZBX_TEMPLATE
	Zabbix monitoring template name to insert the host in

- ZBX_HOSTGROUP
	Zabbix monitoring hostgroup name to insert the host in

- ZBX_ALLOWED_NETWORKS
	Comma separated CIDRs of networks allowed to be monitored
	Ex. 192.168.8.35/32,192.168.8.27/32

- ZBX_SENDER_KEY
	Zabbix item name

- ZBX_SERVER_TIMEOUT
	In seconds. Set a value greater then the pause between received pings