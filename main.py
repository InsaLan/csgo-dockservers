import docker
import time
import yaml

# Disables the warnings you get when deploying
# Because the docker lib forces urllib3 to let you
# use untrusted certificates.
# That is fine. That is what we want. Shut up.
import urllib3
urllib3.disable_warnings()

from server_mgmt import deploy_ebotserver, deploy_csgoserver, register_server_ebot

if __name__ == "__main__":
    print("Reading configuration")
    with open("config.yml", "r") as config_file:
        config = yaml.load(config_file, Loader=yaml.FullLoader)

    tls_config = docker.tls.TLSConfig(
        ca_cert=config["docker_tls"]["ca_cert"],
        client_cert=config["docker_tls"]["client_cert"]
    )
    nb_csgo = config["csgo"]["nb_instances"]
    image = config["csgo"]["image_name"]
    servers = config["host"]["csgo_servers_ip"]
    ebot_ip = config["host"]["ebot_ip"]

    with open("topology.csv", "w") as topo:
        print("Starting ebot containers")
        deploy_ebotserver(ebot_ip, tls_config, topo)
        print("Deploying csgo servers")
        deploy_csgoserver(nb_csgo, servers, ebot_ip, image, tls_config, topo)

    print("Waiting for db to start...")
    time.sleep(20) #FIXME find a way to ping the DB instead of waiting a arbitrary amount of time
    print("Inserting servers into ebot db")
    register_server_ebot(servers, ebot_ip, tls_config)
