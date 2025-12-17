# EVOHOME-MITM-DOCKER – Inbedrijfstelling

## Doel
Dit stappenplan beschrijft hoe **evohome-mitm-docker** veilig en gecontroleerd
in gebruik wordt genomen op een aparte Raspberry Pi.

---

## 0. Vooraf controleren

Controleer eerst of het volgende in orde is:

- Raspberry Pi draait op **Raspberry Pi OS Lite**
- **Docker** en **docker-compose** zijn geïnstalleerd
- De **MQTT-broker** is bereikbaar (bijvoorbeeld `10.0.0.190`)
- Home Assistant stuurt de buitentemperatuur via MQTT naar  
  `evohome/context/outdoor_temperature` (met `retain=true`)
- De Evohome-installatie werkt normaal
- De **evofw3 USB-stick** is aangesloten

---

## 1. Software ophalen

Download de software en ga naar de juiste map:

    git clone https://github.com/jee67/evohome-mitm-docker.git
    cd evohome-mitm-docker

---

## 2. USB-stick controleren

Controleer of de RF-stick wordt herkend:

    ls -l /dev/serial/by-id/

Je ziet bijvoorbeeld:

    usb-evofw3-mitm -> ../../ttyUSB0

Komt dit pad niet overeen, pas het dan aan in:

    docker/docker-compose.yml

---

## 3. Configuratie controleren

Open het configuratiebestand:

    cat config/config.yaml

Controleer minimaal:

- het juiste **serial device**
- het juiste **MQTT-adres** (`10.0.0.190`)
- dat **adaptieve regeling** is ingeschakeld (`enabled: true`)
- dat de **curve** past bij jouw installatie

---

## 4. Container bouwen

Bouw de Docker-container:

    docker compose build

Dit moet zonder fouten verlopen.

---

## 5. Container starten

Start de container:

    docker compose up -d

Controleer of de container draait:

    docker ps

---

## 6. Logcontrole

Bekijk de logregels:

    docker logs -f evohome-mitm-docker

Je verwacht onder andere:

- een startmelding
- een melding met de buitentemperatuur
- **geen foutmeldingen**

---

## 7. Fail-safe test

Stop de MITM tijdelijk:

    docker stop evohome-mitm-docker

Controleer dat:

- Evohome normaal blijft verwarmen
- er geen communicatiefouten optreden
- het comfort gelijk blijft

Start daarna opnieuw:

    docker start evohome-mitm-docker

---

## 8. Adaptieve CH-max controleren (optioneel)

Deze stap is optioneel, maar aanbevolen:

- Verander tijdelijk de buitentemperatuur in Home Assistant
- Bekijk de logs
- Controleer dat de watertemperatuur niet boven het ingestelde maximum komt
- Let op dat verhogingen rustig verlopen (in stappen)

---

## 9. Definitief in gebruik nemen

Herstart de container:

    docker restart evohome-mitm-docker

Laat het systeem daarna minimaal **24 uur** draaien en let op:

- comfort in huis
- gedrag van de ketel
- eventueel pendelgedrag

---

## 10. Terugval bij problemen

Bij twijfel of storing kun je altijd stoppen:

    docker stop evohome-mitm-docker

Evohome neemt dan direct weer volledig de regeling over.
