---
talk: Secure Boot on Arm systems — Protecting your embedded devices
speaker: Alexandre Vicenzi（SUSE）
conference: openSUSE Conference 2024（oSC24）
year: 2024
video: https://youtu.be/3g-WURfbhKI
slides: https://files.speakerdeck.com/presentations/09affb0b08f14ba5882a506a025ba35f/oSC24_-_Secure_Boot_on_Arm_systems.pdf
---

# Secure Boot on Arm systems [▶ 影片](https://youtu.be/3g-WURfbhKI)

> **演講**：Alexandre Vicenzi（SUSE），openSUSE Conference 2024（media.ccc.de/v/4521；Speaker Deck 頁面日期 2024-06-27）
> **來源**：YouTube 錄影（25:26）用 Whisper `turbo` 轉成逐字稿，再加上講者在 Speaker Deck 放的投影片（18 頁）。
> **標記說明**：`【口頭】` 是投影片沒有的。`【投影片補充】` 是投影片有、講者沒講的。`【Q&A】` 是現場提問。`⚠️ 逐字稿缺字` 是 Whisper 聽錯。`⚠️ 待確認` 是查不清楚的地方。
> 這是一場**入門**演講：概念，加上一個 NXP Layerscape 的 TF-A build 例子，再加上怎麼在 openSUSE 的 OBS 裡做。

---

## 目錄

