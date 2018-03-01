import time
import docker
import mysql.connector
import ipaddress
import os

from math import *

tokens=[]

def create_network(servers, tls_config, netn):
    for s in servers:
        client = docker.APIClient(base_url='tcp://{}:2375'.format(s['ip']), tls=tls_config)
        net = client.networks(filters={'name': netn})
        ipamm = docker.types.IPAMConfig(pool_configs=[s['pool']])
        if(len(net) > 0):
            nett = net.pop()['Id']
            client.remove_network(nett)
        if(len(net) == 0):
            client.create_network(name=netn, driver='macvlan', options={'parent': s['interface']}, ipam=ipamm)
        
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
    #cursor.execute("TRUNCATE TABLE servers")
    add_server = ("INSERT INTO servers"
                  "(ip, rcon, hostname, tv_ip, created_at, updated_at)"
                  "values(%s,%s,%s,%s,'2017-12-17 00:00:00','2017-12-17 00:00:00')")
    for i in csgo_containers:
        ip = i.attrs['NetworkSettings']['Networks'][net]['IPAddress']
        name = i.attrs['Name']
        data_server = ("{}:27015".format(ip), "notbanana", name, "{}:27020".format(ip))
        cursor.execute(add_server, data_server)
    cnx.commit()
    cursor.close()
    cnx.close()

def deploy(tlsconfig, nb_csgo, servers, net, ebotweb_ip, image):
    pwd = os.getcwd()
    ip = ipaddress.ip_address(ebotweb_ip)
    for y in range(0, len(servers)):
        for i in range(int(ceil(nb_csgo/len(servers)) * y), int(ceil(nb_csgo/len(servers)) * (y+1))):
            ip = ipaddress.ip_address(ip+1)
            tls_config = docker.tls.TLSConfig(ca_cert='/root/.docker/ca.pem', client_cert=('/root/.docker/cert.pem', '/root/.docker/key.pem'))
            client = docker.APIClient(base_url='tcp://{}:2375'.format(servers[y]['ip']), tls=tls_config)
            container = client.create_container(
                image, detach=True,
                host_config = client.create_host_config(
                    restart_policy={'Name': 'always'}
                ),
                environment={'CSGO_HOSTNAME': "csgo-server-{}".format(i),
                                    'CSGO_PASSWORD': '',
                                    'RCON_PASSWORD': 'notbanana',
                                    'STEAM_ACCOUNT_TOKEN': tokens[i],
                                    'HOST_PORT': '27015',
                                    'CLIENT_PORT': '27005',
                                    'STV_PORT': '27020'},
                networking_config={
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

def launch(client, nb_csgo, servers, db_ip, ebot_ip, ebotweb_ip, net):
    db_container = client.create_container(
        'mysql:5.7', detach=True, volumes=['/var/lib/mysql'],
        host_config=client.create_host_config(restart_policy={'Name': 'always'},
                                              binds=['/opt/docker/ebot/mysql:/var/lib/mysql']),
        environment={'MYSQL_DATABASE': 'ebotv3', 'MYSQL_USER': 'ebotv3',
                     'MYSQL_PASSWORD': 'ebotv3', 'MYSQL_ROOT_PASSWORD': 'nhurmanroot'},
        command='mysqld',
        networking_config={
            'EndpointsConfig': {
                net: {
                    'IPAMConfig': {
                        'IPv4Address': db_ip,
                    }
                }
            }
        },
        name='db_container')
    
    ebot_container = client.create_container(
        'hsfactory/ebot', detach=True, volumes=['/ebot/logs', '/ebot/demos'],
        host_config=client.create_host_config(restart_policy={'Name': 'always'},
                                              extra_hosts={'mysql': db_ip},
                                              binds=['/opt/docker/ebot/logs:/ebot/logs',
                                                       '/opt/docker/ebot/demo:/ebot/demos']),
        environment={'EXTERNAL_IP': ebot_ip, 'MYSQL_HOST': 'mysql',
                     'MYSQL_PORT': '3306', 'MYSQL_DB': 'ebotv3',
                     'MYSQL_USER': 'ebotv3', 'MYSQL_PASS': 'ebotv3',
                     'LO3_METHOD': 'restart', 'KO3_METHOD': 'restart',
                     'DEMO_DOWNLOAD': 'true', 'REMIND_RECORD': 'false',
                     'DAMAGE_REPORT': 'true', 'DELAY_READY': 'false',
                     'NODE_STARTUP_METHOD': 'node', 'TOORNAMENT_PLUGIN_KEY': ''},
        networking_config={
            'EndpointsConfig': {
                net: {
                    'IPAMConfig': {
                        'IPv4Address': ebot_ip,
                    }
                }
            }
        },
        name='ebot_container')
    
    ebotweb_container = client.create_container(
        'hsfactory/ebotweb', detach=True, volumes=['/ebot/logs', '/ebot/demos'],
        host_config=client.create_host_config(restart_policy={'Name': 'always'},
                                              extra_hosts={'mysql': db_ip, 'ebot': ebot_ip},
                                              binds=['/opt/docker/ebot/logs:/opt/ebot/logs',
                                                       '/opt/docker/ebot/demo:/opt/ebot/demos']),
        environment={'EBOT_IP': ebot_ip, 'EBOT_PORT': '12360',
                     'EBOT_ADMIN_USER': 'insalan', 'EBOT_ADMIN_PASS': 'nhurman',
                     'EBOT_ADMIN_MAIL': 'insalade@ebot', 'MYSQL_HOST': 'mysql',
                     'MYSQL_PORT': '3306', 'MYSQL_DB': 'ebotv3',
                     'MYSQL_USER': 'ebotv3', 'MYSQL_PASS': 'ebotv3',
                     'DEMO_DOWNLOAD': 'true', 'DEFAULT_RULES': 'esl5on5', 'TOORNAMENT_ID': '',
                     'TOORNAMENT_SECRET': '',  'TOORNAMENT_PLUGIN_KEY': '',
                     'TOORNAMENT_API_KEY': ''},
        networking_config={
            'EndpointsConfig': {
                net: {
                    'IPAMConfig': {
                        'IPv4Address': ebotweb_ip,
                    }
                }
            }
        },
        name='ebotweb_container')
    
    client.start(db_container)
    time.sleep(10)
    client.start(ebot_container)
    time.sleep(10)
    client.start(ebotweb_container)

    
    
