#!/usr/bin/env python3
"""Genera agenda-nautica.ics (español) y agenda-nautica-en.ics (inglés) desde agenda/eventos.json.
Cada evento puede tener un bloque "en" con titulo, detalle y lugar en inglés; si falta, se usa el español.
Uso: python3 agenda/generar_ics.py"""
import json, datetime as dt, pathlib
raiz = pathlib.Path(__file__).resolve().parent.parent
data = json.loads((raiz / "agenda" / "eventos.json").read_text(encoding="utf-8"))
def esc(s): return s.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")
def fold(line):
    b = line.encode("utf-8"); out = []
    while len(b) > 75:
        cut = 75 if not out else 74
        while (b[cut] & 0xC0) == 0x80: cut -= 1
        out.append(b[:cut]); b = b[cut:]
    out.append(b)
    return "\r\n ".join(x.decode("utf-8") for x in out)
d = lambda s: dt.date.fromisoformat(s)
stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
TIPO_EN = {"Campeonato": "Championship", "Regata de club": "Club regatta", "Aniversario": "Anniversary",
           "Escuela de verano": "Summer school", "Evento": "Event", "Curso": "Course", "Clínica": "Clinic"}

def calendario(lang):
    en = lang == "en"
    L = ["BEGIN:VCALENDAR", "VERSION:2.0",
         f"PRODID:-//Ignacio Porrini//Agenda Nautica Uruguay//{'EN' if en else 'ES'}",
         "CALSCALE:GREGORIAN", "METHOD:PUBLISH",
         "X-WR-CALNAME:" + ("Uruguay Sailing Calendar" if en else "Agenda Náutica Uruguay"),
         "X-WR-TIMEZONE:America/Montevideo",
         "X-WR-CALDESC:" + ("Club regattas\\, summer schools\\, anniversaries and championships of Uruguayan sailing. Every event with its source."
                            if en else "Regatas de club\\, escuelas de verano\\, aniversarios y campeonatos de la náutica uruguaya. Cada evento con su fuente."),
         "REFRESH-INTERVAL;VALUE=DURATION:P1D", "X-PUBLISHED-TTL:P1D"]
    for e in data["eventos"]:
        t = e.get("en", {}) if en else {}
        titulo, detalle, lugar = t.get("titulo", e["titulo"]), t.get("detalle", e["detalle"]), t.get("lugar", e["lugar"])
        tipo = TIPO_EN.get(e["tipo"], e["tipo"]) if en else e["tipo"]
        # Español: UID con el dominio viejo a propósito, evita duplicados al migrar suscriptores
        uid = f"{e['id']}-en@navegauy.github.io" if en else f"{e['id']}@ignacioporrini.github.io"
        L += ["BEGIN:VEVENT", f"UID:{uid}", f"DTSTAMP:{stamp}"]
        if e.get("hora"):
            h, m = map(int, e["hora"].split(":"))
            ini = dt.datetime.combine(d(e["inicio"]), dt.time(h, m)) + dt.timedelta(hours=3)  # UY = UTC-3
            fin = ini + dt.timedelta(hours=e.get("duracionHoras", 2))
            L += [f"DTSTART:{ini:%Y%m%dT%H%M%SZ}", f"DTEND:{fin:%Y%m%dT%H%M%SZ}"]
        else:
            fin = d(e.get("fin", e["inicio"])) + dt.timedelta(days=1)
            L += [f"DTSTART;VALUE=DATE:{d(e['inicio']):%Y%m%d}", f"DTEND;VALUE=DATE:{fin:%Y%m%d}"]
        if en:
            desc = f"{detalle}\nOrganizer: {e['organiza']}\nSource: {e['fuente']['nombre']} – {e['fuente']['url']}\nCalendar: https://navegauy.github.io/en/docencia-de-vela.html#agenda"
        else:
            desc = f"{detalle}\nOrganiza: {e['organiza']}\nFuente: {e['fuente']['nombre']} – {e['fuente']['url']}\nAgenda: https://navegauy.github.io/docencia-de-vela.html#agenda"
        L += [f"SUMMARY:{esc(titulo)}", f"LOCATION:{esc(lugar)}", f"DESCRIPTION:{esc(desc)}",
              f"URL:{e['fuente']['url']}", f"CATEGORIES:{esc(tipo)}", "END:VEVENT"]
    L.append("END:VCALENDAR")
    return "\r\n".join(fold(x) for x in L) + "\r\n"

(raiz / "agenda-nautica.ics").write_text(calendario("es"), encoding="utf-8", newline="")
(raiz / "agenda-nautica-en.ics").write_text(calendario("en"), encoding="utf-8", newline="")
print(len(data["eventos"]), "eventos (es y en)")
