"""Autotest silnika na małej bazie wbudowanej w plik (5 przypadków)."""
import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from silnik import wnioskuj_w_przod, wnioskuj_wstecz, regula_spelniona

BAZA = {
    "nazwa": "Mini doradca", "cel": "kawa",
    "atrybuty": {
        "temperatura": {"typ": "liczba", "pytanie": "t?", "zakres": [-30, 45]},
        "kofeina_ok": {"typ": "wybor", "pytanie": "k?", "wartosci": ["tak", "nie"]},
        "rodzaj": {"typ": "wniosek", "wartosci": ["zimna", "goraca"]},
        "kawa": {"typ": "wniosek", "wartosci": ["mrozona", "espresso", "bezkofeinowa"]}},
    "reguly": [
        {"id": "R1", "jesli": [["temperatura", ">", 22]], "to": ["rodzaj", "zimna"]},
        {"id": "R2", "jesli": [["temperatura", "<=", 22]], "to": ["rodzaj", "goraca"]},
        {"id": "R3", "jesli": [["kofeina_ok", "==", "nie"]], "to": ["kawa", "bezkofeinowa"]},
        {"id": "R4", "jesli": [["rodzaj", "==", "zimna"], ["kofeina_ok", "==", "tak"]], "to": ["kawa", "mrozona"]},
        {"id": "R5", "jesli": [["rodzaj", "==", "goraca"], ["kofeina_ok", "==", "tak"]], "to": ["kawa", "espresso"]}]}


def odpowiedzi(dane, zapytane):
    def zapytaj(atrybut, regula):
        zapytane.append(atrybut)
        return dane.get(atrybut)
    return zapytaj


def wstecz(dane):
    zapytane, slad = [], []
    wynik = wnioskuj_wstecz(BAZA, "kawa", {}, odpowiedzi(dane, zapytane), slad)
    return wynik, slad, zapytane


def t1():
    """TODO 1: wszystkie warunki reguły muszą być spełnione"""
    r = BAZA["reguly"][3]
    return (regula_spelniona(r, {"rodzaj": "zimna", "kofeina_ok": "tak"})
            and not regula_spelniona(r, {"rodzaj": "zimna", "kofeina_ok": "nie"})
            and not regula_spelniona(r, {"rodzaj": "zimna"}))


def t2():
    """TODO 2: łańcuch w przód i ślad reguł"""
    fakty, slad = wnioskuj_w_przod(BAZA, {"temperatura": 18, "kofeina_ok": "tak"})
    return fakty["kawa"] == "espresso" and slad == ["R2", "R5"]


def t3():
    """TODO 3-4: wstecz pyta tylko o potrzebne dane, bez powtórzeń"""
    wynik, slad, zapytane = wstecz({"temperatura": 25, "kofeina_ok": "nie"})
    return wynik == "bezkofeinowa" and zapytane == ["kofeina_ok"] and slad == ["R3"]


def t4():
    """oba tryby dają ten sam wynik"""
    dane = {"temperatura": 25, "kofeina_ok": "tak"}
    fakty, _ = wnioskuj_w_przod(BAZA, dane)
    wynik, _, zapytane = wstecz(dane)
    return fakty["kawa"] == wynik == "mrozona" and len(zapytane) == len(set(zapytane))


def t5():
    """brak danych: nieznany fakt nie odpala reguły"""
    fakty, _ = wnioskuj_w_przod(BAZA, {"temperatura": 25})
    wynik, _, _ = wstecz({"temperatura": 25})
    return "kawa" not in fakty and wynik is None


if __name__ == "__main__":
    testy = [t1, t2, t3, t4, t5]
    zaliczone = 0
    for t in testy:
        ok = t()
        zaliczone += ok
        print(f"{'OK  ' if ok else 'BŁĄD'} {t.__name__}: {t.__doc__}")
    print(f"Zaliczone przypadki: {zaliczone}/{len(testy)}")
    sys.exit(0 if zaliczone == len(testy) else 1)
