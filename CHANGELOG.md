---
## 1.1.0 - 2026-06-16


### Bug fixes


- Correctly deref deployment_data double pointer for null check
 ([0bc6757](https://github.com/mendersoftware/mender-mcu/commit/0bc67571782d19778edf7fe0d8158f29b8dbcf11))  by @danielb-IDG




  Null check as it stood will always succeed, as assert at top of function already checks it.
- Avoid crash when IPv4 info is unavailable in Zephyr inventory
 ([10cc0ec](https://github.com/mendersoftware/mender-mcu/commit/10cc0ec620da0a6d650af935a05c19c5848160e0))  by @Dexter9532






### Features


- Add support for chunked artifact download
 ([751274c](https://github.com/mendersoftware/mender-mcu/commit/751274c148dabfa5d751560ceca98bef0fa72370))  by @Dexter9532




  Using HTTP requests with `Range` headers artifact
  downloads can be chunked reducing requirements
  on network buffers and potentially performing better
  in bad network deployments.




### Build


- Warnings based on device tier defaults
([MEN-9288](https://northerntech.atlassian.net/browse/MEN-9288)) ([2e00a42](https://github.com/mendersoftware/mender-mcu/commit/2e00a420f5be3fdccbd3037cbf6d4c1bd4dcfaa1))  by @rewanrashid-boop






  Added defaults based on device tier in Zephyr Kconfig and extended
  functionality in Cmake source file to trigger warnings.






## 1.0.0 - 2026-04-17

* The first stable release


## 0.9.0 - 2025-04-11

* Preview of Mender MCU

---
