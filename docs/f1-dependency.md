# Application storage and update-state hooks

These optional hooks let an application share the existing Zephyr NVS owner
and inspect persisted update metadata without exposing stored JSON or URLs.
They do not authorize an update or replace the client's normal authentication.

## Storage

The Zephyr NVS backend exports the following application-specific ABI:

```c
int mender_storage_f1_init(void);
int mender_storage_f1_read(unsigned slot, void *data, size_t capacity);
int mender_storage_f1_write(unsigned slot, const void *data, size_t length);
```

Slots 0–5 map to NVS IDs `0xf100`–`0xf105`, separate from Mender's IDs.
Initialization mounts the same NVS handle under an owner mutex, without loading
the client's deployment or artifact caches. The minimum sector size is 2464
bytes. Applications must initialize successfully before reading or writing.

Reads accept capacities 1–2448 and return the NVS record length or a negative
errno. Applications must reject lengths inconsistent with their record format.
Writes accept lengths 16–2448, returning zero on a complete or unchanged write,
or a negative errno. A short positive write becomes `-EIO`. Invalid arguments
return `-EINVAL`; access before mounting returns `-ENODEV`.
The application owns schema, CRC, journaling and readback verification; these
hooks do not make a multi-record transaction atomic. Hardware power-loss and
flash-endurance qualification remain separate.

## Update metadata and pinning

`mender_client_get_persisted_update_summary(id, state)` reads a fresh stored
deployment object and returns only a validated 36-character hexadecimal UUID
and integral state in the supported range. The ID buffer must hold 37 bytes.
`MENDER_NOT_FOUND` means no stored deployment; malformed or unreadable state is
an error, not idle. On failure with valid pointers the outputs are empty/-1.
The function frees its temporary deployment object and does not write storage.

Call `mender_client_pin_deployment(id)` before client activation, with a
lowercase UUID. Setup must be serialized by the caller; it is not a concurrent
runtime reconfiguration API. A second pin is rejected, including the same UUID.
The pin is immutable for the rest of the boot and checked for both new and
resumed deployments. It is consumed before terminal-record deletion, including
failed deletion, preventing reuse in that boot. An unpinned client retains its
normal deployment-selection behavior.

State persistence errors now stop update callbacks for the rest of the boot.
This latch is intentional: a later successful probe must not silently resume
callbacks after the relationship between durable state and performed actions
became uncertain. Recovery requires a subsequent boot with state validation;
automatic in-boot retry/clearing is not part of this API contract.
Loop detection is different from a persistence error: its counter-reset signal
transitions to FAILURE, persists that state and enters normal failure handling.
If persisting FAILURE fails, the same fail-closed latch stops callbacks.
Terminal-record deletion failures are retried on a subsequent scheduled run;
new deployment work remains blocked while cleanup is pending. A resumed END
record is cleaned up instead of replaying update callbacks.

Deployment-data CRC appending uses a separate allocation so ownership of the
caller's JSON buffer remains unchanged. CRC-check failure frees the temporary
read buffer rather than returning it as valid state.

## Offline regression tests

Run `python3 tests/f1-dependency/test_hooks.py` with an installed C compiler
supporting AddressSanitizer and UndefinedBehaviorSanitizer (override with `CC`).
The fixtures compile actual hook function bodies from the candidate sources,
using synthetic NVS, allocation and metadata failures. They cover slot/size
bounds, key mapping, mount/read/write failures, short/unchanged writes, UUID and
numeric-state validation, pin consumption, persistence-error latching, cleanup
retry state and CRC buffer ownership. No cloud, credentials or board is used.

These focused fixtures stub platform and JSON accessors: they do not compile
the complete client state machine, validate real flash readback, or establish
Zephyr integration, reboot recovery or physical-device acceptance. Full target
builds and independent exact-candidate review remain required downstream.

(Briar helped draft this)
