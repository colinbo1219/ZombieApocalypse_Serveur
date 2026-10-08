#!/bin/sh
# Compile ZAMoteur. Usage : sh moteur/build.sh <chemin/spigot-api-1.20.1.jar>
set -e
cd "$(dirname "$0")"
API="${1:-spigot-api.jar}"
rm -rf build && mkdir -p build/classes
javac --release 17 -encoding UTF-8 -nowarn -cp "$API" -d build/classes $(find src -name '*.java')
cp resources/* build/classes/
(cd build/classes && jar cf ../../../plugins/ZAMoteur.jar .)
echo "plugins/ZAMoteur.jar prêt"
