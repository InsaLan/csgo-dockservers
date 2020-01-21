import re
import time
from math import ceil
from typing import List, Dict, IO
import yaml
import docker
import ipaddress

import mysql
#from key import *

with open("config.yml", "r") as config_file:
    config = yaml.load(config_file, Loader=yaml.FullLoader)

def register_server_ebot(servers: List[Dict[str, str]], db_ip: str) -> None:
    """
    Register a game server to the Ebot server, by adding values to its database.

    :param servers: A list of servers to add
    :param db_ip: The IP of Ebot's DB
    """
    containers = []
    csgo_containers = []
    tls_config = docker.tls.TLSConfig(config["docker_tls"])
    for s in servers:
        client = docker.DockerClient(
            base_url="tcp://{}:2375".format(s["ip"]), tls=tls_config
        )
        containers.extend(client.containers.list("all"))
        csgo_containers.extend(
            c for c in containers if c.attrs["Config"]["User"] == "steam"
        )

    cnx = mysql.connector.connect(
        user="ebotv3", password="ebotv3", host=db_ip, database="ebotv3"
    )
    cursor = cnx.cursor()
    try:
        cursor.execute("delete from servers where id!=-1")
    except:
        print("truncate failed")
    try:
        add_server = (
            "INSERT INTO servers"
            "(ip, rcon, hostname, tv_ip, created_at, updated_at)"
            "values(%s,%s,%s,%s,'2017-12-17 00:00:00','2017-12-17 00:00:00')"
        )
        stvp = re.compile("STV_PORT")
        hostp = re.compile("HOST_PORT")
        ipp = re.compile("IP")
        for i in csgo_containers:
            for y in i.attrs["Config"]["Env"]:
                if stvp.search(y):
                    stvport = re.split("=", y)[1]
                if hostp.search(y):
                    hostport = re.split("=", y)[1]
                if ipp.search(y):
                    ip = re.split("=", y)[1]
            name = i.attrs["Name"]
            data_server = (
                "{}:{}".format(ip, hostport),
                "notbanana",
                name,
                "{}:{}".format(ip, stvport),
            )
            cursor.execute(add_server, data_server)
            cnx.commit()
        cursor.close()
        cnx.close()
    except:
        print("insertion failed")


