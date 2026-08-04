# Common `mender-mcu` pin policy (Dynamic Devices)

**Status:** In force (2026-08-04)  
**Owner:** firmware lanes using Hosted Mender MCU on Zephyr 4.4  

This fork (`DynamicDevices/mender-mcu`) is the **shared Mender MCU client** for
Active ESL / DD Zephyr products. Product firmware repos must **not** carry
divergent local copies of the client.

## Canonical pin

| Field | Value |
|-------|--------|
| Remote | `https://github.com/DynamicDevices/mender-mcu` |
| Branch (development) | `feature/zephyr-4.4-mbedtls4` |
| **West `revision`** | **`1dbc35b572e0e2837a95c12a0bff92fc8cc39e49`** (full 40-char SHA) |
| Short | `1dbc35b` — *do not* use abbreviated SHAs in west manifests (CI `west update -o=--depth=1` cannot resolve them) |
| **Machine pin** | [`DD_PIN`](./DD_PIN) (one SHA, one line) — CI SoT |
| **Immutable tag** | `dd-pin-1dbc35b` → same SHA (retag on each client bump) |

What this pin includes (relative to upstream `mendersoftware/mender-mcu` `main`):

- Zephyr **4.4** / Mbed TLS **4.x** / TF-PSA-Crypto TLS + storage guards  
- `zephyr-image` **RAM staging** before secondary-slot write (FlexSPI XIP-safe on i.MX RT)

Docs-only commits on `feature/zephyr-4.4-mbedtls4` after the pin SHA do **not** require
consumer west bumps — west tracks the **client** commit in `DD_PIN`, not branch tip.

## Consumer product repos (must match)

| Product | Manifest | Board focus |
|---------|----------|-------------|
| F1 gateway | [`zephyr-rt1186-f1`](https://github.com/DynamicDevices/zephyr-rt1186-f1) `f1-controller/west.yml` | FRDM-IMXRT1186 |
| Room display | [`zephyr-rt1170-room-display`](https://github.com/DynamicDevices/zephyr-rt1170-room-display) `room-display/west.yml` | MIMXRT1170-EVK |
| E-ink / RT118x integration | [`zephyr-rt1170-eink`](https://github.com/DynamicDevices/zephyr-rt1170-eink) `mender-mcu-integration/west.yml` | RT1180-EVK / FRDM-1186 reference |

Agent skill (ops): `~/.cursor/skills/mender-hosted/` — Hosted tenant/PAT, deploy, accept.

## Rules

1. **One pin for all consumers.** Bumping `mender-mcu` means updating **every**
   consumer `west.yml` in the same change set (or coordinated PRs the same day).
2. **Full SHA only** in west manifests.
3. **No product-local forks** of `mender-mcu` source. If you need a client fix,
   land it here first, then bump pins.
4. **Product-local stays product-local:** board overlays, `device_type`, partition
   maps, MCUboot signing keys, ELE opaque TLS / `psa_crypto_driver`, artifact
   names, Hosted device groups.
5. **Proof class:** native_sim ≠ EVK flash ≠ custom PCB — pin is shared; proof is not.
6. After a pin bump: run the **smoke matrix** below before calling the bump done.
7. Consumer CI must run `scripts/check-consumer-pin.sh` (or equivalent) against
   `DD_PIN` so pin drift fails the build.

## How to bump

```bash
# 1) Land + push client commits on feature/zephyr-4.4-mbedtls4 (or successor)
NEW=$(git rev-parse HEAD)   # full SHA of the *client* commit to pin

# 2) Update DD_PIN + PIN-POLICY + all three consumer west.yml (dry-run then apply)
./scripts/bump-consumer-pins.sh "$NEW"          # preview
./scripts/bump-consumer-pins.sh "$NEW" --apply

# 3) Annotate + push immutable tag
git tag -a "dd-pin-${NEW:0:7}" "$NEW" -m "Shared Zephyr 4.4 mender-mcu pin"
git push origin "dd-pin-${NEW:0:7}"

# 4) Commit/push this repo + each consumer; west update; smoke matrix
```

Local verify one consumer before push:

```bash
./scripts/check-consumer-pin.sh /data_drive/dd/zephyr-rt1186-f1/f1-controller/west.yml
```

## Smoke matrix (required after a pin bump)

Proof class must be named honestly. Check boxes in the bump PR / notes.

| # | Product | Check | Pass criteria |
|---|---------|-------|----------------|
| 1 | F1 | `./scripts/smoke-native-sim-mender.sh` (or native_sim Hosted path) | builds; Hosted check-in or documented noop path |
| 2 | F1 | FRDM Hosted (when board present) | `No deployment available` or intentional OTA finish on **fleet-signed** image |
| 3 | Room-display | `./scripts/build-native-sim.sh` (+ Mender smoke if wired) | host build green; note if OTA not yet on EVK |
| 4 | E-ink | `./scripts/test-mender-native-sim.sh` / Phase 0b | Hosted noop path green |
| 5 | E-ink | RT118x EVK/FRDM (when present) | Ethernet + Hosted check-in; OTA only if intended |

Do **not** claim EVK/FRDM proof from native_sim alone.

## Out of scope for this repo

- Hosted Mender org / tenant tokens (Bitwarden `cursor-agent-lab`)  
- Per-product MCUboot key ceremonies  
- ELE HyperRAM / OCRAM NVM fixes (`DynamicDevices/psa_crypto_driver`)  
