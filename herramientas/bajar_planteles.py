"""Baja el plantel actual de cada equipo desde Wikipedia (en inglés) y lo guarda en datos/wikipedia/<slug>.json.

Uso:  python3 -I herramientas/bajar_planteles.py [slug ...]
Sin argumentos baja los 28 equipos. Lee solo la sección "Current squad" (o "First-team squad"),
así quedan afuera los préstamos, las reservas y las convocatorias anteriores.
"""
import json
import pathlib
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

RAIZ = pathlib.Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "datos" / "wikipedia"
API = "https://en.wikipedia.org/w/api.php"
AGENTE = "RuletaBernie/1.0 (proyecto personal; juego de futbol)"

PAGINAS = {
    "boca": "Boca Juniors",
    "river": "Club Atlético River Plate",
    "racing": "Racing Club de Avellaneda",
    "central": "Rosario Central",
    "sanlorenzo": "San Lorenzo de Almagro",
    "independiente": "Club Atlético Independiente",
    "barcelona": "FC Barcelona",
    "napoles": "SSC Napoli",
    "realmadrid": "Real Madrid CF",
    "psg": "Paris Saint-Germain FC",
    "benfica": "S.L. Benfica",
    "ajax": "AFC Ajax",
    "bayern": "FC Bayern Munich",
    "mancity": "Manchester City F.C.",
    "liverpool": "Liverpool F.C.",
    "tottenham": "Tottenham Hotspur F.C.",
    "dortmund": "Borussia Dortmund",
    "manutd": "Manchester United F.C.",
    "alnassr": "Al-Nassr FC",
    "argentina": "Argentina national football team",
    "brasil": "Brazil national football team",
    "portugal": "Portugal national football team",
    "francia": "France national football team",
    "inglaterra": "England national football team",
    "noruega": "Norway national football team",
    "eeuu": "United States men's national soccer team",
    "alemania": "Germany national football team",
    "italia": "Italy national football team",
}

SECCION = re.compile(r"^(current squad|first[- ]team squad|current first[- ]team squad|squad)$", re.I)
PLANTILLAS = {"fs player", "football squad player", "nat fs g player", "nat fs player"}
POSICION = {"GK": "POR", "DF": "DEF", "MF": "MED", "FW": "DEL"}


def api(**params):
    params["format"] = "json"
    params["redirects"] = 1
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": AGENTE})
    for intento in range(6):
        time.sleep(2.5)  # Wikipedia corta si se le pide muy rápido
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code != 429 or intento == 5:
                raise
            espera = int(e.headers.get("Retry-After") or 0) or 15 * (intento + 1)
            print(f"  Wikipedia pide esperar {espera}s…", flush=True)
            time.sleep(espera)


def plantillas(texto):
    """Devuelve el contenido de cada {{...}} de primer nivel, respetando llaves anidadas."""
    out, i, n = [], 0, len(texto)
    while i < n:
        if texto.startswith("{{", i):
            prof, j = 0, i
            while j < n:
                if texto.startswith("{{", j):
                    prof += 1
                    j += 2
                elif texto.startswith("}}", j):
                    prof -= 1
                    j += 2
                    if prof == 0:
                        break
                else:
                    j += 1
            out.append(texto[i + 2:j - 2])
            i = j
        else:
            i += 1
    return out


def partir(cuerpo):
    """Separa los parámetros de una plantilla por '|' de primer nivel."""
    partes, prof, actual, i = [], 0, "", 0
    while i < len(cuerpo):
        dos = cuerpo[i:i + 2]
        if dos in ("{{", "[["):
            prof += 1
            actual += dos
            i += 2
            continue
        if dos in ("}}", "]]"):
            prof -= 1
            actual += dos
            i += 2
            continue
        if cuerpo[i] == "|" and prof == 0:
            partes.append(actual)
            actual = ""
        else:
            actual += cuerpo[i]
        i += 1
    partes.append(actual)
    return partes


