"""Własne testy bazy wiedzy wiedza/moja_dziedzina.json w obu trybach wnioskowania."""
import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from silnik import wczytaj_baze, wnioskuj_w_przod, wnioskuj_wstecz

BAZA = wczytaj_baze(Path(__file__).parent.parent / "wiedza" / "moja_dziedzina.json")
CEL = BAZA["cel"]

PRZYPADKI = [
    # (nr, rodzaj, dane wejściowe, oczekiwany wynik)
    ("T1", "typowy", {"dystans": 4, "temperatura": 15, "opady": "brak", "bagaz": "maly",
                      "pora_dnia": "dzien", "spieszy_sie": "tak"}, "hulajnoga"),
    ("T2", "typowy", {"dystans": 10, "temperatura": 20, "opady": "brak", "bagaz": "brak",
                      "pora_dnia": "dzien", "spieszy_sie": "nie"}, "rower"),
    ("T3", "granica", {"dystans": 1.5, "temperatura": 5, "opady": "brak", "bagaz": "brak",
                       "pora_dnia": "dzien", "spieszy_sie": "nie"}, "pieszo"),
    ("T4", "brak wyniku", {"dystans": 4, "temperatura": 15, "opady": None, "bagaz": "maly",
                           "pora_dnia": "dzien", "spieszy_sie": "tak"}, None),
    ("T5", "konflikt", {"dystans": 4, "temperatura": 3, "opady": "deszcz", "bagaz": "brak",
                        "pora_dnia": "noc", "spieszy_sie": "nie"}, "taksowka"),
]


def w_przod(baza, dane):
    fakty = {k: v for k, v in dane.items() if v is not None}
    fakty, slad = wnioskuj_w_przod(baza, fakty)
    return fakty.get(baza["cel"]), slad


def wstecz(baza, dane):
    zapytane = []

    def zapytaj(atrybut, regula):
        zapytane.append(atrybut)
        return dane.get(atrybut)

    slad = []
    wynik = wnioskuj_wstecz(baza, baza["cel"], {}, zapytaj, slad)
    return wynik, slad, zapytane


def zmien_kolejnosc(baza, id_reguly):
    """Kopia bazy z regułą przeniesioną na koniec listy (test strategii konfliktów)."""
    nowa = copy.deepcopy(baza)
    r = next(x for x in nowa["reguly"] if x["id"] == id_reguly)
    nowa["reguly"].remove(r)
    nowa["reguly"].append(r)
    return nowa


def uruchom():
    wiersze, zaliczone = [], 0
    for nr, rodzaj, dane, oczekiwany in PRZYPADKI:
        wp, slad_p = w_przod(BAZA, dane)
        ws, slad_w, _ = wstecz(BAZA, dane)
        ok = wp == oczekiwany and ws == oczekiwany
        zaliczone += ok
        wiersze.append((nr, rodzaj, dane, oczekiwany, wp, ws, slad_p, slad_w, ok))
    return wiersze, zaliczone


def test_kolejnosc_regul():
    dane = PRZYPADKI[4][2]
    po_zmianie = zmien_kolejnosc(BAZA, "R12")
    return w_przod(BAZA, dane)[0], w_przod(po_zmianie, dane)[0]


if __name__ == "__main__":
    wiersze, zaliczone = uruchom()
    for nr, rodzaj, dane, oczek, wp, ws, sp, sw, ok in wiersze:
        print(f"{nr} [{rodzaj}] oczekiwany={oczek} | w przód={wp} ({' -> '.join(sp) or '—'}) "
              f"| wstecz={ws} ({' -> '.join(sw) or '—'}) | {'OK' if ok else 'BŁĄD'}")
    przed, po = test_kolejnosc_regul()
    print(f"Kolejność reguł (T5): R12 na początku -> {przed}; R12 na końcu -> {po}")
    kolejnosc_ok = przed == "taksowka" and po == "komunikacja_miejska"
    print(f"Zaliczone przypadki: {zaliczone + kolejnosc_ok}/{len(wiersze) + 1}")
    sys.exit(0 if zaliczone == len(wiersze) and kolejnosc_ok else 1)
