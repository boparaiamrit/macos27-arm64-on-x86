# Legal Disclaimer, Research Scope & EULA Compliance Notice

## 1. Independent Educational & Interoperability Research Project
This repository (`boparaiamrit/macos27-arm64-on-x86`) is an **independent academic, educational, and systems-interoperability research publication** created by **Amritpal Singh ([@boparaiamrit](https://github.com/boparaiamrit))**.

Its sole purpose is to document systems-engineering research into:
- Cross-ISA dynamic binary translation (`AArch64 → x86_64` JIT compilation inside QEMU TCG).
- Paravirtualized graphics translation (`Metal` intermediate representations to Khronos `SPIR-V` / `Vulkan 1.3`).
- Read-only file system data structures (APFS B-trees) and Network Block Device (`NBD`) caching architectures.
- Open-source hardware emulation models in QEMU (`hw/vmapple`).

**This project is NOT a commercial product, turnkey operating system distribution, or consumer virtualization package.**

---

## 2. Zero Proprietary Assets & No DRM Circumvention
- **Open-Source Code Only:** This repository contains strictly original source code (`.c`, `.h`, `.rs`, `.py`, `.sh`), unified patches (`.diff`, `.patch`) against open-source projects, and written engineering analysis.
- **No Apple Software Distributed:** This repository does **not** contain, host, redistribute, or link to unauthorized copies of macOS, `.ipsw` restore bundles, Apple firmware/ROMs (`AVPBooter`, `iBoot`), kernelcaches, kexts, proprietary Metal shaders, cryptographic keys, or device `ECID` identifiers.
- **No Copyright-Protection Circumvention:** Nothing in this repository circumvents or attempts to circumvent Apple FairPlay, App Store DRM, content-protection schemes, or hardware cryptographic roots of trust.

---

## 3. Apple macOS Software License Agreement (EULA) Notice
While this repository contains only open-source research code and does not distribute macOS itself, **downloading, installing, or running Apple's macOS is governed by Apple's End-User License Agreement (EULA)**.

- Apple's macOS Software License Agreement permits installing and running virtualized instances of macOS **solely on Apple-branded hardware** (for example, an Intel-based `x86_64` Mac or an Apple Silicon Mac running Linux/QEMU for kernel, compiler, or emulator research).
- **Only run macOS workloads on official Apple-branded hardware**, or strictly within applicable statutory exemptions for lawful security and interoperability research in your jurisdiction. Any other use of Apple's proprietary operating system software is not permitted by Apple's EULA.
- The author does **not** condone, encourage, or support piracy, copyright infringement, or violations of any End-User License Agreement.

---

## 4. "AS IS" Warranty & Limitation of Liability
This software and research documentation are provided **"AS IS"**, without warranty of any kind, express or implied, including but not limited to the warranties of merchantability, fitness for a particular purpose, and noninfringement.

By viewing, compiling, or using any code or documentation in this repository, **you acknowledge that you are solely responsible for how you use it** and for complying with all applicable laws, licenses, patents, trademarks, and End-User License Agreements (EULAs). In no event shall the author be liable for any claim, damages, legal consequences, data loss, or other liability arising from or in connection with this repository.

---

## 5. Trademarks & Non-Affiliation
- **Apple**, **macOS**, **Apple Silicon**, **iBoot**, **XNU**, **Darwin**, **Metal**, and **APFS** are trademarks of **Apple Inc.**, registered in the U.S. and other countries.
- **QEMU** is a trademark of **Fabrice Bellard**.
- **Vulkan** and **SPIR-V** are trademarks or registered trademarks of **The Khronos Group Inc.**
- **Linux** is the registered trademark of **Linus Torvalds**.
- **Windows** and **DirectX / Direct3D** are registered trademarks of **Microsoft Corporation**.

All product names, brands, and trademarks mentioned in this repository are used strictly in a nominative, descriptive manner for technical identification and remain the property of their respective holders. **This project is completely independent and is NOT affiliated with, sponsored by, authorized by, or endorsed by Apple Inc. or any other trademark holder.**

---

## 6. Upstream Open-Source License Compliance & Good-Faith Contact
- **QEMU Integration Files & Patches** (`src/fastjit-qemu/fastjit-a64.c`, `src/fastjit-qemu/fastjit-a64.h`, `src/qemu-apple-vm-patches/`): Distributed under **GNU General Public License v2.0 or later (`GPL-2.0-or-later`)**, respecting QEMU's upstream licensing.
- **`reims-vgpu` Patches** (`src/reims-vgpu-patches/`): Distributed under the upstream license of [`steelbrain/reims-vgpu`](https://github.com/steelbrain/reims-vgpu).
- **Standalone Tools, Benchmarks & Documentation**: Distributed under the **MIT License** (see [`LICENSE`](./LICENSE)).

**Good-Faith Rightsholder Contact:** If any copyright, license, or trademark holder has any concern regarding any material in this research repository, please open an issue or contact **Amritpal Singh (`@boparaiamrit`)** directly on GitHub for prompt, good-faith review and resolution.
