import docker
import time
from launcher import *

if __name__ == '__main__':
    tls_config = docker.tls.TLSConfig(ca_cert='/root/.docker/ca.pem', client_cert=('/root/.docker/cert.pem', '/root/.docker/key.pem'))
    nb_csgo = 4
    macvlan = True
    image='csgoserver'
    client = docker.APIClient('tcp://192.168.0.103:2375', tls=tls_config)
    
    print("Making networks")
    if(macvlan):
        pool = docker.types.IPAMPool(
            subnet='192.168.0.0/24',
            gateway='192.168.0.1'
        )
        servers = [
            {'ip': '192.168.0.103', 'interface': 'bond0',
             'pool': pool},
        ]
        net= 'macvlan-csgo'
        db_ip = '192.168.0.176'
        ebot_ip = '192.168.0.177'
        ebotweb_ip = '192.168.0.178'
        create_macvlan_network(servers, tls_config, net)
    else:
        servers = [
            {'ip': '192.168.0.103'}
        ]
        net = 'host'
        db_ip = '192.168.0.103'
        ebot_ip = '192.168.0.103'
        ebotweb_ip = '192.168.0.103'
    
    print("Starting ebot containers")
    with open('topology.csv', 'w') as topo:
        launch(client, nb_csgo, servers, db_ip, ebot_ip, ebotweb_ip, net, topo)
        print("Deploying csgo servers")
        deploy(tls_config, nb_csgo, servers, net, ebotweb_ip, image, topo)
    print("Waiting for db to start...")
    time.sleep(20)
    print("Inserting servers into ebot db")
    ebot_add_servers(servers, db_ip, net)
    
