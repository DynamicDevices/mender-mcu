# Branch: `feature/zephyr-ram-stage-on-main`

**Purpose:** carry FlexSPI-safe **RAM staging** for `zephyr-image` on top of
current `mendersoftware/mender-mcu` `main` (Zephyr 4.4 / Mbed TLS 4.x already
upstream via #247).

**Base:** `55fa6a1` (upstream `main` as of 2026-08-04 eval)  
**Delta:** `src/platform/update_modules/zephyr/image/update-module.c` only —
Josef Holzmayr `sdram-stage-download` idea (realloc-free whole-image stage +
direct-to-flash fallback), rebased.

**Not yet:** consumer `DD_PIN` / west bumps — products still pin
`1dbc35b` on `feature/zephyr-4.4-mbedtls4` until smoke + Alex OK.

**Next:** native_sim / FRDM OTA smoke → `bump-consumer-pins.sh` → retag `dd-pin-*`.

Eval notes: `~/tmp/mender-mcu-josef-note/PIN-BUMP-EVAL-2026-08-04.md`
