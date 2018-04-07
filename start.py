import docker
import time
from launcher import *

if __name__ == '__main__':
    tls_config = docker.tls.TLSConfig(ca_cert='/root/.docker/ca.pem', client_cert=('/root/.docker/cert.pem', '/root/.docker/key.pem'))
    nb_csgo = 4
    configinsalan = True
    net='vlan-bond0.101'
    image='csgoserver'
    if(not configinsalan):
        client = docker.APIClient('tcp://192.168.0.103:2375', tls=tls_config)
        servers = [
            {'ip': '192.168.0.103', 'interface': 'bond0',
             'pool': docker.types.IPAMPool(
                 subnet='192.168.0.0/24',
                 gateway='192.168.0.1'
             )}
        ]
        db_ip = '192.168.0.106'
        ebot_ip = '192.168.0.107'
        ebotweb_ip = '192.168.0.108'
    else:
        client = docker.APIClient('tcp://172.16.1.3:2375', tls=tls_config)
        servers = [
            {'ip': '172.16.1.3', 'interface': 'eth0',
             'pool': docker.types.IPAMPool(
                 subnet='172.16.1.0/24',
                 gateway='172.16.1.1'
             )},
            {'ip': '172.16.1.4', 'interface': 'eth0',
             'pool': docker.types.IPAMPool(
                 subnet='172.16.1.0/24',
                 gateway='172.16.1.1'
             )}
        ]
        db_ip = '172.17.1.176'
        ebot_ip = '172.17.1.177'
        ebotweb_ip = '172.17.1.178'

    print("Making networks")
    create_network(servers, tls_config, net)
    print("Starting ebot containers")
    with open('topology.csv', 'w') as topo:
        launch(client, nb_csgo, servers, db_ip, ebot_ip, ebotweb_ip, net, topo)
        print("Deploying csgo servers")
        deploy(tls_config, nb_csgo, servers, net, ebotweb_ip, image, topo)
    print("Waiting for db to start...")
    #time.sleep(20)
    #print("Inserting servers into ebot db")
    #ebot_add_servers(servers, db_ip, net)
    
