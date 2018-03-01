FROM steamcmd
MAINTAINER nominoe kervadec <nominoe.kervadec@insa-rennes.fr>

# install csgo up to date
WORKDIR /home/steam
USER steam
RUN ./steamcmd.sh +login anonymous +force_install_dir csgo/ +app_update 740 validate +quit
