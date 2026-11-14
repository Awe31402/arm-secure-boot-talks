---
talk: Overview of Secure Boot state in the ARM-based SoCs
speaker: Maciej Pijanowski（3mdeb）
conference: FOSDEM 2021，Hardware-Aided Trusted Computing devroom（線上）
year: 2021
video: https://youtu.be/QtYO1vbyoN0
slides: https://archive.fosdem.org/2021/schedule/event/tee_arm_secboot/attachments/paper/4635/export/events/attachments/tee_arm_secboot/paper/4635/Overview_of_Secure_Boot_in_Arm_based_SoCs.pdf
---

# Overview of Secure Boot state in the ARM-based SoCs [▶ 影片](https://youtu.be/QtYO1vbyoN0)

> **演講**：Maciej Pijanowski（3mdeb 嵌入式韌體團隊主管），FOSDEM 2021 Hardware-Aided Trusted Computing devroom
> **來源**：YouTube（3mdeb 頻道，2024-07-04 上傳）錄影（14:31）用 Whisper `turbo` 轉成逐字稿，再加上 FOSDEM 官方附件投影片（26 頁）。
> **標記說明**：`【口頭】` 是投影片沒有的。`【投影片補充】` 是投影片有、講者沒講的。`⚠️ 逐字稿缺字` 是 Whisper 聽錯。`⚠️ 待確認` 是查不清楚的地方。
> **年代提醒**：這是 2021 年的調查結果。各家文件公開程度之後可能變了，筆記照講者當時講的寫。第二版（2023）見 [06b](06b-zyjewski-secure-boot-arm-socs-overview-2nd.md)。
> 錄影最後只說「現在是提問時間」，影片沒有錄到 Q&A。

---

## 目錄

