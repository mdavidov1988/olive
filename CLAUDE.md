# Olive — Baby Tracker PWA

## What This Is
Pure client-side baby tracker. No backend, no database, no accounts. All data lives in the user's browser localStorage. Hosted as static files on GitHub Pages.

## Live URL
https://mdavidov1988.github.io/olive/

## Architecture
- Single `index.html` file (~1000 lines) containing all HTML, CSS, and JavaScript
- Tailwind CSS via CDN, Inter font via Google Fonts
- Service worker (`sw.js`) for offline caching (cache-first strategy)
- `manifest.json` for PWA installability
- GitHub Pages auto-deploy via `.github/workflows/pages.yml`

**Critical:** All paths in manifest.json and sw.js MUST be relative (`./`) not root (`/`) because GitHub Pages serves at `/olive/` subdirectory.

## Data Model (localStorage)
- `olive_baby_name` — string
- `olive_feedings` — JSON array: `{ id, dt, milk_type, amount_oz }`
- `olive_poops` — JSON array: `{ id, dt, poop_type, notes }`
- `olive_sleeps` — JSON array: `{ id, start, end, duration_hrs, notes }`
- `olive_weights` — JSON array: `{ id, dt, pounds, ounces, total_lbs, kg, input_mode }`
- `olive_sleep_start` — ISO string (active sleep timer)
- `olive_weight_mode` — string: 'lbs_oz' | 'lbs' | 'kg'

## Key Code Patterns
- **Data layer:** `load(key)` / `save(key, data)` / `addEntry(key, entry)` / `deleteEntryById(key, id)` / `updateEntryById(key, id, updates)`
- **Boot:** `boot()` → checks for baby name → shows setup or app screen
- **Tabs:** 4 main tabs (feed/poop/sleep/weight) in `allTabs` array. Settings is separate, toggled by gear icon.
- **Weight:** 3 input modes (lbs+oz, lbs, kg). All modes cross-compute and store both lbs and kg. `_normalize_weight` logic in `submitWeight()`.
- **Sleep timer:** Start time persisted in `olive_sleep_start` localStorage key so it survives page closes.
- **CSV export:** Sectioned format with `[feedings]`, `[poops]`, `[sleeps]`, `[weights]` headers. Import parses this back.
- **Entry lists:** `renderList(tab)` builds HTML. Each entry has colored left border (category-specific).

## Color Palette (Sage/Olive Green)
```
brand-50: #F5F7F0   brand-100: #E8EDDF   brand-200: #D2DBBE
brand-300: #B5C799   brand-400: #94AD74   brand-500: #6B8C42
brand-600: #5A7A3B   brand-700: #476432   brand-800: #384F2A
```
Stat card accent colors: green (feeds), amber (oz), rose (poops), blue (sleep), violet (weight).

## Design Decisions
- **No backend by design:** User explicitly does not want to store anyone's personal data. Each phone is independent.
- **Tailwind CDN:** Avoids build tooling. Service worker caches it for offline use.
- **Single HTML file:** Keeps deployment trivial (just static files).
- **CSV over JSON for export:** User preference for a more universally readable format.

## iOS Notes
- `apple-touch-icon` link tag for home screen icon
- `apple-mobile-web-app-capable` for standalone mode
- Service worker must cache CDN assets (Tailwind, fonts) or offline mode breaks
- Real PNG icons required (iOS ignores data: URI icons in manifest)
