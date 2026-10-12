"""Junta los planteles bajados de Wikipedia con los puntajes y escribe planteles.js para el juego.

Uso:  python3 -I herramientas/armar_planteles.py
Entradas:  datos/wikipedia/<slug>.json   (lo genera bajar_planteles.py)
           datos/puntajes.json           ({"Nombre": 84} o {"Nombre": [84, "LI"]}; el segundo valor es el puesto fino)
Salida:    planteles.js
Los futbolistas sin puntaje cargado reciben el puntaje base del equipo y se listan al final para completarlos.
"""
import datetime
import json
import pathlib
import re

RAIZ = pathlib.Path(__file__).resolve().parent.parent
ORIGEN = RAIZ / "datos" / "wikipedia"
PUNTAJES = RAIZ / "datos" / "puntajes.json"
SALIDA = RAIZ / "planteles.js"

ORDEN = ["boca", "river", "racing", "central", "sanlorenzo", "independiente", "barcelona", "napoles",
         "realmadrid", "psg", "benfica", "ajax", "bayern", "mancity", "liverpool", "tottenham", "dortmund",
         "manutd", "alnassr", "argentina", "brasil", "portugal", "francia",
         "inglaterra", "noruega", "eeuu", "alemania", "italia"]
SELECCIONES = {"argentina", "brasil", "portugal", "francia", "inglaterra", "noruega", "eeuu", "alemania", "italia"}

# Puntaje para quien todavía no tiene uno cargado (juveniles o recién llegados)
BASE = {"boca": 66, "river": 66, "racing": 65, "central": 64, "sanlorenzo": 63, "independiente": 64,
        "barcelona": 72, "napoles": 72, "realmadrid": 73, "psg": 73, "benfica": 70, "ajax": 68, "alnassr": 68,
        "bayern": 73, "mancity": 73, "liverpool": 73, "tottenham": 70, "dortmund": 70, "manutd": 71,
        "argentina": 76, "brasil": 76, "portugal": 77, "francia": 78, "inglaterra": 77, "noruega": 72,
        "eeuu": 71, "alemania": 75, "italia": 75}
PUESTOS = {"ARQ", "DFC", "LI", "LD", "MCD", "MC", "MCO", "MI", "MD", "EI", "ED", "DC"}


def limpiar_nombre(n):
    n = re.sub(r"\s*\((?:[^)]*foot[^)]*|[^)]*soccer[^)]*|[^)]*born[^)]*)\)", "", n)
    # Wikipedia pega marcas como RET (retirado de la selección), INJ (lesionado) o WD (se bajó)
    n = re.sub(r"(?<=[a-zà-ÿ.])(RET|INJ|WD|SUS|PRE|COV|ALT)+$", "", n)
    return n.strip()


def main():
    puntajes = json.loads(PUNTAJES.read_text(encoding="utf-8")) if PUNTAJES.exists() else {}
    equipos, faltan, problemas = {}, {}, []
    fechas = []
    for slug in ORDEN:
        archivo = ORIGEN / f"{slug}.json"
        if not archivo.exists():
            problemas.append(f"{slug}: falta {archivo.name}")
            continue
        datos = json.loads(archivo.read_text(encoding="utf-8"))
        if "error" in datos:
            problemas.append(f"{slug}: {datos['error']}")
            continue
        vistos, lista = set(), []
        for j in datos["jugadores"]:
            nombre = limpiar_nombre(j["n"])
            if nombre in vistos or j["p"] == "?":
                continue
            vistos.add(nombre)
            valor = puntajes.get(nombre)
            puesto = ""
            if isinstance(valor, list):
                valor, puesto = valor[0], valor[1]
            if valor is None:
                faltan.setdefault(slug, []).append(nombre)
                valor = BASE[slug]
            if puesto and puesto not in PUESTOS:
                problemas.append(f"{slug}: puesto raro '{puesto}' para {nombre}")
                puesto = ""
            item = {"n": nombre, "p": j["p"], "num": j["num"], "r": int(valor)}
            if puesto:
                item["d"] = puesto
            if slug in SELECCIONES and j.get("c"):
                item["c"] = limpiar_nombre(j["c"])
            lista.append(item)
        cuenta = {g: sum(1 for x in lista if x["p"] == g) for g in ("POR", "DEF", "MED", "DEL")}
        if cuenta["POR"] < 2 or cuenta["DEF"] < 5 or cuenta["MED"] < 5 or cuenta["DEL"] < 3:
            problemas.append(f"{slug}: plantel corto {cuenta}")
        fecha = datetime.date.fromisoformat(datos["revision"][:10])
        fechas.append(fecha)
        equipos[slug] = {
            "fecha": f"Wikipedia, {fecha.strftime('%d/%m/%Y')}",
            "url": datos["url"],
            "jugadores": lista,
        }

    actualizado = max(fechas).strftime("%d/%m/%Y") if fechas else ""
    cuerpo = json.dumps({"actualizado": actualizado, "equipos": equipos}, ensure_ascii=False, separators=(",", ":"))
    cuerpo = cuerpo.replace('},{"n"', '},\n{"n"').replace('"jugadores":[{', '"jugadores":[\n{')
    SALIDA.write_text(
        "// Generado por herramientas/armar_planteles.py — no editar a mano.\n"
        "// Planteles: sección \"Current squad\" de Wikipedia. Puntajes: datos/puntajes.json (estimados, escala 1-99).\n"
        f"window.PLANTELES = {cuerpo};\n",
        encoding="utf-8",
    )
    total = sum(len(e["jugadores"]) for e in equipos.values())
    print(f"planteles.js: {len(equipos)} equipos, {total} futbolistas, actualizado {actualizado}")
    sin = sum(len(v) for v in faltan.values())
    print(f"sin puntaje cargado (usan el base del equipo): {sin}")
    for slug, nombres in faltan.items():
        print(f"  {slug}: {', '.join(nombres)}")
    for p in problemas:
        print("AVISO", p)


if __name__ == "__main__":
    main()
