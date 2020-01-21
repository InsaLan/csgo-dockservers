import docker
import time
import yaml
from server_mgmt import *

if __name__ == "__main__":
    with open("config.yml", "r") as config_file:
        config = yaml.load(config_file,Loader=yaml.FullLoader)

    tls_config = docker.tls.TLSConfig(
        config["docker_tls"]
    )
    nb_csgo = config["csgo"]["nb_instances"]
    image = config["csgo"]["image_name"]
    client = docker.APIClient("{}:{}".format(config["docker"]["connection"], config["docker"]["port"]), tls=tls_config)

    print("Making networks")
    servers = config["host"]["csgo_servers_ip"]
    ebot_ip = config["host"]["ebot_ip"]

    print("Starting ebot containers")
    with open("topology.csv", "w") as topo:
        deploy_ebotserver(client, ebot_ip, topo)
        print("Deploying csgo servers")
        deploy_csgoserver(nb_csgo, servers, ebot_ip, image, topo)
    print("Waiting for db to start...")
    time.sleep(20)
    print("Inserting servers into ebot db")
    register_server_ebot(servers, db_ip)
