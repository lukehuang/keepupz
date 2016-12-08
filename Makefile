help:
    @echo "Options:"
    @echo "    build-image: build the docker image of rConfig"

build-image:
    # docker build --rm -t ispm/icmpreceiver icmpreceiver/ && docker build --rm -t ispm/rconfig-api api/
    docker build --rm -t ispm/keepupz .

test:
    docker run -e "CONSUMER_TASKS=5" -e "ZBX_SERVER=192.168.8.23" -e "ZBX_USERNAME=Admin" -e "ZBX_PASSWORD=zabbix" -e "ZBX_TEMPLATE=ISPM - BGAN" -e "ZBX_HOSTGROUP=BGAN" -e "ZBX_ALLOWED_NETWORKS=192.168.8.35/32,192.168.8.27/32" -e "ZBX_SENDER_KEY=agent.ping" -e "ZBX_SERVER_TIMEOUT=120" ispm/keepupz python tests.py
