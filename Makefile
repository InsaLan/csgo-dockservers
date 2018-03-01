build:
	docker build -t steamcmd steamcmd/
	docker build -t csgoinsalan csgo/
	docker build -t csgoserver csgoserver/
	docker build -t csgobarebone csgobarebone/
	docker pull hsfactory/ebot
	docker pull hsfactory/ebotweb
	docker pull mysql:5.7
run:
	python start.py
secure:
	iptables -I INPUT -p tcp -s IPACHANGER --dport 2375 -j ACCEPT
	iptables -I INPUT -p tcp -s 0.0.0.0/0 --dport 2375 -j DROP
stop:
	./killswarm.sh

superStop:
	./killswarm.sh 1
