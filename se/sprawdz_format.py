"""Kontrola formatu bazy wiedzy w JSON oraz wymagań zadania Z2."""
import json
import re
import sys
from pathlib import Path

OPERATORY_LICZBA = {">", ">=", "<", "<="}
OPERATORY_WSZYSTKIE = OPERATORY_LICZBA | {"==", "!="}
NAZWA = re.compile(r"^[a-z0-9_]+$")


def sprawdz(sciezka):
    bledy, uwagi = [], []
    try:
        with open(sciezka, encoding="utf-8") as f:
            tekst = f.read()
        baza = json.loads(tekst)
    except json.JSONDecodeError as e:
        print(f"[BŁĄD] Składnia JSON, linia {e.lineno}, kolumna {e.colno}: {e.msg}")
        return None, 1, 0
    except (OSError, UnicodeDecodeError) as e:
        print(f"[BŁĄD] Nie można odczytać pliku (UTF-8): {e}")
        return None, 1, 0

    for klucz in ("nazwa", "cel", "atrybuty", "reguly"):
        if klucz not in baza:
            bledy.append(f"brak klucza '{klucz}'")
    if bledy:
        for b in bledy:
            print(f"[BŁĄD] {b}")
        return None, len(bledy), 0

    atr = baza["atrybuty"]
    for nazwa, opis in atr.items():
        if not NAZWA.match(nazwa):
            bledy.append(f"atrybut '{nazwa}': nazwa tylko z małych liter ASCII, cyfr i _")
        typ = opis.get("typ")
        if typ == "liczba":
            wymagane = ("pytanie", "zakres")
        elif typ == "wybor":
            wymagane = ("pytanie", "wartosci")
        elif typ == "wniosek":
            wymagane = ("wartosci",)
            if "pytanie" in opis:
                uwagi.append(f"atrybut '{nazwa}': wniosek nie powinien mieć pola 'pytanie'")
        else:
            bledy.append(f"atrybut '{nazwa}': nieznany typ '{typ}'")
            continue
        for pole in wymagane:
            if pole not in opis:
                bledy.append(f"atrybut '{nazwa}': brak pola '{pole}'")
        if typ == "liczba" and "zakres" in opis:
            z = opis["zakres"]
            if not (isinstance(z, list) and len(z) == 2 and all(isinstance(x, (int, float)) for x in z) and z[0] < z[1]):
                bledy.append(f"atrybut '{nazwa}': 'zakres' musi być listą [min, max]")
        if typ in ("wybor", "wniosek") and "wartosci" in opis:
            if not (isinstance(opis["wartosci"], list) and opis["wartosci"]):
                bledy.append(f"atrybut '{nazwa}': 'wartosci' musi być niepustą listą")

    cel = baza["cel"]
    if cel not in atr:
        bledy.append(f"cel '{cel}' nie jest zadeklarowany w atrybutach")
    elif atr[cel].get("typ") != "wniosek":
        bledy.append(f"cel '{cel}' musi mieć typ 'wniosek'")

    ids = set()
    for i, r in enumerate(baza["reguly"], 1):
        rid = r.get("id", f"#{i}")
        if "id" not in r:
            bledy.append(f"reguła nr {i}: brak 'id'")
        elif rid in ids:
            bledy.append(f"reguła {rid}: powtórzone id")
        ids.add(rid)
        jesli = r.get("jesli")
        if not isinstance(jesli, list) or not jesli:
            bledy.append(f"reguła {rid}: 'jesli' musi być niepustą listą warunków")
            jesli = []
        elif not all(isinstance(w, list) for w in jesli):
            bledy.append(f"reguła {rid}: pojedynczy warunek też musi być w liście: "
                         f"\"jesli\": [[\"atrybut\", \"op\", wartość]]")
            jesli = []
        for w in jesli:
            if len(w) != 3:
                bledy.append(f"reguła {rid}: warunek {w} musi mieć 3 elementy")
                continue
            a, op, wart = w
            if a not in atr:
                bledy.append(f"reguła {rid}: niezadeklarowany atrybut '{a}'")
                continue
            if op not in OPERATORY_WSZYSTKIE:
                bledy.append(f"reguła {rid}: nieznany operator '{op}'")
                continue
            typ = atr[a].get("typ")
            if typ == "liczba":
                if isinstance(wart, bool) or not isinstance(wart, (int, float)):
                    bledy.append(f"reguła {rid}: liczba '{a}' porównywana z tekstem {wart!r} (bez cudzysłowu)")
            else:
                if op in OPERATORY_LICZBA:
                    bledy.append(f"reguła {rid}: operator '{op}' tylko dla liczb ('{a}')")
                elif wart not in atr[a].get("wartosci", []):
                    bledy.append(f"reguła {rid}: wartość {wart!r} nie występuje w deklaracji '{a}'")
        to = r.get("to")
        if not (isinstance(to, list) and len(to) == 2):
            bledy.append(f"reguła {rid}: 'to' musi być parą [atrybut, wartość]")
        else:
            a, wart = to
            if a not in atr:
                bledy.append(f"reguła {rid}: niezadeklarowany atrybut '{a}' w 'to'")
            elif atr[a].get("typ") != "wniosek":
                bledy.append(f"reguła {rid}: atrybut '{a}' w 'to' musi mieć typ 'wniosek'")
            elif wart not in atr[a].get("wartosci", []):
                bledy.append(f"reguła {rid}: wartość {wart!r} nie występuje w deklaracji '{a}'")
        if "metafora" not in r:
            uwagi.append(f"reguła {rid}: brak 'metafora'")
        if isinstance(to, list) and to and to[0] == cel and "coto" not in r:
            uwagi.append(f"reguła {rid}: brak 'coto' w regule z decyzją końcową")

    for b in bledy:
        print(f"[BŁĄD] {b}")
    for u in uwagi:
        print(f"[UWAGA] {u}")
    print(f"Format — błędy: {len(bledy)}, uwagi: {len(uwagi)}.")
    return baza, len(bledy), len(uwagi)


