# Suburban Tours

Play a route as a "film": enter a start and destination, and the app drives a
camera along the route using real imagery. Three self-contained variants are
included, no build step — just static HTML.

## Variants

| File | What it does | Needs |
| --- | --- | --- |
| `streetview.html` | **Main app.** A guided Street View tour that hops panorama-to-panorama along the route, with smooth dolly-zoom, a pause/free-look mode, a live speed control, a Navi mode (stop at every junction, capped jumps on highways), a mini map, and a local usage estimate. | Google Maps API key |
| `index.html` | Cinematic flythrough using Google Photorealistic 3D Tiles (CesiumJS). Smooth like a video, but oblique/aerial rather than ground level. | Google Maps API key |
| `demo.html` | Keyless 3D demo (MapLibre + OpenFreeMap + OSRM). Grey 3D buildings instead of photos, but no API key and free forever. | nothing |

Routing and geocoding use the keyless **OSRM** and **Nominatim** services, so
the Google key is only needed for the imagery itself.

## Running

Any static file server works:

```bash
python3 -m http.server 8777
```

Then open <http://localhost:8777/streetview.html>.

## Google API key

`streetview.html` and `index.html` need a Google Maps Platform API key. The key
is entered in the app at runtime and stored only in your browser's
localStorage — it is never part of the code.

Enable these APIs on the key's project:

- Maps JavaScript API
- Street View Static API

Restrict the key to your host (e.g. HTTP referrer `http://localhost:8777/*`) so
it can't be reused elsewhere.

## Notes

- Street View is a sequence of discrete panoramas (~10 m apart), so a tour is a
  fast slideshow, not true video. The dolly-zoom softens the cuts.
- The usage counter (top-right) is a local estimate for this browser only — the
  real quota lives in the Google Cloud Console.