- [0. 這場演講要做什麼](#0-這場演講要做什麼)
- [1. 這裡說的 secure boot 是什麼](#1-這裡說的-secure-boot-是什麼)
- [2. 典型實作與流程](#2-典型實作與流程)
- [3. 各家 SoC 逐一看](#3-各家-soc-逐一看)
- [4. 總表](#4-總表)
- [5. 結論](#5-結論)
- [6. 一頁速查表](#6-一頁速查表)
- [7. 延伸連結](#7-延伸連結)

---

## 0. 這場演講要做什麼

[▶ 00:00](https://youtu.be/QtYO1vbyoN0?t=0)（p.2）

1. 說明「secure boot」在這場指的是什麼。
2. 典型的實作與流程。
3. **調查結果**：11 家（系列）Arm SoC 的 secure boot，文件、工具拿不拿得到、要不要 NDA。

---

## 1. 這裡說的 secure boot 是什麼

[▶ 01:35](https://youtu.be/QtYO1vbyoN0?t=95)（p.6）

- 只談 **Arm**。
- 指的是**廠商 boot ROM 的一個功能**。
- 【口頭】其實叫 **verified boot** 更貼切：主要目的是**執行韌體之前先驗它**。
  - 驗的是韌體的簽章。私鑰用來簽，公鑰用來驗，**裝置一定要知道公鑰**。
- **假設 boot ROM 是可信的。**
  - 【口頭】有些人會不同意，因為 boot ROM 在所有情況下都是**閉源、我們無法控制**的程式碼（[▶ 02:07](https://youtu.be/QtYO1vbyoN0?t=127)）。
- 在不同架構、不同情境下，「secure boot」的意思可能不一樣。

---

## 2. 典型實作與流程

### 2.1 典型實作

[▶ 02:07](https://youtu.be/QtYO1vbyoN0?t=127)（p.7）

- **公鑰永久寫進 SoC**：用 **eFuse**（電子熔絲）或其他 **OTP**（一次性可程式化）暫存器。
- 這把公鑰就是驗證鏈的 **root of trust**。
- boot ROM 用 fuse 裡的公鑰驗**第一個**元件。之後的元件可以用**不同的金鑰**（p.7 的圖：ROM 用 pubkey 1 驗 bootloader，bootloader 用 pubkey 2 驗 kernel）。
- 【投影片補充】p.7：後面的元件一定要鎖好（例如**關掉 U-Boot shell**），信任鏈才保得住。
- **這場只看第一步**：boot ROM 驗第一個 binary（[▶ 02:40](https://youtu.be/QtYO1vbyoN0?t=160)）。

### 2.2 典型流程

[▶ 03:15](https://youtu.be/QtYO1vbyoN0?t=195)（p.8）

1. 產生金鑰對。
2. 在**安全的地方**用私鑰簽韌體。
3. 把公鑰 fuse 進 SoC。
4. 開啟 secure boot 功能。
5. 確認韌體驗證正常。
6. **鎖住（close）平台**。從此只有簽過的韌體能跑。
   - 【口頭】鎖平台通常也是**燒某一個特定的 fuse**。

**什麼情況會失敗或被繞過**：
- 講者只講了正常流程。
- 以下**不是逐字稿內容**，是依 p.8 的順序推論的：第 5 步確認之前就做第 6 步，萬一簽章或 fuse 有錯，裝置就只能跑「驗不過的韌體」，等於變磚。所以順序很重要。

### 2.3 簽過的 binary 長什麼樣

[▶ 03:49](https://youtu.be/QtYO1vbyoN0?t=229)（p.9）

- 通常是原本的 binary 資料**加上一個 header**。
- header 格式每家不同。
- 共同點：**數位簽章是 header 的主要內容之一**。

---

## 3. 各家 SoC 逐一看

### 3.1 NXP i.MX 6/7/8：HABv4

[▶ 04:20](https://youtu.be/QtYO1vbyoN0?t=260)（p.10–11）

- 名字：**HAB**（High Assurance Boot），boot ROM 的功能。
- 最多存 **5 把**公鑰。
- 支援 RSA 1024–4096、EC p256／p384／p521。
- **HAB API 可以驗不只一個 binary**：
  - 【口頭】例如在 U-Boot 裡呼叫 HAB API，用 fuse 在 SoC 裡的那把公鑰**直接驗 kernel image**。
  - 【口頭】這樣**一把金鑰就能驗整條開機鏈的所有元件**（[▶ 04:20](https://youtu.be/QtYO1vbyoN0?t=260)）。
- **文件**：
  - 應用筆記免費：AN4581（HABv4 secure boot）、AN12263（HABv4 RVT 指引）。
  - 網路上有很多教學。
  - SoC reference manual：免費註冊後可下載。
  > ⚠️ 逐字稿缺字：講者念「AN3581」，p.11 是 AN4581。
- **簽章工具**：CST（Code Signing Tool），免費註冊後下載。可以搭配 HSM（AN12812）。
- **boot ROM 也會有漏洞**（[▶ 05:26](https://youtu.be/QtYO1vbyoN0?t=326)）：
  - 幾年前 HAB 就被找到過漏洞（p.11 附 Quarkslab 的文章）。
  - 【口頭】**用的時候要確定你的裝置用的是修補過的 boot ROM。**

### 3.2 NXP Layerscape：QorIQ Trust Architecture

[▶ 05:59](https://youtu.be/QtYO1vbyoN0?t=359)（p.12）

- secure boot 是 QorIQ Trust Architecture 的功能之一。【口頭】大部分 Layerscape 都有。
- 功能、文件狀況都跟 HAB 類似。
- 應用筆記免費（AN5227）。
- **LSDK User Guide 第 6.1 節「Secure boot」寫得很好。**
- reference manual、簽章工具要註冊。簽章工具是 CST，包在 LSDK 裡。

### 3.3 Marvell Armada

[▶ 06:33](https://youtu.be/QtYO1vbyoN0?t=393)（p.13）

- **細節不公開**：SoC reference manual 和 secure boot 應用筆記（AN-383）都要 **NDA**。
- 但 Marvell 的 GitHub repo 有用：
  - U-Boot repo 的 `doc/mvebu/trusted_boot.txt` **幾乎是一步一步的教學**。
  - 32 位元 Armada 38x 和 64 位元 Armada 7k/8k 流程類似。
  - **U-Boot 和 EDK2 都有燒 fuse 的指令**（[▶ 07:11](https://youtu.be/QtYO1vbyoN0?t=431)）。
  - 簽章工具：`atf-marvell` repo 的 `tools/doimage`。

### 3.4 ST STM32MP1

[▶ 07:11](https://youtu.be/QtYO1vbyoN0?t=431)（p.14）

- 【口頭】ST 不久前才用 STM32MP1 進入 Linux 市場。
- **只支援 EC 金鑰，不支援 RSA**（跟其他家不同）。
- 線上文件品質高（ST wiki）。
- 產生金鑰、簽章的工具是 STM32CubeProgrammer 的一部分，免費註冊下載。

### 3.5 Xilinx Zynq

[▶ 07:43](https://youtu.be/QtYO1vbyoN0?t=463)（p.15）

- RSA 2048。
- 【口頭】**可能是文件最開放的廠商**：reference manual 和 secure boot 文件**不用註冊**就能下載（[▶ 08:21](https://youtu.be/QtYO1vbyoN0?t=501)）。
- 應用筆記 XAPP1175 把 secure boot 準備流程寫得很詳細。
- Zynq-7000 TRM 第 32 章「Device Secure Boot」。

### 3.6 NVIDIA Tegra

[▶ 08:53](https://youtu.be/QtYO1vbyoN0?t=533)（p.16）

- RSA 2048。
- **線上 JetPack SDK 文件就有實作需要的所有細節。**
- 【口頭】金鑰直接用 `openssl` 指令產生。
- 燒 fuse：JetPack SDK 的 `odmfuse.sh`。
- 簽章：燒錄 script `flash.sh` 有簽章選項。
- 【投影片補充】Xavier TRM 裡跟 secure boot 有關的內容不多，線上文件就夠了。

### 3.7 Microchip（Atmel）SAMA5

[▶ 09:26](https://youtu.be/QtYO1vbyoN0?t=566)（p.17）

- RSA。
- 公開文件 AN2748 **少了一些細節**；更多文件（AN2435）要 NDA。
- 簽章、燒 fuse 用 **Secure SAM-BA** 工具。用法有寫在 AN2748，但**工具本身要 NDA**。

### 3.8 TI Sitara

[▶ 09:57](https://youtu.be/QtYO1vbyoN0?t=597)（p.18）

- 公開文件（AM335x TRM）**只說有 secure boot**，沒有細節。
- 高階概觀文件「真的很高階」。【口頭】比較像行銷文宣，不是技術文件。
- 要更多細節得聯絡 TI 或簽 NDA。

### 3.9 Qualcomm

[▶ 10:29](https://youtu.be/QtYO1vbyoN0?t=629)（p.19）

- 只有高階的公開文件（Secure Boot and Image Authentication Technical Overview）。用 RSA。
- 第三方文章有些有趣的資訊（Timesys、LineageOS 部落格）。
- 簽章工具是專屬的 **sectool**，要 NDA。
  > ⚠️ 逐字稿缺字：「intersec tool」＝sectool（依 p.19）。

### 3.10 Rockchip

[▶ 11:04](https://youtu.be/QtYO1vbyoN0?t=664)（p.20）

- RK3399 TRM 提到有 secure boot 和 eFuse（兩組 1024 bit eFuse），但：
  - 不清楚**哪些 eFuse 暫存器存公鑰**。
  - 不清楚**怎麼燒 eFuse**。
- 網路上找得到「Rockchip Secure Boot Specification」之類的文件。
- 有一個 Windows 工具 `SecureBootTool`，用來產生金鑰、簽韌體。
- 結論：**很可能有某種 secure boot，但不清楚怎麼用**。找不到成功案例，要跟廠商聯絡（[▶ 11:39](https://youtu.be/QtYO1vbyoN0?t=699)）。

### 3.11 Allwinner

[▶ 11:39](https://youtu.be/QtYO1vbyoN0?t=699)（p.21）

- 有跡象顯示有某種 secure boot。
- **可能沒有人知道怎麼用。**
- Armbian 論壇上最深入的一個使用者嘗試，做到一半卡住了。

---

## 4. 總表

[▶ 12:14](https://youtu.be/QtYO1vbyoN0?t=734)（p.22–23；p.22 是一張圖，這裡照圖抄成表）

| SoC | 文件（eFuse 暫存器表、secure boot 細節） | 應用筆記／教學 | 燒 fuse 工具 | 簽章工具 | 不簽 NDA 能用嗎？ |
|---|---|---|---|---|---|
| NXP i.MX 6/7/8 | yes (1) | yes | yes | yes (1) | yes |
| NXP Layerscape | yes (1) | yes | yes | yes (1) | yes |
| Marvell Armada | NDA (2) | NDA (2) | yes (2) | yes (2) | yes (2) |
| ST STM32MP1 | yes | yes | yes (1) | yes (1) | yes |
| Xilinx Zynq | yes | yes | yes | yes | yes |
| NVIDIA Tegra | yes | yes | yes (1) | yes (1) | yes |
| Microchip SAMA5 | NDA | NDA | NDA | NDA | no |
| TI Sitara | NDA | NDA | NDA | NDA | no |
| Qualcomm | NDA | NDA | NDA | NDA | no |
| Rockchip | 有一些文件流傳 | 沒資訊 | 沒資訊 | 好像有，可能要 NDA | 大概不行 |
| Allwinner | 沒資訊 | 沒資訊 | 沒資訊 | 沒資訊 | 大概不行 |

註（p.23）：
- (1) 要免費註冊。
- (2) Marvell U-Boot repo 裡的文件應該夠讓東西動起來，但不夠完全理解。

口頭重點：
- 【口頭】**11 個案例裡，6 個不簽任何 NDA 就能用 secure boot。**
- 【口頭】Marvell 很有趣：文件要 NDA，但 GitHub 上的資訊和工具應該足夠實作，只是可能不會完全理解細節（[▶ 12:45](https://youtu.be/QtYO1vbyoN0?t=765)）。
- 【口頭】大多數廠商至少要免費註冊才拿得到部分文件和工具。

---

## 5. 結論

[▶ 12:45](https://youtu.be/QtYO1vbyoN0?t=765)（p.24）

1. **各家的做法大同小異**：
   - 執行前驗 image。
   - 公鑰放在 eFuse。
   - 燒某個特定 fuse 來「鎖」裝置（切到 secure 模式）。
2. **最常見的簽章金鑰是 RSA-2048**：
   - 有的只支援 EC（ST）。
   - 有的兩種都支援（NXP：RSA 最高 4096，加幾種 EC）。
3. **雜湊函數全部都是 SHA-256**（[▶ 13:45](https://youtu.be/QtYO1vbyoN0?t=825)）。
4. 通常也有**韌體解密**功能，但不在這場的範圍。

---

## 6. 一頁速查表

**通用流程（各家都一樣）**：產生金鑰對 → 在安全處簽韌體（加 header＋簽章）→ 公鑰（或其雜湊）燒進 eFuse/OTP → 開 secure boot → 確認驗證正常 → 燒「鎖定」fuse。

**選 SoC 時看這幾點**：

| 問題 | 好的答案 | 差的答案 |
|---|---|---|
| eFuse 暫存器表和 secure boot 細節公開嗎？ | 免費或免費註冊（NXP、ST、Xilinx、NVIDIA） | 要 NDA（Microchip、TI、Qualcomm） |
| 燒 fuse、簽章的工具拿得到嗎？ | 開源或免費註冊 | NDA、或只有 Windows 工具（Rockchip） |
| 有人成功做過嗎？ | 有應用筆記、有教學 | 找不到成功案例（Rockchip、Allwinner） |
| boot ROM 有沒有已知漏洞？ | 已修補的版本 | 有漏洞的舊 ROM（例如舊版 i.MX HAB） |

**演算法**：RSA-2048 最常見；ST 只有 EC；NXP 最彈性；全部 SHA-256。

---

## 7. 延伸連結

- MT8189 上 BL2 eFuse（MediaTek 這家的做法）：[`../verified-boot-notes/vb-intro.md`](../verified-boot-notes/vb-intro.md)
- 第二版（2023，加了 Rockchip、MediaTek 實例）：[06b](06b-zyjewski-secure-boot-arm-socs-overview-2nd.md)

---

## 附：一句話總結

> **各家 Arm SoC 的 secure boot 原理幾乎一樣（ROM 用 eFuse 裡的公鑰驗第一個 binary，再燒 fuse 鎖板），真正的差別在文件和工具能不能拿到。2021 年 11 家裡有 6 家不用 NDA 就能做。**

---

*筆記依據 Maciej Pijanowski〈Overview of Secure Boot state in the ARM-based SoCs〉（FOSDEM 2021）錄影（Whisper `turbo` 轉錄，14:31）與 FOSDEM 官方附件投影片整理。*
