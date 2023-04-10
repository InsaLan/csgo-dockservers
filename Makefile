build:
	docker build -t steamcmd steamcmd/
	docker build -t csgoinsalan csgo/
	docker build -t csgoserver csgoserver/
	docker pull hsfactory/ebot
	docker pull hsfactory/ebotweb
	docker pull mysql:5.7
run:
	python3 main.py

stop:
	-docker rm $$(docker stop $$(docker ps -a -q --filter name=csgo-server ))
	-docker rm $$(docker stop $$(docker ps -a -q --filter name=ebot ))
	-docker rm $$(docker stop $$(docker ps -a -q --filter name=db ))

