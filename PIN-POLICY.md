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

What this pin includes (relative to upstream `mendersoftware/mender-mcu` `main`):

- Zephyr **4.4** / Mbed TLS **4.x** / TF-PSA-Crypto TLS + storage guards  
- `zephyr-image` **RAM staging** before secondary-slot write (FlexSPI XIP-safe on i.MX RT)

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
6. After a pin bump: each consumer runs its usual Hosted smoke (at least check-in /
   `No deployment available` on lab hardware or native_sim as appropriate).

## How to bump

```bash
# 1) Land + push on this repo (feature/zephyr-4.4-mbedtls4 or successor branch)
NEW=$(git rev-parse HEAD)   # full SHA

# 2) In EACH consumer west.yml:
#    revision: <NEW full SHA>

# 3) west update mender-mcu && rebuild/smoke per product
```

## Out of scope for this repo

- Hosted Mender org / tenant tokens (Bitwarden `cursor-agent-lab`)  
- Per-product MCUboot key ceremonies  
- ELE HyperRAM / OCRAM NVM fixes (`DynamicDevices/psa_crypto_driver`)  
