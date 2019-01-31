import time
import docker
import mysql.connector
import ipaddress
import os
import re
from math import *
from key import *

def create_macvlan_network(servers, tls_config, netn):
    for s in servers:
        client = docker.APIClient(base_url='tcp://{}:2375'.format(s['ip']), tls=tls_config)
        net = client.networks(filters={'name': netn})
        ipamm = docker.types.IPAMConfig(pool_configs=[s['pool']])
        if(len(net) > 0):
            nett = net.pop()['Id']
            client.remove_network(nett)
        if(len(net) == 0):
            client.create_network(name=netn, driver='macvlan', options={'parent': s['interface']}, ipam=ipamm)
            
def create_bridge_network(servers, tls_config, netn):
    for s in servers:
        client = docker.APIClient(base_url='tcp://{}:2375'.format(s['ip']), tls=tls_config)
        net = client.networks(filters={'name': netn})
        ipamm = docker.types.IPAMConfig(pool_configs=[s['pool']])
        if(len(net) > 0):
            nett = net.pop()['Id']
            client.remove_network(nett)
        if(len(net) == 0):
            client.create_network(name=netn, driver='bridge', ipam=ipamm)
            
def ebot_add_servers(servers, db_ip, net):
    containers = []
    csgo_containers = []
    tls_config = docker.tls.TLSConfig(ca_cert='/root/.docker/ca.pem', client_cert=('/root/.docker/cert.pem', '/root/.docker/key.pem'))
    for s in servers:
        client = docker.DockerClient(base_url='tcp://{}:2375'.format(s['ip']), tls=tls_config) 
        containers += client.containers.list("all")
        csgo_containers += list(filter(lambda c: c.attrs['Config']['User'] == 'steam', containers))
        
    cnx = mysql.connector.connect(user='ebotv3', password='ebotv3', host=db_ip, database='ebotv3')
    cursor = cnx.cursor()
    try:
        cursor.execute("delete from servers where id!=-1")
    except:
        print("truncate failed")
    try:
        add_server = ("INSERT INTO servers"
                      "(ip, rcon, hostname, tv_ip, created_at, updated_at)"
                      "values(%s,%s,%s,%s,'2017-12-17 00:00:00','2017-12-17 00:00:00')")
        stvp = re.compile("STV_PORT")
        hostp = re.compile("HOST_PORT")
        ipp = re.compile("IP")
        for i in csgo_containers:
            for y in i.attrs['Config']['Env']:
                if(stvp.search(y)):
                    stvport = re.split("=", y)[1]
                if(hostp.search(y)):
                    hostport = re.split("=", y)[1]
                if(ipp.search(y)):
                    ip = re.split("=", y)[1]
            name = i.attrs['Name']
            data_server = ("{}:{}".format(ip, hostport), "notbanana", name, "{}:{}".format(ip, stvport))
            cursor.execute(add_server, data_server)
            cnx.commit()
        cursor.close()
        cnx.close()
    except:
        print("insertion failed")
    
def deploy(tlsconfig, nb_csgo, servers, net, ebotweb_ip, image, topo):
    pwd = os.getcwd()
    ip = ipaddress.ip_address(ebotweb_ip)
    hostport = 27015
    clientport = hostport + nb_csgo
    stvport = clientport + nb_csgo
    hostname = 'csgoinsalan'
    nb_serv = len(servers) + 1
    print(len(servers))
    print(int(ceil(nb_csgo/len(servers))))
    for y in range(0, len(servers)):
        for i in range(int(ceil(nb_csgo/nb_serv) * y), int(ceil(nb_csgo/nb_serv) * (y+1))):
            ip = ipaddress.ip_address(ip+1)
            tls_config = docker.tls.TLSConfig(ca_cert='/root/.docker/ca.pem', client_cert=('/root/.docker/cert.pem', '/root/.docker/key.pem'))
            client = docker.APIClient(base_url='tcp://{}:2375'.format(servers[y]['ip']), tls=tls_config)
            container = client.create_container(
                image, detach=True, hostname=hostname,
                host_config = client.create_host_config(
                    extra_hosts={hostname: servers[y]['ip']} if net=='host' else {},
                    restart_policy={'Name': 'always'},
                    network_mode= 'host' if net=='host' else None
                ),
                environment={ 'IP': "{}".format(servers[y]['ip']),
                              'CSGO_HOSTNAME': "csgo-server-{}".format(i),
                             'CSGO_PASSWORD': '',
                             'RCON_PASSWORD': 'notbanana',
                             'STEAM_ACCOUNT_TOKEN': tokens[i] if len(tokens) > i else  '',
                             'HOST_PORT': str(hostport+i) if net=='host' else '27015',
                             'CLIENT_PORT': str(clientport+i) if net=='host' else '27005',
                             'STV_PORT': str(stvport+i) if net=='host' else '27020'},
                networking_config= None
                if net == 'host' else
                {
                    'EndpointsConfig': {
                        net: {
                            'IPAMConfig': {
                                'IPv4Address': str(ip)
                            }
                        }
                    }
                },
                name="csgo-servers-{}".format(i))
            client.start(container)
            topo.write("csgo-servers-{};{};{}\n".format(i, str(ip), client.base_url))

