# Suburban Tours

Play a route as a "film": enter a start and destination, and the app drives a
Google Street View camera along the route, hopping from panorama to panorama.
Single self-contained file, no build step — just static HTML.

## Features

- Guided Street View tour along a real driving route.
- Smooth dolly-zoom between panoramas (zoom scales with the gap, so the next
  frame lines up) plus damped heading so the view stays forward, not wobbly.
- **Pause + free look:** pause to drag around and mouse-wheel zoom; resume
  continues from where you were looking.
- **Live speed / dwell** control.
- **Navi mode:** stop at every junction, with a capped max jump (e.g. 10 km on
  a highway between exits).
- Route options: **avoid highways / tolls / ferries** (via Google Directions;
  falls back to the normal route if that API isn't enabled).
- **Scenic byways:** detects when the route runs on a named scenic byway (from
  OpenStreetMap route relations) and turns the control bar teal (distinct from
  the green border bar) for the whole stretch, with the byway's name.
- Control bar always shows **current US state · distance travelled · elevation**
  (elevation via the keyless open-meteo API).
- **Route via scenic byways (optional):** if a scenic byway runs close to the
  normal route, it's woven in as via-waypoints so the drive follows it — capped
  at +40 % extra distance, otherwise dropped. Uses OSM (queried up front, so the
  start is slower) and only detours to byways that are genuinely nearby.
- Live **OSM status** indicator (top-right): shows whether the OpenStreetMap
  lookups are loading, succeeding, or failing, with a success/fail counter.
- **Photos:** in pause mode, 📷 grabs the current view as a real JPEG from the
  Street View Static API (not a screenshot), tagged with Google's capture date
  and the location. Photos are stored locally in the browser's IndexedDB and
  shown in a **gallery** view, each with a download button. (A static web page
  can't write into the project folder itself, so "local" means IndexedDB +
  manual download.)
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

Any static file server works:

```bash
python3 -m http.server 8777
```

Then open <http://localhost:8777/streetview.html>.

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
