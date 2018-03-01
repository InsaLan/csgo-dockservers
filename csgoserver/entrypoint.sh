#!/bin/bash
set -e
trap '' TERM INT HUP

# Ensure csgo is up to date; might be removed to speed up deploy process
#./steamcmd.sh +login anonymous +force_install_dir csgo/ +app_update 740 validate +quit

#if [ -d /home/steam/htdocs ]; then
#	echo "Copying htdocs..."
#	cp -fR /home/steam/csgo/csgo/maps /home/steam/htdocs
#	cp -fR /home/steam/csgo/csgo/sound /home/steam/htdocs
#fi

cd csgo

./srcds_run -game csgo +hostname "$CSGO_HOSTNAME" -usercon +rcon_password "$RCON_PASSWORD" +sv_setsteamaccount "$STEAM_ACCOUNT_TOKEN" -net_port_try 1 -console -log on -tickrate 128 -debug +hostport "$HOST_PORT" +clientport "$CLIENT_PORT" +tv_port "$STV_PORT" +game_type 0 +game_mode 1 +mapgroup mg_active +map de_cache