def launch(client, nb_csgo, servers, db_ip, ebot_ip, ebotweb_ip, net, topo):
    db_container = client.create_container(
        'mysql:5.7', detach=True,
        host_config=client.create_host_config(restart_policy={'Name': 'always'},
                                              mounts=[docker.types.Mount('/var/lib/mysql',
                                                                         '/opt/docker/ebot/mysql',
                                                                         type='bind')
                                                      ],
                                              network_mode= 'host' if net=='host' else None
        ),
        environment={'MYSQL_DATABASE': 'ebotv3', 'MYSQL_USER': 'ebotv3',
                     'MYSQL_PASSWORD': 'ebotv3', 'MYSQL_ROOT_PASSWORD': 'nhurmanroot'},
        command='mysqld',
        networking_config= None
        if net == 'host' else
        {
            'EndpointsConfig': {
                net: {
                    'IPAMConfig': {
                        'IPv4Address': db_ip,
                    }
                }
            }
        },
        name='db_container')
    topo.write('db_container;{};{}\n'.format(db_ip, client.base_url))
    
    ebot_container = client.create_container(
        'hsfactory/ebot', detach=True, hostname='ebot',
        host_config=client.create_host_config(restart_policy={'Name': 'always'},
                                              extra_hosts={'mysql': db_ip, 'ebot': ebot_ip},
                                              mounts=[docker.types.Mount('/ebot/logs',
                                                                         '/opt/docker/ebot/logs',
                                                                         type='bind'),
                                                      docker.types.Mount('/ebot/demos',
                                                                         '/opt/docker/ebot/demo',
                                                                         type='bind')],
                                              network_mode= 'host' if net=='host' else None
        ),
        environment={'EXTERNAL_IP': ebot_ip, 'MYSQL_HOST': 'mysql',
                     'MYSQL_PORT': '3306', 'MYSQL_DB': 'ebotv3',
                     'MYSQL_USER': 'ebotv3', 'MYSQL_PASS': 'ebotv3',
                     'LO3_METHOD': 'restart', 'KO3_METHOD': 'restart',
                     'DEMO_DOWNLOAD': 'true', 'REMIND_RECORD': 'false',
                     'DAMAGE_REPORT': 'true', 'DELAY_READY': 'false',
                     'NODE_STARTUP_METHOD': 'node', 'TOORNAMENT_PLUGIN_KEY': ''},
        networking_config= None
        if net == 'host' else
        {
            'EndpointsConfig': {
                net: {
                    'IPAMConfig': {
                        'IPv4Address': ebot_ip,
                    }
                }
            }
        },
        name='ebot_container')
    topo.write('ebot_container;{};{}\n'.format(ebot_ip, client.base_url))
    
    ebotweb_container = client.create_container(
        'hsfactory/ebotweb', detach=True,
        host_config=client.create_host_config(restart_policy={'Name': 'always'},
                                              extra_hosts={'mysql': db_ip, 'ebot': ebot_ip},
                                              mounts=[docker.types.Mount('/opt/ebot/logs',
                                                                         '/opt/docker/ebot/logs',
                                                                         type='bind'),
                                                      docker.types.Mount('/opt/ebot/demos',
                                                                         '/opt/docker/ebot/demo',
                                                                         type='bind')],
                                              network_mode= 'host' if net=='host' else None
        ),
        environment={'EBOT_IP': ebot_ip, 'EBOT_PORT': '12360',
                     'EBOT_ADMIN_USER': 'insalan', 'EBOT_ADMIN_PASS': 'nhurman',
                     'EBOT_ADMIN_MAIL': 'insalade@ebot', 'MYSQL_HOST': 'mysql',
                     'MYSQL_PORT': '3306', 'MYSQL_DB': 'ebotv3',
                     'MYSQL_USER': 'ebotv3', 'MYSQL_PASS': 'ebotv3',
                     'DEMO_DOWNLOAD': 'true', 'DEFAULT_RULES': 'esl5on5', 'TOORNAMENT_ID': '',
                     'TOORNAMENT_SECRET': '',  'TOORNAMENT_PLUGIN_KEY': '',
                     'TOORNAMENT_API_KEY': ''},
        networking_config= None
        if net == 'host' else
        {
            'EndpointsConfig': {
                net: {
                    'IPAMConfig': {
                        'IPv4Address': ebotweb_ip,
                    }
                }
            }
        },
        name='ebotweb_container')
    topo.write('ebotweb_container;{};{}\n'.format(ebotweb_ip, client.base_url))
    
    client.start(db_container)
    time.sleep(10)
    client.start(ebot_container)
    time.sleep(10)
    client.start(ebotweb_container)

