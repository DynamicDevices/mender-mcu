# Branch: `feature/zephyr-ram-stage-on-main`

**Live shared pin** for Dynamic Devices Zephyr 4.4 products (see `DD_PIN` /
`PIN-POLICY.md`).

**Base:** upstream `mendersoftware/mender-mcu` `main` @ `55fa6a1`  
**Client pin SHA:** `64c10fa` — RAM staging on `zephyr-image`  
**Tag:** `dd-pin-64c10fa`

Predecessor: `feature/zephyr-4.4-mbedtls4` @ `1dbc35b` (superseded).

## Smoke matrix (2026-08-04 pin `64c10fa`)

| # | Product | Check | Result |
|---|---------|-------|--------|
| 1 | F1 | native_sim Mender | **OK** (earlier; TLS+check-in) |
| 2 | F1 | FRDM Hosted OTA | **OK** — `f1-fleet-ramstage-64c10fa` finished/success |
| 3 | Room-display | `build-native-sim.sh` | **OK** — host build green @ `64c10fa` |
| 4 | E-ink | `test-mender-native-sim.sh` | **OK** — activated + `No deployment available` |
| 5 | E-ink RT118x HW | — | skipped (no EVK claim) |
