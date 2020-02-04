FROM csgoinsalan
MAINTAINER nominoe kervadec <nominoe.kervadec@insa-rennes.fr>

WORKDIR /home/steam
USER steam

# make sure csgo is updated
RUN ./steamcmd.sh +login anonymous +force_install_dir csgo/ +app_update 740 validate +quit

RUN mkdir /home/steam/csgo/csgo/addons
RUN wget http://www.esport-tools.net/download/CSay-CSGO.zip  -P /tmp/
RUN unzip /tmp/CSay-CSGO.zip -d /home/steam/csgo/csgo/addons/ && rm /tmp/CSay-CSGO.zip

ADD ./entrypoint.sh entrypoint.sh

# add default configuration files
ADD cfg/ /home/steam/csgo/csgo/cfg
USER root
RUN chown -R steam:steam /home/steam/csgo/csgo/addons
RUN apt-get update && apt-get install -y iputils-ping$
USER steam
RUN cp /home/steam/csgo/csgo/gamemodes_server.txt.example /home/steam/csgo/csgo/gamemodes_server.txt
#ADD cfg/server.cfg /home/steam/csgo/csgo/cfg/server_last.cfg
