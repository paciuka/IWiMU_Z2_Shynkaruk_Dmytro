"""Silnik wnioskujący: wnioskowanie w przód i wstecz na bazie wiedzy w JSON."""
import json
import operator
import sys
from pathlib import Path

OPERATORY = {
    "==": operator.eq, "!=": operator.ne,
    ">": operator.gt, ">=": operator.ge,
    "<": operator.lt, "<=": operator.le}


def wczytaj_baze(sciezka):
    with open(sciezka, encoding="utf-8") as f:
        return json.load(f)


def typ(baza, atrybut):
    if atrybut not in baza["atrybuty"]:
        raise ValueError(f"Niezadeklarowany atrybut: {atrybut}")
    return baza["atrybuty"][atrybut]["typ"]


def warunek_spelniony(warunek, fakty):
    atrybut, op, wartosc = warunek
    return (atrybut in fakty and fakty[atrybut] is not None
            and OPERATORY[op](fakty[atrybut], wartosc))


def regula_spelniona(regula, fakty):
    # TODO 1
    return all(warunek_spelniony(w, fakty) for w in regula["jesli"])


def wnioskuj_w_przod(baza, fakty):
    fakty = dict(fakty)
    slad = []
    zmiana = True
    while zmiana:
        zmiana = False
        for regula in baza["reguly"]:
            atrybut, wartosc = regula["to"]
            if (atrybut not in fakty
                    and regula_spelniona(regula, fakty)):
                fakty[atrybut] = wartosc            # TODO 2
                slad.append(regula["id"])
                zmiana = True
    return fakty, slad


def wnioskuj_wstecz(baza, cel, fakty, zapytaj, slad, powod=None):
    if cel in fakty:
        return fakty[cel]
    reguly = [r for r in baza["reguly"] if r["to"][0] == cel]
    if not reguly and typ(baza, cel) == "wniosek":       # luka w wiedzy
        return None
    if not reguly:                                        # TODO 3
        fakty[cel] = zapytaj(cel, powod)
        return fakty[cel]
    for regula in reguly:
        spelniona = True
        for atrybut, op, wartosc in regula["jesli"]:      # TODO 4
            znana = wnioskuj_wstecz(baza, atrybut, fakty,
                                    zapytaj, slad, regula)
            if znana is None or not OPERATORY[op](znana, wartosc):
                spelniona = False
                break
        if spelniona:
            fakty[cel] = regula["to"][1]
            slad.append(regula["id"])
            return fakty[cel]
    return None


def opis_warunku(w):
    return f"{w[0]} {w[1]} {w[2]}"


def zapytaj_konsola(baza, wejscie=input):
    """Zwraca funkcję zapytaj(atrybut, regula) pytającą użytkownika w konsoli."""
    licznik = [0]
    echo = not sys.stdin.isatty()

    def zapytaj(atrybut, regula):
        opis = baza["atrybuty"][atrybut]
        licznik[0] += 1
        if regula is not None:
            warunek = next(w for w in regula["jesli"] if w[0] == atrybut)
            print(f"(bo sprawdzam {regula['id']}: {opis_warunku(warunek)} …)")
        while True:
            odp = wejscie(f"pytanie {licznik[0]}: {opis['pytanie']} → ").strip()
            if echo:
                print(odp)
            if odp == "":
                return None                      # „nie wiem”
            if opis["typ"] == "liczba":
                try:
                    wartosc = float(odp.replace(",", "."))
                except ValueError:
                    print("  Podaj liczbę.")
                    continue
                if wartosc == int(wartosc):
                    wartosc = int(wartosc)
                return wartosc
            if odp in opis["wartosci"]:
                return odp
            print("  Dozwolone wartości: " + ", ".join(opis["wartosci"]))

    zapytaj.licznik = licznik
    return zapytaj


def konsultacja_wstecz(baza, wejscie=input):
    zapytaj = zapytaj_konsola(baza, wejscie)
    fakty, slad = {}, []
    wynik = wnioskuj_wstecz(baza, baza["cel"], fakty, zapytaj, slad)
    return wynik, slad, fakty, zapytaj.licznik[0]


def opis_decyzji(baza, slad):
    ostatnia = next((r for r in baza["reguly"] if r["id"] == slad[-1]), None) if slad else None
    return ostatnia.get("coto", "") if ostatnia else ""


if __name__ == "__main__":
    PLIK_BAZY = Path(__file__).parent.parent / "wiedza" / "moja_dziedzina.json"
    FAKTY = {"dystans": 4, "temperatura": 15, "opady": "brak",
             "bagaz": "duzy", "pora_dnia": "dzien", "spieszy_sie": "tak"}   # dane wejściowe
    baza = wczytaj_baze(PLIK_BAZY)
    cel = baza["cel"]

    print("=== Wnioskowanie w przód ===")
    fakty, slad = wnioskuj_w_przod(baza, FAKTY)
    print(f"Wynik: {fakty.get(cel)} | reguły: {' -> '.join(slad)}")

    print("\n=== Wnioskowanie wstecz ===")
    wynik, slad, fakty, pytan = konsultacja_wstecz(baza)
    print(f"Wynik: {wynik} | pytań: {pytan}")
    print(f"ślad: {' -> '.join(slad)}")
    nie_pytano = [a for a, o in baza["atrybuty"].items()
                  if o["typ"] != "wniosek" and a not in fakty]
    print("Nie zapytał o: " + (", ".join(nie_pytano) if nie_pytano else "—"))
