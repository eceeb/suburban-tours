#!/usr/bin/env python3
"""Einmal-Import der vorgefertigten Touren → data/tours/<id>.json + data/tours/index.json.

Quellen (bleiben lokal unter data/, nicht im Git):
  - GPX-Exporte aus Roadtrippers (eigenes Konto, privater Gebrauch): data/tours/<id>.gpx
  - Touren, die bei Roadtrippers nur Ortslisten ohne Route sind: data/tours/_ungeroutet.json
    → Stopps werden per Nominatim gefunden, sinnvoll sortiert und per OSRM selbst geroutet.

Aufruf:  python3 tools/import_tours.py
"""
import json, math, os, re, time, urllib.parse, urllib.request
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR = os.path.join(ROOT, "data", "tours")
UA = {"User-Agent": "suburban-tours/1.0 (personal project)"}

# Katalog: Titel/Beschreibung für die Auswahl-Ansicht. "gpx" = Datei, sonst Ortsliste aus _ungeroutet.json.
CATALOG = [
    ("arizona-ghost-towns", "Geisterstädte im Süden Arizonas", "Alte Minenstädte rund um Tombstone", "https://maps.roadtrippers.com/trips/26967597", True),
    ("tennessee-whiskey-trail", "Tennessee Whiskey Trail", "Brennereien im Hinterland von Nashville", "https://maps.roadtrippers.com/trips/34941967", True),
    ("free-range-art-highway", "Free Range Art Highway", "US-95 durch Nevada: Geisterstadt Rhyolite, Wüstenkunst, Car Forest", "https://maps.roadtrippers.com/trips/20231376", True),
    ("badlands-secrets", "Badlands-Geheimtipps", "Präriehunde, Wounded Knee, 1880 Homestead", "https://maps.roadtrippers.com/trips/16754711", False),
    ("nevada-interesting-towns", "Nevadas schräge Kleinstädte", "Geisterstädte, heiße Quellen, Clown-Motel, UFO-Highway", "https://maps.roadtrippers.com/trips/32620808", True),
    ("yellowstone-secrets", "Yellowstones Geheimtipps", "Geisterstadt Bannack statt Old-Faithful-Trubel", "https://maps.roadtrippers.com/trips/10498525", True),
    ("texas-ghost-towns", "Geisterstädte in Texas", "Glenrio, Lobo, Terlingua (Big Bend), Catarina, Luckenbach", "https://maps.roadtrippers.com/trips/27757459", False),
    ("nomadland", "Nomadland-Roadtrip", "Drehorte: Empire NV, Quartzsite, Badlands", "https://maps.roadtrippers.com/trips/32395552", True),
    ("dumb-and-dumber", "Dumb and Dumber: Drehorte", "Von Providence quer durchs Land bis Colorado", "https://maps.roadtrippers.com/trips/14702721", True),
]


def hav(a, b):
    R = 6371000
    la1, la2 = math.radians(a[0]), math.radians(b[0])
    dl, dp = math.radians(b[1] - a[1]), la2 - la1
    return 2 * R * math.asin(math.sqrt(math.sin(dp / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin(dl / 2) ** 2))


def thin(path, min_m=15):
    """Punkte, die näher als min_m am letzten liegen, weglassen (Datei kleiner, Strecke gleich)."""
    out = [path[0]]
    for p in path[1:]:
        if hav(out[-1], p) >= min_m:
            out.append(p)
    if out[-1] != path[-1]:
        out.append(path[-1])
    return out


def from_gpx(fn):
    r = ET.parse(fn).getroot()
    ns = {"g": r.tag.split("}")[0].strip("{")}
    stops = [{"name": (w.findtext("g:name", default="", namespaces=ns) or "").strip(),
              "lat": float(w.get("lat")), "lng": float(w.get("lon"))} for w in r.findall("g:wpt", ns)]
    path = [(float(p.get("lat")), float(p.get("lon"))) for p in r.findall(".//g:rtept", ns)]
    return stops, path


def geocode(q):
    """Nominatim mit Rückfällen: 'Name, Staat' → Name ohne Zusätze ('Ghost Town', 'Historic District')
    → 'Ort, Staat' → Name allein. Straßen und ganze Staaten/Countys werden NIE als Treffer akzeptiert."""
    parts = [p.strip() for p in q.split(",")]
    name, state = parts[0], parts[-1]
    clean = re.sub(r"\b(Historic District|Ghost Town)\b", "", name).strip()
    cands = [q, f"{name}, {state}", f"{clean}, {state}"] + ([f"{parts[-2]}, {state}"] if len(parts) > 2 else []) + [clean]
    for cand in dict.fromkeys(cands):  # Reihenfolge behalten, Duplikate raus
        url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode({"format": "jsonv2", "limit": 5, "countrycodes": "us", "q": cand})
        time.sleep(1.2)  # Nominatim: max ~1 Anfrage/Sekunde
        for r in json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20)):
            # keine Straßen (z.B. „Glenrio Road" in Albuquerque) und keine ganzen Staaten/Countys
            if r.get("category") != "highway" and r.get("addresstype") not in ("state", "country", "county"):
                return float(r["lat"]), float(r["lon"]), cand
    raise RuntimeError("nicht gefunden: " + q)


