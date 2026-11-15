# Production offline check — manual browser verification

Automated build/precache checks do not prove that a browser successfully installed the service worker. No browser offline pass is claimed until the result below is filled in.

1. From dashboard/, export PATH="$HOME/.local/node/bin:$PATH", then run npm run sync:release, npm run build and npm run preview.
2. Open the preview URL printed by Vite (normally http://127.0.0.1:4173). Confirm the real simulated-release label and seed 1000; default crew C2/day41.
3. While online, open DevTools → Application → Service Workers. Wait for sw.js to be activated and running; reload once so the page is controlled. Under Cache Storage confirm the current spacehealth-* cache contains index.html, every hashed asset, the manifest/icon and all public/data JSON files.
4. Select DevTools → Network → Offline, or turn off Wi-Fi. Keep the preview process running; network requests must be served by the worker cache.
5. Reload the page. Check Today; open Physiological change Detail and its action card; verify no raw template braces; record a local action. Open Crew and Log. Open Replay + Validation, scrub to day72 and verify radiation Act and the holdout summary. Open a direct query URL while offline and reload. Check day122/C4 missing data.
6. Confirm missing data still says No reliable data, and errors never fall back to a nominal health status. Test a production build update online and confirm old spacehealth-* caches are removed after activation; unrelated caches should remain.
7. Restore network access. Stop the owned preview process when finished.

Service-worker registration is skipped in development/test. The first installation needs network access and enough cache storage. Browser private-mode/storage restrictions can prevent offline installation. Ground messages remain local queued records; no transport or background sync is added.

## Result record

- Browser + version:
- OS/device and viewport:
- Build/cache version (from dist/precache-manifest.js):
- Initial online install and controlled reload:
- Offline reload/Today/Detail/Replay/Validation results:
- Console/network failures:
- Tester/date:
- Verdict: NOT YET VERIFIED
