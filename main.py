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
    db_ip = "172.16.1.3"
    ebot_ip = "172.16.1.3"
    ebotweb_ip = "172.16.1.3"

    print("Starting ebot containers")
    with open("topology.csv", "w") as topo:
        launch(client, db_ip, ebot_ip, ebotweb_ip, topo)
        print("Deploying csgo servers")
        deploy(nb_csgo, servers, ebotweb_ip, image, topo)
    print("Waiting for db to start...")
    time.sleep(20)
    print("Inserting servers into ebot db")
    ebot_add_servers(servers, db_ip)
