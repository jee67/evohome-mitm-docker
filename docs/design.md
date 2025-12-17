# Evohome MITM – Ontwerp & Gedrag

## 1. Doel en scope

Deze applicatie fungeert als een transparante RAMSES-II man-in-the-middle
tussen Evohome en R8810A/CiC.

Doel:
- waterzijdige begrenzing van het CH-setpoint (verb 1F09),
- behoud van Evohome-regellogica,
- optimale samenwerking met een Quatt hybride warmtepomp.

Alle overige frames worden ongewijzigd doorgelaten.

---

## 2. Architectuur

- RF-communicatie via evofw3 USB-stick
- MITM draait als Docker-container op een dedicated Raspberry Pi
- Geen Home Assistant afhankelijkheid
- MQTT uitsluitend voor observatie en context-input

Datastromen:

Evohome ⇄ MITM ⇄ R8810A/CiC ⇄ Ketel  
Home Assistant → MQTT → MITM (context)

---

## 3. CH-setpoint gedrag (1F09)

- Idle-setpoint (10 °C) blijft onaangeroerd
- Maximaal CH-setpoint wordt begrensd:
  - statisch (config)
  - adaptief (buitentemperatuur)
- Stijgen: gerampt (+2 °C per 30 s)
- Dalen: direct toegestaan

Dit voorkomt hydraulische schokken en pendelgedrag.

---

## 4. Adaptieve CH-max (weersafhankelijk)

De MITM berekent een *effectieve* CH-max op basis van buitentemperatuur
(ontvangen via MQTT).

Eigenschappen:
- lineaire interpolatie tussen curvepunten
- harde minimum- en maximumwaarden
- alleen actief bij geldige, recente data
- fallback naar vaste CH-max bij dataverlies

De MITM stuurt **nooit actief**; zij stelt uitsluitend een plafond.

---

## 5. MQTT-contract

### Inkomend (context)

**Topic**
