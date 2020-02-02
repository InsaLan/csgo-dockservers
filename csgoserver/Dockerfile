FROM csgoinsalan
MAINTAINER nominoe kervadec <nominoe.kervadec@insa-rennes.fr>

WORKDIR /home/steam
USER steam

# make sure csgo is updated
RUN ./steamcmd.sh +login anonymous +force_install_dir csgo/ +app_update 740 validate +quit
RUN  wget http://www.esport-tools.net/download/CSay-CSGO.zip  -P ctf/
RUN cd /cfg && unzip CSay-CSGO.zip && rm CSay-CSGO.zip
RUN mv /cfg/CSay-CSGO/ /cfg

ADD ./entrypoint.sh entrypoint.sh

# add default configuration files
ADD cfg/ /home/steam/csgo/csgo/cfg
ADD addons/ /home/steam/csgo/csgo/addons
USER root
RUN chown -R steam:steam /home/steam/csgo/csgo/addons
RUN apt-get update && apt-get install -y iputils-ping$
USER steam
RUN cp /home/steam/csgo/csgo/gamemodes_server.txt.example /home/steam/csgo/csgo/gamemodes_server.txt
#ADD cfg/server.cfg /home/steam/csgo/csgo/cfg/server_last.cfg

RUN mkdir -p /home/steam/.steam/sdk32/
RUN ln -s /home/steam/linux32/steamclient.so ~/.steam/sdk32/steamclient.so

CMD ./entrypoint.sh
