FROM ubuntu:latest
MAINTAINER nominoe kervadec <nominoe.kervadec@insa-rennes.fr>

# install required dependencies
RUN dpkg --add-architecture i386 && apt-get update && apt-get install -o APT::Immediate-Configure=0 -y wget lib32gcc1 libstdc++6 libstdc++6:i386 unzip gdb

# install steamcmd
RUN useradd -ms /bin/bash steam
WORKDIR /home/steam
USER steam
RUN wget -O /tmp/steamcmd_linux.tar.gz http://media.steampowered.com/installer/steamcmd_linux.tar.gz
RUN tar -xvzf /tmp/steamcmd_linux.tar.gz
RUN rm /tmp/steamcmd_linux.tar.gz

# install steamcmd
RUN ./steamcmd.sh +quit 
