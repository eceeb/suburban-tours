# Suburban Tours

Play a route as a "film": enter a start and destination, and the app drives a
Google Street View camera along the route, hopping from panorama to panorama.
One HTML file plus a tiny stdlib-only Python server (`server.py`) that also
stores favourites and photos — no build step, no dependencies.

## Features

- Guided Street View tour along a real driving route.
- Smooth dolly-zoom between panoramas (zoom scales with the gap, so the next
  frame lines up) plus damped heading so the view stays forward, not wobbly.
- **Pause + free look & walk:** pause to drag around and mouse-wheel zoom, and
  move panorama-to-panorama by clicking the road or with the ↑/↓ arrow keys — no
  Google navigation-arrow overlay. Resume continues from where you were looking.
- **Live speed / dwell** control.
- **Navi mode:** stop at every junction, with a capped max jump (e.g. 10 km on
  a highway between exits).
- Route options: **avoid highways / tolls / ferries** (via Google Directions;
  falls back to the normal route if that API isn't enabled).
- **Scenic byways:** detects when the route runs on a named scenic byway (from
  OpenStreetMap route relations) and turns the control bar teal (distinct from
  the green border bar) for the whole stretch, with the byway's name.
- **Big rivers:** stops right on the bridge when the route crosses a major river,
  turns the bar green with the river's name (e.g. "🌊 North Platte River") and
  holds 3× as long. Which rivers count as "big" comes from the Natural Earth
  dataset (offline, reliable); since that is heavily generalised (up to ~10 km
  off), the exact bridge is found in OpenStreetMap vector tiles (OpenFreeMap,
  keyless CDN) by matching the river name within ±12 km. No exact match → no stop,
  rather than a wrong one.
- Control bar always shows **current US state · distance travelled · elevation**
  (elevation via the keyless open-meteo API).
- **Route via scenic byways (optional):** if a scenic byway runs close to the
  normal route, it's woven in as via-waypoints so the drive follows it — capped
  at +40 % extra distance, otherwise dropped. Uses OSM (queried up front, so the
  start is slower) and only detours to byways that are genuinely nearby.
- Live **OSM status** indicator (top-right): shows whether the OpenStreetMap
  lookups are loading, succeeding, or failing, with a success/fail counter.
- **Photos:** in pause mode, 📷 grabs the current view as a real JPEG at full
  window resolution (rendered off-screen from the live Street View viewer, not a
  screenshot and not the 640 px Static API), tagged with Google's capture date
  and the location. Photos are shown in a **gallery** grouped into country →
  region folders, each with a download button and click-to-open-full-size.
  Falls back to the 640×640 Static API if the off-screen capture fails.
- **Central storage:** favourites and photos live on disk under `data/`
  (`favorites.json`, `photos/<id>.jpg` + `photos/index.json`), served by
  `server.py` — so every browser on the machine sees the same data. `data/` is
  git-ignored.
- **Pre-made tours (🗺 Touren):** a picker with curated tours (stops, length,
  estimated Street View requests for the current mode — orange if it exceeds
  what's left this month). A tour plays its fixed route exactly: avoid-highway
  and scenic routing are greyed out. Named stops get a green bar ("📍 Gleeson")
  and a 2× hold; a stop without Street View coverage is announced on the next
  available image. Tours are imported once with `tools/import_tours.py` into
  `data/tours/` (local only, not in git) — e.g. from your own Roadtrippers GPX
  exports; place lists without a route are geocoded and routed via OSRM.
- **Open a favourite in the viewer:** the 👁 button on a saved favourite opens
  that exact spot in the Street View viewer (paused, free-look) so you can look
  around and take photos there without driving a whole tour.
- **Local radio (📻):** streams a local station for the state/region you are
  currently in (keyless, via the Radio-Browser community DB) and switches
  automatically when you cross into a new state. **Click** opens a popup with
  all stations for the current state (turns the radio on if it was off) — pick
  one, or use ⏭ next / ⏹ off; unreachable stations get struck through.
  **Right-click** turns it off.
- Mini map (bottom-left) tracking the current position.
- Local usage estimate (top-right) as a rough free-quota gauge, with a warning
  banner (and optional auto-stop) when the estimate crosses the free tier. This
  is only an estimate — a hard quota cap in the Google Cloud Console is the only
  real guarantee of $0.

Routing and geocoding use the keyless **OSRM** and **Nominatim** services, so
Google is only needed for the imagery (and, optionally, the avoid-route options).
For resilience, routing races two public OSRM servers (whichever answers first
wins) and both routes and geocodes are cached locally, so the same trip doesn't
re-hit the flaky public services. Overpass (POIs/junctions/byways) likewise
races several mirrors, prefers a non-empty answer, and caches results.

## Running

```bash
python3 server.py
```

Then open <http://localhost:8777/streetview.html>. (A plain static server like
`python3 -m http.server` still runs the app, but favourites fall back to the
browser's localStorage and photos can't be saved.)

## Google API key

The key is entered in the app at runtime and stored only in your browser's
localStorage — it is never part of the code.

Enable these APIs on the key's project:

- Maps JavaScript API
- Street View Static API
- Directions API — only if you want the avoid-highways/tolls/ferries options

Restrict the key to your host (e.g. HTTP referrer `http://localhost:8777/*`) so
it can't be reused elsewhere.

## Notes

- Street View is a sequence of discrete panoramas (~10 m apart), so a tour is a
  fast slideshow, not true video. The dolly-zoom softens the cuts, and Google's
  own transition handles blending between linked panoramas.
- The usage counter is a local estimate for this browser only — the real quota
  lives in the Google Cloud Console.
