build:
	docker build -t steamcmd steamcmd/
	docker build -t csgoinsalan csgo/
	docker build -t csgoserver csgoserver/
	docker pull hsfactory/ebot
	docker pull hsfactory/ebotweb
	docker pull mysql:5.7
run:
	python3 start.py

