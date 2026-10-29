# Dependency and compatibility report — 23 October 2026

Core requirements installed successfully in a fresh Python 3.12 environment. `pip check` reports no broken requirements; resolved versions are in `reports/improvement-20261023/pip-freeze.txt`. No new production dependency was introduced. Frontend `npm ci` and Vite production build pass with the existing lockfile. Python direct requirements are pinned, but the release does not supply a fully hashed transitive Python lock.

| Check | Result / boundary |
| --- | --- |
| Python core tests | 121 passed on this Linux runtime; one Starlette/AnyIO deprecation warning remains |
| Frontend build | Passed; npm reports an environment `http-proxy` configuration warning |
| Database format | Frozen SQLite snapshots pass integrity; no migration introduced |
| Historical files | SHA-256 preservation report covers experiment/snapshot/prepared data files |
| Native Windows | Prior acceptance retained; this follow-up was not executed on Windows |
| Browser | Previous release 13-page Linux acceptance retained; no fresh full browser pass in this backend/input-audit follow-up |
| Ollama / model runtime | No new inference or model download; runtime binaries and weights excluded from ZIP |
| RAM / VRAM | Static audit needs no model or GPU; 32 GB / 8 GB target inference profile has not been newly benchmarked |
| Vulnerability database scan | NOT_RUN in this phase; successful install/pip check is not a security scan |
| Dependency/source licence review | NOT_RUN as a complete release audit |
| Public deployment | Not accepted; retain loopback local deployment boundary |

Extract into a separate empty folder and follow the existing Windows setup/start scripts. Keep the current Windows installation and live database intact. The packaged databases are preserved historical snapshots, not an automatic replacement for newer local work. Roll back by using the retained prior ZIP and its matching dependency environment; no schema rollback is required. Git read changes disable helper execution and use the platform's null device, but require fresh native Windows regression/acceptance testing before a Windows-specific claim.

## Detailed audit v2 follow-up

The latest code has 131 passing tests and a fresh 13-page Linux Chromium acceptance pass. Vite is updated to 6.4.5 with a matching lockfile; production build passes. npm audit reports one high-severity affected dependency before the update and zero vulnerabilities afterwards. This updates the earlier frontend-scan status only. Python vulnerability/license review and fresh native Windows testing remain outstanding. No production Python dependencies or database schema were added.