def poziomy(baza):
    """Poziom atrybutu: wejście = 0, wniosek = 1 + max poziom atrybutów z warunków."""
    atr = baza["atrybuty"]
    cache = {}

    def poziom(a, stos=()):
        if a in cache:
            return cache[a]
        if atr[a]["typ"] != "wniosek" or a in stos:
            return 0
        najlepszy = 1
        for r in baza["reguly"]:
            if r["to"][0] == a:
                for w in r["jesli"]:
                    najlepszy = max(najlepszy, 1 + poziom(w[0], stos + (a,)))
        cache[a] = najlepszy
        return najlepszy

    return {a: poziom(a) for a in atr}


def wymagania_z2(baza):
    reguly = baza["reguly"]
    pz = poziomy(baza)
    cel = baza["cel"]
    print("Wymagania Z2:")
    tak = lambda x: "[TAK]" if x else "[NIE]"
    print(f"{tak(len(reguly) >= 20)} co najmniej 20 reguł (jest {len(reguly)})")
    print(f"{tak(pz[cel] >= 2)} łańcuch co najmniej 3 poziomów atrybutów (cel na poziomie {pz[cel] + 1})")
    print(f"{tak(all('metafora' in r for r in reguly))} pole 'metafora' w każdej regule")
    print(f"{tak(all('coto' in r for r in reguly if r['to'][0] == cel))} pole 'coto' w każdej regule z decyzją")


if __name__ == "__main__":
    sciezka = sys.argv[1] if len(sys.argv) > 1 else Path(__file__).parent.parent / "wiedza" / "moja_dziedzina.json"
    baza, nb, nu = sprawdz(sciezka)
    if baza is not None and nb == 0:
        wymagania_z2(baza)
    sys.exit(1 if nb else 0)