def deploy_ebotserver(client, ebot_ip, topo: IO) -> None:
    """
    Deploy ebot (ebot web and his DB) on a physical server.

    :param client: Number of container to deploy
    :param ebot_ip: IP of the server on which ebot should be deployed
    :param topo: File descriptor to the topology file

    """

    db_container = client.create_container(
        "mysql:5.7",
        detach=True,
        host_config=client.create_host_config(
            restart_policy={"Name": "always"},
            mounts=[
                docker.types.Mount(
                    "/var/lib/mysql", "/opt/docker/ebot/mysql", type="bind"
                )
            ],
            network_mode="host",
        ),
        environment={
            "MYSQL_DATABASE": "ebotv3",
            "MYSQL_USER": "ebotv3",
            "MYSQL_PASSWORD": "ebotv3",
            "MYSQL_ROOT_PASSWORD": "nhurmanroot",
        },
        command="mysqld",
        name="db_container",
    )
    topo.write("db_container;{};{}\n".format(ebot_ip, client.base_url))

    ebot_container = client.create_container(
        "hsfactory/ebot",
        detach=True,
        hostname="ebot",
        host_config=client.create_host_config(
            restart_policy={"Name": "always"},
            extra_hosts={"mysql": ebot_ip, "ebot": ebot_ip},
            mounts=[
                docker.types.Mount("/ebot/logs", "/opt/docker/ebot/logs", type="bind"),
                docker.types.Mount("/ebot/demos", "/opt/docker/ebot/demo", type="bind"),
            ],
            network_mode="host",
        ),
        environment={
            "EXTERNAL_IP": ebot_ip,
            "MYSQL_HOST": "mysql",
            "MYSQL_PORT": "3306",
            "MYSQL_DB": "ebotv3",
            "MYSQL_USER": "ebotv3",
            "MYSQL_PASS": "ebotv3",
            "LO3_METHOD": "restart",
            "KO3_METHOD": "restart",
            "DEMO_DOWNLOAD": "true",
            "REMIND_RECORD": "false",
            "DAMAGE_REPORT": "true",
            "DELAY_READY": "false",
            "NODE_STARTUP_METHOD": "node",
            "TOORNAMENT_PLUGIN_KEY": "",
        },
        name="ebot_container",
    )
    topo.write("ebot_container;{};{}\n".format(ebot_ip, client.base_url))

    ebotweb_container = client.create_container(
        "hsfactory/ebotweb",
        detach=True,
        host_config=client.create_host_config(
            restart_policy={"Name": "always"},
            extra_hosts={"mysql": ebot_ip, "ebot": ebot_ip},
            mounts=[
                docker.types.Mount(
                    "/opt/ebot/logs", "/opt/docker/ebot/logs", type="bind"
                ),
                docker.types.Mount(
                    "/opt/ebot/demos", "/opt/docker/ebot/demo", type="bind"
                ),
            ],
            network_mode="host",
        ),
        environment={
            "EBOT_IP": ebot_ip,
            "EBOT_PORT": "12360",
            "EBOT_ADMIN_USER": "insalan",
            "EBOT_ADMIN_PASS": "nhurman",
            "EBOT_ADMIN_MAIL": "insalade@ebot",
            "MYSQL_HOST": "mysql",
            "MYSQL_PORT": "3306",
            "MYSQL_DB": "ebotv3",
            "MYSQL_USER": "ebotv3",
            "MYSQL_PASS": "ebotv3",
            "DEMO_DOWNLOAD": "true",
            "DEFAULT_RULES": "esl5on5",
            "TOORNAMENT_ID": "",
            "TOORNAMENT_SECRET": "",
            "TOORNAMENT_PLUGIN_KEY": "",
            "TOORNAMENT_API_KEY": "",
        },
        name="ebotweb_container",
    )
    topo.write("ebotweb_container;{};{}\n".format(ebot_ip, client.base_url))

    client.start(db_container)
    time.sleep(10)
    client.start(ebot_container)
    time.sleep(10)
    client.start(ebotweb_container)


def deploy_csgoserver(
    nb_csgo: int, servers: List[Dict[str, str]], ebot_ip: str, image: str, topo: IO
) -> None:
    """
    Deploy csgo containers over physical servers.

    :param nb_csgo: Number of container to deploy
    :param servers: List of physical servers on which the containers will be deployed
    :param ebot_ip: IP address of ebot (#FIXME confirm with original author)
    :param image: Name of the docker image to deploy
    :param topo: File descriptor to the topology file

    """

    ip = ipaddress.ip_address(ebot_ip)
    hostport = 27015
    clientport = hostport + nb_csgo
    stvport = clientport + nb_csgo
    hostname = "csgoinsalan"
    for y in range(0, len(servers)):
        for i in range(
            int(ceil(nb_csgo / len(servers)) * y),
            int(ceil(nb_csgo / len(servers)) * (y + 1)),
        ):
            ip = ipaddress.ip_address(ip + 1)
            tls_config = docker.tls.TLSConfig(config["docker_tls"])
            client = docker.APIClient(
                base_url="tcp://{}:2375".format(servers[y]), tls=tls_config
            )
            container = client.create_container(
                image,
                detach=True,
                hostname=hostname,
                host_config=client.create_host_config(
                    extra_hosts={hostname: servers[y]},
                    restart_policy={"Name": "always"},
                    network_mode="host",
                ),
                environment={
                    "IP": "{}".format(servers[y]),
                    "CSGO_HOSTNAME": "csgo-server-{}".format(i),
                    "CSGO_PASSWORD": "",
                    "RCON_PASSWORD": "notbanana",
                    "STEAM_ACCOUNT_TOKEN": tokens[i] if len(tokens) > i else "",
                    "HOST_PORT": str(hostport + i),
                    "CLIENT_PORT": str(clientport + i),
                    "STV_PORT": str(stvport + i),
                },
                name="csgo-servers-{}".format(i),
            )
            client.start(container)
            topo.write("csgo-servers-{};{};{}\n".format(i, str(ip), client.base_url))
