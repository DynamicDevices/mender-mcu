# Coordinated F1 LED-settings dependency repair

Briar introduced the mismatch by advancing the Flexi consumer to a client
commit that the shared canonical pin had not yet adopted. Reverting the other
consumers removed premature rollout, but it did not complete the dependency
integration. This proposal coordinates the whole pin change; it does not weaken
the checker to make an inconsistent candidate green.

## Exact client change

Current live canonical client: a0c6e2d456c7c5b8aeed17245a024a2dc302788d.
Proposed immutable client: c121219d704fc159f37c9da1fc946aba0379454a.
The two storage functions admit application slots 6/7 for alternating LED
settings. The shared NVS owner, mutex, keys for existing slots and length bounds
are unchanged. Other client source is identical. Native_sim, sanitizer fixtures,
custom-controller hardware and other-product hardware are separate proof classes.

The already tested replacement controller 0.0.82 and sensors 0.0.14 are not
rebuilt, flashed or replaced by these metadata changes. Their images remain
rig-bound development artifacts. No RAM-staging, transport, tenant, bootloader,
calibration or credential changes are proposed for the other products.

## Coordinated candidates

| Repository | Manifest / metadata | Proposed pin |
| --- | --- | --- |
| DynamicDevices/mender-mcu | DD_PIN and PIN-POLICY.md | c121219 (full SHA above) |
| active-esl/zephyr-mcx-f1-flexi | app/west.yml; existing PR243 | c121219 |
| DynamicDevices/zephyr-rt1186-f1 | f1-controller/west.yml | c121219 |
| DynamicDevices/zephyr-rt1170-room-display | room-display/west.yml | c121219 |
| DynamicDevices/zephyr-rt1186-eink | mender-mcu-integration/west.yml | c121219 |

The three non-Flexi consumer PRs must contain only the full-SHA manifest change
from current main. The earlier withdrawn PRs remain historical failures; do not
reuse their apparent status as acceptance of these new candidates.

## Validation and integration order

1. Review the complete coordinated diff, verify unchanged source outside the
   slot-limit change, and run the existing five F1 sanitizer fixture groups.
2. Check all four manifests against the proposed DD_PIN locally. Keep a negative
   case proving those manifests still fail against the old canonical pin.
   Candidate consistency is not live canonical CI success.
3. Run the applicable existing consumer native_sim/smoke matrix and independent
   reviews. If a canonical pre-build gate blocks these until integration, record
   that condition; do not redirect or disable the live check. Record untested
   product/hardware paths explicitly instead of inferring them from Flexi proof.
4. Alex reviews and merges the shared-client promotion. Only after independently
   reading back the live canonical DD_PIN may the consumer canonical checks be
   rerun and reported as passing. Alex retains every consumer merge as well.
5. Qualify the existing private F1 kit through its required CI/review gates. Keep
   its release draft if any gate remains blocked. Preserve the failed soak,
   updater cleanup timing defect and pending Windows hardware acceptance.

Source publication, CI state, exact results and PR links are recorded in the
owning F1 release checkpoint and the PRs. No automatic cross-product deployment,
hardware operation, merge or shipment approval is part of this repair.

Assisted-by: Briar.