def nearest_order(stops):
    """Reihenfolge per 'nächster Nachbar' ab dem ersten Stopp (Ortslisten haben keine Reihenfolge)."""
    rest, out = stops[1:], [stops[0]]
    while rest:
        nxt = min(rest, key=lambda s: hav((out[-1]["lat"], out[-1]["lng"]), (s["lat"], s["lng"])))
        out.append(nxt)
        rest.remove(nxt)
    return out


def osrm(stops):
    pts = ";".join(f"{s['lng']},{s['lat']}" for s in stops)
    for base in ["https://routing.openstreetmap.de/routed-car/route/v1/driving/", "https://router.project-osrm.org/route/v1/driving/"]:
        try:
            j = json.load(urllib.request.urlopen(urllib.request.Request(base + pts + "?overview=full&geometries=geojson", headers=UA), timeout=60))
            return [(lat, lng) for lng, lat in j["routes"][0]["geometry"]["coordinates"]]
        except Exception as e:
            print("   OSRM-Fehler", base.split("/")[2], e)
    raise RuntimeError("OSRM nicht erreichbar")


def main():
    lists = json.load(open(os.path.join(DIR, "_ungeroutet.json"), encoding="utf-8"))
    index = []
    for tid, title, desc, source, is_gpx in CATALOG:
        if is_gpx:
            stops, path = from_gpx(os.path.join(DIR, tid + ".gpx"))
            routed_by = "roadtrippers"
        else:
            print(f"{tid}: Stopps suchen …")
            stops = []
            for q in lists[tid]["stopps"]:
                lat, lng, used = geocode(q)
                print(f"   {q}  →  {lat:.4f},{lng:.4f}" + ("" if used == q else f"  (gefunden als '{used}')"))
                stops.append({"name": q.split(",")[0].strip(), "lat": lat, "lng": lng})
            stops = nearest_order(stops)
            path = osrm(stops)
            routed_by = "osrm"
        path = thin(path)
        km = sum(hav(path[i - 1], path[i]) for i in range(1, len(path))) / 1000
        tour = {"id": tid, "title": title, "desc": desc, "source": source, "routedBy": routed_by,
                "km": round(km), "stops": [{**s, "lat": round(s["lat"], 5), "lng": round(s["lng"], 5)} for s in stops],
                "path": [[round(a, 5), round(b, 5)] for a, b in path]}
        with open(os.path.join(DIR, tid + ".json"), "w", encoding="utf-8") as f:
            json.dump(tour, f, ensure_ascii=False, separators=(",", ":"))
        index.append({k: tour[k] for k in ("id", "title", "desc", "source", "routedBy", "km")} | {"stopCount": len(stops)})
        print(f"{tid:26s} {len(stops):3d} Stopps | {round(km):5d} km | {len(path):6d} Punkte")
    index.sort(key=lambda t: t["km"])
    with open(os.path.join(DIR, "index.json"), "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=1)
    print("index.json:", len(index), "Touren")


if __name__ == "__main__":
    main()