def limpiar(valor):
    v = re.sub(r"<!--.*?-->", "", valor, flags=re.S)
    v = re.sub(r"<ref[^>]*/>|<ref[^>]*>.*?</ref>", "", v, flags=re.S)
    m = re.search(r"\{\{\s*sortname\s*\|([^|}]*)\|([^|}]*)(?:\|([^|}]*))?(?:\|[^}]*)?\}\}", v, re.I)
    if m:
        nombre = f"{m.group(1).strip()} {m.group(2).strip()}".strip()
        if m.group(3) and m.group(3).strip() and "=" not in m.group(3):
            pass
        return nombre
    v = re.sub(r"\[\[([^|\]]*)\|([^\]]*)\]\]", r"\2", v)
    v = re.sub(r"\[\[([^\]]*)\]\]", r"\1", v)
    v = re.sub(r"\{\{[^}]*\}\}", "", v)
    v = re.sub(r"<[^>]+>", "", v)
    v = v.replace("'''", "").replace("''", "")
    return re.sub(r"\s+", " ", v).strip()


def bajar(slug, titulo):
    secciones = api(action="parse", page=titulo, prop="sections")["parse"]["sections"]
    sec = next((s for s in secciones if SECCION.match(s["line"].strip())), None)
    if not sec:  # algunas páginas (Al Nassr) tienen el plantel directo en "Players"
        sec = next((s for s in secciones if s["line"].strip().lower() == "players"), None)
    if not sec:
        return {"slug": slug, "pagina": titulo, "error": "no encontré la sección del plantel",
                "secciones": [s["line"] for s in secciones]}
    texto = api(action="parse", page=titulo, section=sec["index"], prop="wikitext")["parse"]["wikitext"]["*"]
    # La API devuelve también las subsecciones (préstamos, reservas): cortamos en el primer subtítulo.
    # Algunas páginas separan los préstamos con un pseudo-título (";Out on loan" o "'''Out on loan'''").
    lineas = texto.split("\n")
    for k, linea in enumerate(lineas[1:], start=1):
        if re.match(r"^=+[^=].*=+\s*$", linea) or re.match(r"^\s*(;|''').*\b(loan|reserves?|academy|youth|under-\d+)\b", linea, re.I):
            texto = "\n".join(lineas[:k])
            break
    rev = api(action="query", titles=titulo, prop="revisions", rvprop="timestamp")
    pagina = next(iter(rev["query"]["pages"].values()))
    jugadores = []
    for cuerpo in plantillas(texto):
        partes = partir(cuerpo)
        if partes[0].strip().lower() not in PLANTILLAS:
            continue
        p = {}
        for parte in partes[1:]:
            if "=" in parte:
                k, v = parte.split("=", 1)
                p[k.strip().lower()] = v
        nombre = limpiar(p.get("name", ""))
        if not nombre:
            continue
        num = re.sub(r"\D", "", limpiar(p.get("no", "")))
        jugadores.append({
            "n": nombre,
            "p": POSICION.get(limpiar(p.get("pos", "")).upper(), "?"),
            "num": int(num) if num else None,
            "c": limpiar(p.get("club", "")) or None,
        })
    return {
        "slug": slug,
        "pagina": titulo,
        "seccion": sec["line"],
        "revision": pagina["revisions"][0]["timestamp"],
        "url": "https://en.wikipedia.org/wiki/" + urllib.parse.quote(titulo.replace(" ", "_")),
        "jugadores": jugadores,
    }


def main():
    SALIDA.mkdir(parents=True, exist_ok=True)
    pedidos = sys.argv[1:] or list(PAGINAS)
    for slug in pedidos:
        try:
            datos = bajar(slug, PAGINAS[slug])
        except Exception as e:  # noqa: BLE001
            datos = {"slug": slug, "pagina": PAGINAS[slug], "error": repr(e)}
        (SALIDA / f"{slug}.json").write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8")
        if "error" in datos:
            print(f"{slug:14} ERROR {datos['error']}")
        else:
            cuenta = {g: sum(1 for j in datos["jugadores"] if j["p"] == g) for g in ("POR", "DEF", "MED", "DEL", "?")}
            print(f"{slug:14} {len(datos['jugadores']):3} jugadores  {cuenta}  rev {datos['revision'][:10]}  [{datos['seccion']}]")
        time.sleep(0.4)


if __name__ == "__main__":
    main()
