#!/bin/sh
# ZombieApocalypse - demarrage (Linux/Mac). Java 17 ou 21 requis.
cd "$(dirname "$0")"
exec java -Xms4G -Xmx8G -jar arclight-5dc8683.jar nogui