- [0. 這場演講要做什麼](#0-這場演講要做什麼)
- [1. Secure boot 是什麼、為什麼要](#1-secure-boot-是什麼為什麼要)
- [2. 運作方式：兩套標準](#2-運作方式兩套標準)
- [3. UEFI Secure Boot：shim、GRUB、MOK](#3-uefi-secure-bootshimgrubmok)
- [4. TF-A Trusted Board Boot](#4-tf-a-trusted-board-boot)
- [5. 哪些硬體支援](#5-哪些硬體支援)
- [6. 做一個簽好的 image：以 NXP LX2160A 為例](#6-做一個簽好的-image以-nxp-lx2160a-為例)
- [7. 在 Open Build Service 裡做](#7-在-open-build-service-裡做)
- [8. Q&A](#8-qa)
- [9. 一頁速查表](#9-一頁速查表)
- [10. 延伸連結](#10-延伸連結)

---

## 0. 這場演講要做什麼

[▶ 00:37](https://youtu.be/3g-WURfbhKI?t=37)（p.3）

講三件事：what（是什麼）、why（為什麼要）、how（怎麼做）。how 分兩套：**UEFI Secure Boot** 和 **TF-A Trusted Board Boot**（TBB）。

講者背景：SUSE 軟體工程師，現在做容器，【口頭】以前在 SUSE 車用團隊玩過 Arm 上的 secure boot。

---

## 1. Secure boot 是什麼、為什麼要

### 1.1 是什麼

[▶ 01:15](https://youtu.be/3g-WURfbhKI?t=75)（p.4）

- PC 產業訂的標準。
- 保證兩件事：
  - **真實性**（authenticity）：image 來自可信的來源。
  - **完整性**（integrity）：image 沒被竄改。
- 開機流程的每個元件都經過**數位簽章**，執行前都要**驗證**。
- **驗證失敗就中止開機**（p.4）。
- 【口頭】可以簽的不只 bootloader，也可以簽模組、driver（[▶ 01:53](https://youtu.be/3g-WURfbhKI?t=113)）。
- 名詞：secure boot、trusted boot、chain of trust。【口頭】文件裡用的詞不一樣，但通常是同一件事：把機器鎖起來，只讓你想開的東西開機。

### 1.2 為什麼要

[▶ 02:27](https://youtu.be/3g-WURfbhKI?t=147)（p.5）

- **安全**：只開驗證過、可信的 image，確定沒被竄改。
  - 【口頭】IoT 的例子：電視、冰箱、洗衣機，或基地台裡的伺服器，都要確定跑的是該跑的東西。
- **法規**：歐盟 **Cyber Resilience Act**（網路韌性法案）。【口頭】某些市場可能會被要求。

---

## 2. 運作方式：兩套標準

[▶ 03:29](https://youtu.be/3g-WURfbhKI?t=209)（p.6）

1. image 都要簽：韌體、bootloader。【口頭】想的話 kernel 也能簽。
2. 每個 image 執行前先驗簽章。【口頭】由主機板或 SoC boot ROM 的韌體驗。
3. **驗證用的金鑰要安全存放**：
   - SoC 上（【口頭】例如 eFuse）。
   - 或 NV-RAM（【口頭】一般 PC 的 UEFI）（[▶ 04:06](https://youtu.be/3g-WURfbhKI?t=246)）。

**細節依架構和廠商而不同**：

| 標準 | 常見在哪 |
|---|---|
| UEFI Secure Boot | x86 的標準；資料中心的 Arm 伺服器常見 |
| TF-A Trusted Boot | 嵌入式、小板子 |

【口頭】就算是同一套標準，怎麼燒錄板子、怎麼啟用、怎麼部署 image，各家都會有些不同。

---

## 3. UEFI Secure Boot：shim、GRUB、MOK

[▶ 04:40](https://youtu.be/3g-WURfbhKI?t=280)（p.7–8）

**基本機制**：UEFI 載入的每個程式都要驗證過、被信任。驗證失敗，開機就停下來，【口頭】會出現錯誤訊息。

**shim 的角色**（[▶ 05:10](https://youtu.be/3g-WURfbhKI?t=310)）：
- **shim** 是一個 EFI 應用程式，當第一階段 bootloader。大多數發行版都用它。
- **shim 由 Microsoft UEFI CA 簽章**。
  - 【口頭】因為大多數 PC 出廠就帶 Microsoft 的金鑰（用來驗 Windows），所以由 Microsoft 幫各發行版簽 shim。
  - 【口頭】自己做發行版也可以送申請，但講者不確定流程。
- shim 裡放著**發行版自己的金鑰**（例如 openSUSE 的），用它來驗 GRUB（[▶ 06:11](https://youtu.be/3g-WURfbhKI?t=371)）。
- 【口頭】**這樣設計的好處**：只要不改 shim、不換簽 GRUB 的金鑰，發行版就能一直出新 image，不必每次都請 Microsoft 簽。

**驗證順序**（p.8）：

```
UEFI ─驗→ shim ─驗→ GRUB ─(可以)驗→ kernel
```

- p.8：驗證失敗時系統會 panic。

**自己控制硬體時可以拿掉 shim**（[▶ 06:46](https://youtu.be/3g-WURfbhKI?t=406)）：
- 【口頭】做 IoT 或自己控制部署的硬體時，可以把**自己的金鑰**放進硬體，不必是 Microsoft 的，這樣就能拿掉 shim。
- 【口頭】如果你知道自己在做什麼，甚至可以連 GRUB 都拿掉，直接開 kernel，因為 kernel 本身就是 EFI stub（[▶ 07:16](https://youtu.be/3g-WURfbhKI?t=436)）。
  > ⚠️ 逐字稿缺字：「the kernel is 5-star」推測是「EFI stub」。

**MOK**（Machine Owner Key，[▶ 07:16](https://youtu.be/3g-WURfbhKI?t=436)）：
- shim 允許使用者**自己管理金鑰**，放在 MOK 資料庫，可以新增、刪除。
- 跟發行版的 CA 金鑰分開。
- 【口頭】例如：自己在本機編的模組，可以用自己的金鑰簽。

> ⚠️ 逐字稿缺字：「Sheen」「Shin」＝shim；「CRR」「Glue」＝GRUB。

---

## 4. TF-A Trusted Board Boot

[▶ 07:49](https://youtu.be/3g-WURfbhKI?t=469)（p.9–10）

**根據**：Arm **TBBR**（Trusted Board Boot Requirements），文件編號 ARM DEN0006D。

- 用公開金鑰密碼學建立信任鏈：**每一段信任下一段**。
- 【口頭】概念跟 UEFI secure boot 類似，實作不同（[▶ 08:19](https://youtu.be/3g-WURfbhKI?t=499)）。
- 驗證範圍：所有韌體 image，一直到一般的 bootloader。
- 流程依平台和廠商不同。【口頭】要看廠商文件，有些要簽 NDA 才拿得到，因為裡面有廠商不想公開的架構設計（[▶ 08:49](https://youtu.be/3g-WURfbhKI?t=529)）。

**建立信任鏈需要的東西**（p.9）：

1. **BL1 在 ROM 裡**。
2. **自簽憑證**。
3. **簽所有韌體 image**。【口頭】要簽哪些看平台。
4. **金鑰燒錄**（key provisioning），三步：
   - **燒金鑰**：把金鑰寫進 SoC 或硬體某處。
   - **鎖金鑰**：讓它不能被換掉。
   - **強制 secure boot**。

**口頭補充的細節**（[▶ 09:20](https://youtu.be/3g-WURfbhKI?t=560)）：
- 【口頭】**撤銷**（revocation）：有些平台可以撤銷金鑰。例如金鑰外洩時，可以撤銷。
- 【口頭】**開發模式與量產模式**（[▶ 09:52](https://youtu.be/3g-WURfbhKI?t=592)）：
  - 通常在燒金鑰時（或之前），要先把板子設成 secure boot 模式。
  - 有些板子有兩種模式：
    - **開發**：可以燒很多次金鑰。
    - **量產**：鎖住之後就沒人能換金鑰了，但需要時還是可以撤銷。

**驗證順序**（p.10；[▶ 10:25](https://youtu.be/3g-WURfbhKI?t=625)）：

```
BL1（Trusted ROM）─驗→ BL2（Trusted Boot）─驗→ BL31（Runtime）
                                         ├驗→ BL32（Secure Payload，例如 OP-TEE）
                                         └驗→ BL33（Bootloader，例如 U-Boot）─(若有金鑰)驗→ kernel
```

- p.10：驗證失敗，系統 panic。
- 【口頭】跟 UEFI 的反應類似，會停下來（[▶ 11:00](https://youtu.be/3g-WURfbhKI?t=660)）。
- 【口頭】BL32 在大多數平台上是 OP-TEE，也可以是別的 secure payload。
- 【口頭】U-Boot 有金鑰、kernel 也簽了的話，U-Boot 就能驗 kernel。
- 【口頭】**概念一樣，實作不一樣**：依架構、廠商、板子而不同，甚至同一廠商的不同板子都不一樣。

---

## 5. 哪些硬體支援

[▶ 11:35](https://youtu.be/3g-WURfbhKI?t=695)（p.11）

| 平台 | secure boot 機制 |
|---|---|
| 符合 Arm SystemReady 的平台（Ampere、NVIDIA、NXP、Xilinx…） | UEFI Secure Boot（標準 PC 開機方式） |
| NXP i.MX 6/7/8/9 | High Assurance Boot（HABv4） |
| NXP Layerscape | QorIQ Trust Architecture。【口頭】跟 i.MX 的類似，但有點不同 |
| Marvell Armada、STM32 等 | — |

【口頭】**要做產品，一定要先問廠商或看廠商文件**，確定有支援某種 secure boot。不是每家廠商的每顆晶片都支援，有時要找他們談（[▶ 12:44](https://youtu.be/3g-WURfbhKI?t=764)）。

---

## 6. 做一個簽好的 image：以 NXP LX2160A 為例

### 6.1 流程

[▶ 12:44](https://youtu.be/3g-WURfbhKI?t=764)（p.12）

1. **產生簽章用的金鑰對。**
2. **準備 binary**：
   - 廠商韌體
   - kernel、initramfs、DTB
   - TF-A、U-Boot
3. **簽 binary**：
   - TF-A 在 **build 時**就會簽。【口頭】金鑰放一個地方，它就幫你簽好開機流程裡的很多段（[▶ 13:56](https://youtu.be/3g-WURfbhKI?t=836)）。
   - 有些平台要用**廠商專屬工具**才能簽。
4. **全部打包。**

### 6.2 準備 TF-A

[▶ 13:56](https://youtu.be/3g-WURfbhKI?t=836)（p.13）

- **相依**：
  - U-Boot
  - OP-TEE（選用。【口頭】想多一層安全時用）
  - 簽章金鑰
  - 有些平台還要：廠商專屬的初始化韌體、廠商專屬的簽章工具
- **額外的 build 參數**：
  - `TRUSTED_BOARD_BOOT=1`
  - `GENERATE_COT=1`。【口頭】有些平台才要。
- **簽章嵌進每個 image**：
  - p.13 寫 BL2、BL31、BL32、BL33。
  - 講者口頭說 TF-A 會處理「BL1、BL2、BL31、BL32、BL33」的簽章（[▶ 14:26](https://youtu.be/3g-WURfbhKI?t=866)），多了 BL1。
  - 兩邊都記下來。⚠️ 待確認

### 6.3 Build 指令

[▶ 15:04](https://youtu.be/3g-WURfbhKI?t=904)（p.14，原文）

```
$ make PLAT=lx2160ardb \
    TRUSTED_BOARD_BOOT=1 \
    CST_DIR=/cst \
    BOOT_MODE=sd \
    RCW=/rcw/rcw_2200_750_3200_19_5_2.bin \
    BL33=/boot/u-boot.bin \
    all fip pbl
```

| 參數 | 意思（口頭說明） |
|---|---|
| `PLAT=lx2160ardb` | 目標平台 |
| `TRUSTED_BOARD_BOOT=1` | 開 TBB |
| `CST_DIR` | NXP 的 **CST**（Code Signing Tool）在哪裡。【口頭】它是開源的，但沒有內建在 TF-A 裡，要另外從 NXP 那邊抓（[▶ 15:46](https://youtu.be/3g-WURfbhKI?t=946)） |
| `BOOT_MODE=sd` | 開機媒體。【口頭】平台可能支援 eMMC、SD、板上 flash，要選一個 |
| `RCW` | LX2160 一定要的初始化韌體（Reset Configuration Word）。【口頭】用來初始化 CPU、RAM 等（[▶ 16:17](https://youtu.be/3g-WURfbhKI?t=977)） |
| `BL33` | U-Boot 在哪裡 |
| `all fip pbl` | p.14 的標註：先編譯，再做出 FIP 和 PBL |

### 6.4 打包

[▶ 16:17](https://youtu.be/3g-WURfbhKI?t=977)（p.15）

1. 做 rootfs：kernel、initramfs、DTB、bootloader、user space 程式。
2. 把簽好的韌體檔寫到**各自的 offset**。
   - offset 依平台和儲存類型而不同。
   - 【口頭】例如 U-Boot 要寫在某個位置，NXP 的初始化韌體要寫在另一個位置。一定要查文件。

---

## 7. 在 Open Build Service 裡做

[▶ 17:25](https://youtu.be/3g-WURfbhKI?t=1045)（p.16）

- 可以在 openSUSE 的 **OBS**（Open Build Service）做。
- 用 **KIWI** build image，用 KIWI 的使用者自訂 script 改 image。
- 【口頭】openSUSE 出的 Arm image 大多已經在用 script，因為很多平台要把 U-Boot 寫在特定位置。

兩個 script：

| script | 做什麼 |
|---|---|
| `pre_disk_sync.sh` | 改 root tree 的內容：把韌體、bootloader、DTB 等複製到正確位置 |
| `editbootinstall.sh` | 把 binary 寫進磁碟的 offset。每個韌體檔有自己的 offset，依板子和媒體（eMMC、SD…）不同 |

**金鑰的問題**（[▶ 18:11](https://youtu.be/3g-WURfbhKI?t=1091)）：
- 全部在 OBS 做的話，**簽章私鑰得放在 OBS 裡**，所以**不能用公開的 instance**。
- 【口頭】做法：
  - 用防火牆後面的私有 instance。
  - 或在 OBS 外面 build 好要簽的 binary，把簽好、不含金鑰的東西上傳，再在 OBS 裡做 image。
- 【口頭】OBS 現在可以放一些憑證，但不適合這種情境。也許將來會有安全存放金鑰的做法（[▶ 19:06](https://youtu.be/3g-WURfbhKI?t=1146)）。

參考資料（p.17）：TF-A Trusted Board Boot 文件、openSUSE UEFI、NXP Layerscape SDK User Guide、NXP Code Signing Tool。

---

## 8. Q&A

【Q&A】**Q：NXP 板子的 TF-A 流程很特殊。如果有另一塊板子流程不同，能不能做一個 image，裝的時候自己判斷要用哪種設定？**（[▶ 20:30](https://youtu.be/3g-WURfbhKI?t=1230)）

- 裝置支援 **UEFI** 的話：**可以**，一個 image 通吃。openSUSE 的 x86 UEFI、Arm UEFI image 就是這樣，只看架構，在任何機器上都能開（[▶ 21:10](https://youtu.be/3g-WURfbhKI?t=1270)）。
- 用 **TF-A** 的話：**每個平台都要各自 build**。
  - 【口頭】至少在 NXP 上，每塊板子、甚至每個板子版本的流程都可能不同。
  - 所以在現場部署多種裝置，可能就要做多個 image（[▶ 22:13](https://youtu.be/3g-WURfbhKI?t=1333)）。

【Q&A】**Q：最近有 Qualcomm Snapdragon 的 Arm 筆電。有人說廠商可以像手機一樣把它鎖起來，進不了 bootloader 就沒戲了。你覺得廠商會擋掉 Linux 嗎？**（[▶ 22:13](https://youtu.be/3g-WURfbhKI?t=1333)）

- 看廠商。**鎖板子本來就是 secure boot 的用意**：鎖起來之後什麼都不能換（[▶ 23:51](https://youtu.be/3g-WURfbhKI?t=1431)）。
- 有些 Android 裝置能換 OS，但通常不容易，或要付出代價。
- 講者不了解那些 Snapdragon 筆電（他知道 Lenovo 和 Microsoft Surface 有幾款）。
- 他的看法：通常**能裝 Windows 的機器，就能換掉 Windows**，因為通常沒鎖死，主機板韌體也能改設定。但這些平台到底鎖到什麼程度，他不確定（[▶ 24:27](https://youtu.be/3g-WURfbhKI?t=1467)）。

---

## 9. 一頁速查表

| | UEFI Secure Boot | TF-A TBB |
|---|---|---|
| 規範 | UEFI | Arm TBBR（DEN0006D） |
| 常見平台 | x86、Arm 伺服器（SystemReady） | 嵌入式 |
| 驗證鏈 | UEFI → shim → GRUB → kernel | BL1 → BL2 → BL31／BL32／BL33 →（U-Boot 驗 kernel） |
| 根金鑰放哪 | NV-RAM（UEFI 變數） | SoC（eFuse 等），要燒、鎖、強制啟用 |
| 誰簽第一段 | Microsoft UEFI CA 簽 shim | 自己的金鑰（TF-A build 時用 `TRUSTED_BOARD_BOOT=1` 簽） |
| 使用者自己的金鑰 | MOK | 開發模式可多次燒；量產鎖死，可能可以撤銷 |
| 一個 image 跑多種板子 | 可以 | 不行，每個平台、甚至每個板子版本各做一個 |
| 驗證失敗 | 停止開機（p.8：panic） | panic |

**做 image 的關鍵**：金鑰對 → build 時簽（TF-A＋CST 等廠商工具）→ 寫到平台規定的 offset。私鑰不能放在公開 build 服務上。

---

## 10. 延伸連結

- MT8189 上實際開 TF-A TBB、FIT 簽章：[`../verified-boot-notes/fit-sign.md`](../verified-boot-notes/fit-sign.md)
- TF-A secure boot 概觀：[`../tf-a-and-op-tee-note/secure-boot-intro.md`](../tf-a-and-op-tee-note/secure-boot-intro.md)

---

## 附：一句話總結

> **Secure boot 有兩套：伺服器／PC 用 UEFI（UEFI → Microsoft 簽的 shim → GRUB），嵌入式用 TF-A TBB（ROM 裡的 BL1 一段段驗到 U-Boot）。後者要自己燒、鎖金鑰，而且每個平台的簽章工具、offset 都不一樣。**

---

## ⚠️ 待確認清單

1. [▶ 14:26](https://youtu.be/3g-WURfbhKI?t=866) TF-A build 時簽哪幾段：p.13 寫 BL2、BL31、BL32、BL33，講者口頭多了 BL1。

---

*筆記依據 Alexandre Vicenzi〈Secure Boot on Arm systems〉（openSUSE Conference 2024）錄影（Whisper `turbo` 轉錄，25:26）與講者 Speaker Deck 投影片整理。*
