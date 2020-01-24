# INSALAN - dockcsgo

This project is the configuration (and deployment tool) of the InsaLan's CSGO servers. Look and adapt your configuration in the start.py file to your needs. All images need to be made beforehand.

## Images
To build the necessary images, run `make build` in the current repertory.
It will download CSGO, which could take a while, and you should check beforehand that your VM or server have around 50GB of free disk space.

## Dependencies
you just need to run pip install -r requirements.txt to install all dependencies :
- docker
- mysql-connector-python

## Docker daemon configuration

- First, generate TLS certificates for the CA, the server and the client. Follow the tutorial [here](https://docs.docker.com/engine/security/https).
 (#FIXME documentation should be more comprehensive)

- Then put the client and CA files (`ca-key.pem ca.pem cert.pem key.pem`) in your client docker configuration folder (in the config file here, it is `/root/.docker/`).

- Put the server and CA files (`ca.pem server-cert.pem server-key.pem`) in your server docker configuration (in the following part we consider that you put them in `/etc/docker/`).

- Then, configure the docker daemon to listen on port 2376 for incoming TLS connections.
To do so, open the file `/etc/systemd/system/docker.service` and replace the ExecStart by the following :
```
ExecStart=/usr/bin/dockerd -H fd:// --containerd=/run/containerd/containerd.sock \
	-H tcp://0.0.0.0:2376 --tlsverify --tlscacert=/etc/docker/ca.pem \
	--tlskey=/etc/docker/server-key.pem --tlscert=/etc/docker/server-cert.pem
```

- Test your configuration by running `docker --tlsverify --tlscacert=ca.pem --tlscert=cert.pem --tlskey=key.pem -H=127.0.0.1:2376 version`

## Usage
When your configuration is accurate and your images are built, simply use this command : python3 start.py

## FAQ
- Csgo server outdated ? docker rmi csgoserver && make build
- passwords ? find . -type f -exec grep --color -n -e password /dev/null \{\} +
- If you get a "docker.errors.TLSParameterError", you badly configured TLS connection to docker daemon
