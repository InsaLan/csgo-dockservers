#!/bin/bash
set -euo pipefail

EBOT_SERVER_DNS="glados.insalan"
EBOT_SERVER_IP="172.16.1.10"

mkdir -p certs && cd certs
mkdir -p ca && cd ca

openssl genrsa -aes256 -out ca-key.pem -passout "pass:test" 4096
openssl req -subj "/C=US/ST=Denial/L=Springfield/O=Dis/CN=$EBOT_SERVER_DNS" -passin "pass:test" -new -x509 -days 365 -key ca-key.pem -sha256 -out ca.pem

chmod -v 0400 ca-key.pem
chmod -v 0444 ca.pem

cd ..

while IFS=, read -r slave_dns slave_ip
do

	mkdir -p $slave_dns && cd $slave_dns	
	mkdir -p server && cd server

	openssl genrsa -out server-key.pem 4096
	openssl req -subj "/CN=$slave_dns" -sha256 -new -key server-key.pem -out server.csr

	echo subjectAltName = DNS:$slave_dns,IP:$slave_ip,IP:127.0.0.1 >> extfile.cnf
	echo extendedKeyUsage = serverAuth >> extfile.cnf

	echo $(pwd)
	openssl x509 -req -days 365 -sha256 -in server.csr -CA ../../ca/ca.pem -CAkey ../../ca/ca-key.pem  -CAcreateserial -out server-cert.pem -extfile extfile.cnf -passin "pass:test"

	chmod -v 0400 server-key.pem
	chmod -v 0444 server-cert.pem


	cd .. && mkdir -p client && cd client
	
	openssl genrsa -out key.pem 4096
	
	openssl req -subj "/CN=$slave_dns" -new -key key.pem -out client.csr
	echo extendedKeyUsage = clientAuth > extfile-client.cnf

	openssl x509 -req -days 365 -sha256 -in client.csr -CA ../../ca/ca.pem -CAkey ../../ca/ca-key.pem -CAcreateserial -out cert.pem -extfile extfile-client.cnf -passin "pass:test"

	chmod -v 0400 key.pem
	chmod -v 0444 cert.pem

	cd ..

	# https://stackoverflow.com/questions/9393038/ssh-breaks-out-of-while-loop-in-bash

	ssh $slave_dns "mkdir -p /root/.docker" < /dev/null

	scp client/{cert,key}.pem $slave_dns:/root/.docker < /dev/null
	scp server/server-{key,cert}.pem $slave_dns:/etc/docker/ < /dev/null
	scp server/server-{key,cert}.pem $slave_dns:/etc/docker/ < /dev/null
	scp ../ca/ca.pem  $slave_dns:/etc/docker/ < /dev/null
	scp ../ca/{ca,ca-key}.pem  $slave_dns:/root/.docker/ < /dev/null

	ssh $slave_dns "sed -i 's/ExecStart=.*$/ExecStart=\/usr\/bin\/dockerd -H fd:\/\/ --containerd=\/run\/containerd\/containerd.sock -H tcp:\/\/0.0.0.0:2376 --tlsverify --tlscacert=\/etc\/docker\/ca.pem --tlskey=\/etc\/docker\/server-key.pem --tlscert=\/etc\/docker\/server-cert.pem/g' /lib/systemd/system/docker.service" < /dev/null
	
	ssh $slave_dns "systemctl daemon-reload" < /dev/null
	ssh $slave_dns "systemctl restart docker" < /dev/null
	
	cd ..

done < "../server_list"
