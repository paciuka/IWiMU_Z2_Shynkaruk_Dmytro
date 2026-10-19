# IWiMU · Z2 · Silnik wnioskujący i baza wiedzy

Dziedzina: **dobór środka transportu na trasie dom – uczelnia** (pieszo, hulajnoga, rower, komunikacja miejska, taksówka).

## Uruchomienie

```
python se/sprawdz_format.py wiedza/moja_dziedzina.json
python se/test_silnik.py
python se/test_moja_dziedzina.py
python se/silnik.py
```

## Konsultacja wstecz (zapis z terminala)

```
python se/silnik.py
(bo sprawdzam R12: pora_dnia == noc …)
pytanie 1: Jaka jest pora dnia? → dzien
(bo sprawdzam R9: bagaz == duzy …)
pytanie 2: Jaki bagaż trzeba zabrać? → duzy
(bo sprawdzam R1: dystans <= 1.5 …)
pytanie 3: Jaki jest dystans trasy (km)? → 4
Wynik: komunikacja_miejska | pytań: 3
ślad: R9 -> R2 -> R14
Nie zapytał o: temperatura, opady, spieszy_sie
```

System zadał trzy pytania, ponieważ cel `srodek_transportu` ustalają reguły R12–R22, sprawdzane w kolejności listy. R12 wymaga pory dnia (stąd pytanie 1), R13 – wniosku `ladunek`, który zależy od bagażu (pytanie 2), a wniosek `zasieg` – od dystansu (pytanie 3). Reguła R14 (ciężki bagaż, średni zasięg) spełniła się przed sprawdzeniem pogody, dlatego system nie zapytał o temperaturę, opady ani pośpiech.

## Kolejność reguł

Przy konflikcie wygrywa reguła stojąca wyżej, ponieważ ustalony fakt nie jest nadpisywany; reguły nocne (R12) i bagażowe (R13–R15) stoją przed regułami pogodowymi (R16–R22), bo nocny przejazd i ciężki bagaż są ważniejsze dla bezpieczeństwa i wygody niż pogoda.
