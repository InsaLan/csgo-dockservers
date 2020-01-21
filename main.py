import docker
import time
from server_mgmt import *

if __name__ == "__main__":
    tls_config = docker.tls.TLSConfig(
        ca_cert="/root/.docker/ca.pem",
        client_cert=("/root/.docker/cert.pem", "/root/.docker/key.pem"),
    )
    nb_csgo = 4
    image = "csgoserver"
    client = docker.APIClient("tcp://172.16.1.3:2375", tls=tls_config)

    print("Making networks")
    servers = [{"ip": "172.16.1.3"}, {"ip": "172.16.1.4"}, {"ip": "172.16.1.5"}]
    ebot_ip = "172.16.1.3"

    print("Starting ebot containers")
    with open("topology.csv", "w") as topo:
        deploy_ebotserver(client, ebot_ip, topo)
        print("Deploying csgo servers")
        deploy_csgoserver(nb_csgo, servers, ebot_ip, image, topo)
    print("Waiting for db to start...")
    time.sleep(20)
    print("Inserting servers into ebot db")
    register_server_ebot(servers, ebot_ip)
