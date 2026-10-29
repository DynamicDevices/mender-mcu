---
## Unreleased

* Zephyr `zephyr-image` update module: optional RAM staging before secondary-slot
  write (XIP-safe on FlexSPI), with `CONFIG_MENDER_ZEPHYR_IMAGE_RAM_STAGE` and
  `CONFIG_MENDER_ZEPHYR_IMAGE_RAM_STAGE_MAX_BYTES`, `mender_malloc` staging
  buffer, direct-to-flash fallback, and unit tests for the staging helpers.
* ESP-IDF: fix `MENDER_STORAGE_PARTITION_LABEL` compile definition mismatch in
  `component.cmake`; grow log formatting beyond a fixed 256-byte stack buffer.

## 1.0.0 - 2026-04-17

* The first stable release


## 0.9.0 - 2025-04-11

* Preview of Mender MCU

---
