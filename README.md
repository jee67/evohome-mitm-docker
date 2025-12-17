# evohome-mitm-docker
evohome mitm - docker Versie

Docker-based Evohome MITM appliance.

- Waterzijdige CH-setpoint begrenzing (RAMSES-II 1F09)
- Adaptieve CH-max o.b.v. buitentemperatuur
- Fail-safe RF pass-through
- Geschikt voor Quatt hybride systemen



## EVOHOME-MITM-DOCKER — INBEDRIJFSTELLING
## Doel: gecontroleerde livegang op dedicated Raspberry Pi



## 0. Randvoorwaarden (handmatig checken) 
- Raspberry Pi OS Lite draait
- Docker + docker-compose zijn geïnstalleerd
- MQTT broker bereikbaar (bijv. 10.0.0.190)
- Home Assistant publiceert buitentemperatuur op:
    evohome/context/outdoor_temperature (retain=true)
- Evohome installatie is operationeel
- evofw3 USB-stick beschikbaar


## 1. Repo ophalen
git clone https://github.com/<jouw-account>/evohome-mitm-docker.git
cd evohome-mitm-docker


## 2. RF-stick detectie
ls -l /dev/serial/by-id/

Verwacht iets als:
 usb-evofw3-mitm -> ../../ttyUSB0

Pas zo nodig het pad aan in docker/docker-compose.yml


## 3. Configuratie controleren
cat config/config.yaml

Verifieer minimaal:
- serial.device
- mqtt.host = 10.0.0.190
- adaptive.enabled = true
- curve conform jouw installatie


## 4. Container bouwen
docker compose build

Verwacht: geen errors


## 5. Container starten ====================================================
docker compose up -d

Controleer dat hij draait
docker ps


## 6. Logcontrole (cruciaal) ===============================================
docker logs -f evohome-mitm-docker

 Verwacht o.a.:
 INFO evohome-mitm-docker started
 INFO Outdoor temperature X.X °C
 GEEN Python exceptions


## 7. Fail-safe test 
Stop MITM expliciet
docker stop evohome-mitm-docker

Verwacht:
- Evohome blijft verwarmen
- Geen communicatiefouten
- Geen comfortverlies

Start opnieuw
docker start evohome-mitm-docker


##  8. Adaptieve CH-max validatie
 (optioneel, gecontroleerd)
 - Verander buitentemperatuur in Home Assistant
 - Observeer logs
 - Controleer dat CH-setpoint niet boven curve-plafond komt
 - Let op ramping (+2 °C per 30 s)


## 9. Definitieve ingebruikname
docker restart evohome-mitm-docker

Laat minimaal 24 uur ononderbroken draaien
Observeer comfort, ketelgedrag en pendelgedrag


## 10. Terugvalscenario (altijd beschikbaar)
Bij twijfel of storing:
docker stop evohome-mitm-docker

Evohome neemt direct volledige regie terug
