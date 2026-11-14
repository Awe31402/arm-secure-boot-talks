---
talk: Implementing UEFI-based Secure Boot + OTA Update for Embedded ARM Devices
speaker: Jan Kiszka、Christian Storm（Siemens AG）
conference: 待補（Linux Foundation 頻道 2022-10-08 上傳；推定為 2022 年 9 月的 ELC Europe／Open Source Summit Europe，見待確認）
year: 2022
video: https://youtu.be/H_dBnwkTAbw
slides: 待補（sched 擋自動抓取，找不到官方投影片）
---

# Implementing UEFI-based Secure Boot + OTA Update for Embedded ARM Devices [▶ 影片](https://youtu.be/H_dBnwkTAbw)

> **演講**：Jan Kiszka、Christian Storm（Siemens Technology），Linux Foundation 頻道 2022-10-08 上傳。
> **場次**：講者說「兩年前我們在線上講過概念和 x86 實作」（說明欄：ELC 2020）。會議名稱沒有直接證據。⚠️ 待確認
> **來源**：YouTube 錄影（41:52）用 Whisper `turbo` 轉成逐字稿。**沒有投影片**，講者說「如圖」的地方都看不到，「slide 13」也只能從口頭推。
> **分工**：Jan 講 UEFI 這半邊，Christian 講 OS 這半邊（OTA、找 rootfs、dm-verity）。
> **標記說明**：`【口頭】` 這場沒有投影片，正文幾乎全是口頭，只標實務經驗和取捨。`【Q&A】` 是現場提問。很多提問者沒用麥克風，聽不清楚的寫「（問題聽不清）」。`⚠️ 逐字稿缺字` 是 Whisper 聽錯。`⚠️ 待確認` 是查不清楚的地方。

---

## 目錄

- [0. 這場演講要做什麼](#0-這場演講要做什麼)
- [1. 背景：為什麼要 secure boot＋可回滾的 OTA](#1-背景為什麼要-secure-boot可回滾的-ota)
- [2. x86 的做法（他們已經做過）](#2-x86-的做法他們已經做過)
- [3. Arm 現在的做法與問題](#3-arm-現在的做法與問題)
- [4. 想法：讓 Arm 也走 UEFI](#4-想法讓-arm-也走-uefi)
- [5. 誰能提供 UEFI：EDK2 vs U-Boot](#5-誰能提供-uefiedk2-vs-u-boot)
- [6. 用 U-Boot UEFI 做 secure boot：步驟與強化清單](#6-用-u-boot-uefi-做-secure-boot步驟與強化清單)
- [7. UEFI payload：EFI Boot Guard 與 UKI 的坑](#7-uefi-payloadefi-boot-guard-與-uki-的坑)
- [8. OS 這半邊：A/B 更新](#8-os-這半邊ab-更新)
- [9. UKI 怎麼找到自己的 rootfs](#9-uki-怎麼找到自己的-rootfs)
- [10. 加上 dm-verity](#10-加上-dm-verity)
- [11. 上游與參考實作：isar-cip-core](#11-上游與參考實作isar-cip-core)
- [12. Q&A](#12-qa)
- [13. 一頁速查表](#13-一頁速查表)
- [14. 延伸連結](#14-延伸連結)

---

## 0. 這場演講要做什麼

[▶ 01:01](https://youtu.be/H_dBnwkTAbw?t=61)

- 兩年前他們講過概念和 **x86** 實作。
- 今天要講：**同一套模式怎麼搬到 Arm 上**。
- 講者背景：
  - Siemens 內部的嵌入式 Linux 顧問和開發者。
  - 都參與 **CIP**（Civil Infrastructure Platform）：Christian 在軟體更新工作組，Jan 帶 kernel 工作組，並維護 **isar-cip-core** layer。

> ⚠️ 逐字稿缺字：「UAV-based」＝UEFI-based；「Jan Kiska」＝Kiszka；「ESA-CIP core／ISA SIP core」＝isar-cip-core。

---

## 1. 背景：為什麼要 secure boot＋可回滾的 OTA

[▶ 01:31](https://youtu.be/H_dBnwkTAbw?t=91)

- 以前是燒在 ROM 的韌體，現在要彈性得多：
  - 到處都連網。
  - 安全是標配。
  - **安全更新不用再討論了**，在他們的一些領域甚至**被標準強制要求**。
- 更新必須**無人值守**，所以一定要**穩健**（[▶ 02:06](https://youtu.be/H_dBnwkTAbw?t=126)）：
  - 測試沒抓到的問題，在現場出事時要能**回滾**。
  - 讓現場所有裝置回到一致的狀態。

---

## 2. x86 的做法（他們已經做過）

[▶ 02:36](https://youtu.be/H_dBnwkTAbw?t=156)

```
UEFI 韌體 ─驗→ EFI Boot Guard（A/B 切換＋開 watchdog）─驗→ UKI（kernel＋cmdline＋initrd）
   → rootfs 唯讀部分：dm-verity
   → 可寫部分：dm-crypt，金鑰來自 TPM
```

| 段 | 做什麼 | 為什麼 |
|---|---|---|
| UEFI 韌體 | 驗下一段的簽章 | x86 現實上都從 UEFI 開機 |
| **EFI Boot Guard** | 他們自己的 UEFI bootloader：**A/B 切換**、**開啟 watchdog** | 可以靠 UEFI 做 A/B，但【口頭】UEFI 實作五花八門，用一個自己熟的 bootloader 比較保險。**watchdog 不是 UEFI 的服務**，一定要有人開（[▶ 03:09](https://youtu.be/H_dBnwkTAbw?t=189)） |
| **UKI** | 把 kernel、cmdline、（initrd）合成**一個** UEFI binary 一起簽 | 只簽 kernel 的話，initrd 和 cmdline 就沒被保護（[▶ 03:42](https://youtu.be/H_dBnwkTAbw?t=222)） |
| rootfs 唯讀部分 | dm-verity | 確認是出廠的樣子 |
| rootfs 可寫部分 | dm-crypt | 現場一定要能改的資料 |
| 平台金鑰 | TPM（實體或韌體做的） | 解 dm-crypt 要一個平台專屬的祕密（[▶ 04:47](https://youtu.be/H_dBnwkTAbw?t=287)） |

- 【口頭】這套他們做過好幾次，運作得很好，「不是火箭科學」，只是要把很多零件湊在一起（[▶ 05:21](https://youtu.be/H_dBnwkTAbw?t=321)）。

---

## 3. Arm 現在的做法與問題

[▶ 05:21](https://youtu.be/H_dBnwkTAbw?t=321)

- 嵌入式 Arm 上常見的是 **U-Boot**。它能做到同樣的事，只是模式不同，**而且需要多很多客製工程**：
  - **每家 SoC 驗早期韌體的方式都不同。**
  - 驗 OS image 通常用**簽章的 FIT**。
  - A/B 切換可以用 U-Boot script 做。【口頭】這次會議好像有另一場講這種做法（[▶ 06:22](https://youtu.be/H_dBnwkTAbw?t=382)）。
  - watchdog 可以在 U-Boot 裡開，這是好事。
  - 拿平台祕密來解密，也要客製。
- 【口頭】做得到，但最理想的是**盡量重用 x86 那套**（[▶ 06:22](https://youtu.be/H_dBnwkTAbw?t=382)）。

---

## 4. 想法：讓 Arm 也走 UEFI

[▶ 06:56](https://youtu.be/H_dBnwkTAbw?t=416)

- Arm 也在往 UEFI 走，例如 **SystemReady** 規範。
- 【口頭】幾年前 Alexander Graf 開始讓 **U-Boot 當 UEFI 提供者**，這是往這個方向的起點之一（[▶ 06:56](https://youtu.be/H_dBnwkTAbw?t=416)）。
- **模式**：只要有一個嵌入式 UEFI 提供者，**它之後的所有東西都可以跟 x86 一樣**（[▶ 07:28](https://youtu.be/H_dBnwkTAbw?t=448)）。
- **平台祕密**：越來越多平台（甚至一些 32 位元的）有 **OP-TEE**，可以用它放平台祕密、管理平台專屬的可信儲存，取代 TPM 這一塊（[▶ 07:58](https://youtu.be/H_dBnwkTAbw?t=478)）。

> ⚠️ 逐字稿缺字：「alex raf」＝Alexander Graf（推測）；「opti」＝OP-TEE。

---

## 5. 誰能提供 UEFI：EDK2 vs U-Boot

[▶ 08:28](https://youtu.be/H_dBnwkTAbw?t=508)

| | EDK2 | U-Boot |
|---|---|---|
| 是什麼 | UEFI 參考實作，x86 韌體很常用，連商用韌體裡都有它的部分 | 嵌入式事實上的標準韌體 |
| Arm 支援 | 有 Arm／Arm64，但**SoC 廠商通常不支援**（少數例外）。拿到的東西不能直接用在你的板子上 | **廠商支援**，BSP 通常就有 |
| driver | 【口頭】上游 driver **很少**，連開 watchdog 這種簡單的事都沒有基礎建設（[▶ 08:58](https://youtu.be/H_dBnwkTAbw?t=538)） | driver 很多，包括啟動協同處理器之類的 |
| UEFI 支援 | 完整 | **已經相當進階**，只是很多人不知道、還沒被廣泛使用（[▶ 10:04](https://youtu.be/H_dBnwkTAbw?t=604)） |

**一個小故事**（[▶ 10:36](https://youtu.be/H_dBnwkTAbw?t=636)）：
- 【口頭】他們出過一塊從 U-Boot 開機的板子，用廠商預設設定，跑傳統的 distro boot（FIT 開機）。
- 後來研究 UEFI 時發現：**UEFI 預設就開著**。把開機流程換成 GRUB EFI，**直接就開起來了**。
- 也就是說，他們**早就在現場出貨支援 UEFI 的系統，自己卻不知道**。
- 那是一個開放平台，沒有關到最少功能，所以照預期運作（[▶ 11:07](https://youtu.be/H_dBnwkTAbw?t=667)）。

---

## 6. 用 U-Boot UEFI 做 secure boot：步驟與強化清單

### 6.1 延續信任鏈

[▶ 11:07](https://youtu.be/H_dBnwkTAbw?t=667)

- **ROM → U-Boot（或中間那段）**：通常還是**廠商專屬**，但廠商通常已經整合好，可以直接用（[▶ 11:37](https://youtu.be/H_dBnwkTAbw?t=697)）。
- **U-Boot 透過 UEFI 載入的東西**，要有信任鏈，兩種做法：

| 做法 | 怎麼做 | 優缺點 |
|---|---|---|
| 靜態 | **把公鑰編進 U-Boot binary** | 最簡單；跟 FIT 的做法一樣。換金鑰要換整個韌體 |
| UEFI 變數 | 把金鑰放在 UEFI 變數，變數放在**安全儲存** | **現場可以更新金鑰**，不用整個換掉韌體。當時還在開發中，有相依條件（[▶ 12:08](https://youtu.be/H_dBnwkTAbw?t=728)） |

### 6.2 強化清單

[▶ 12:38](https://youtu.be/H_dBnwkTAbw?t=758)

【口頭】他們沒看過有人把這些整理成一份，這是幾年實作累積的清單。很多項不只適用 UEFI secure boot：

1. **開機流程不能互動**：鎖住所有跟 bootloader 互動的方式。互動通常就是做非安全開機的入口。
2. **只允許 UEFI 開機**（[▶ 13:15](https://youtu.be/H_dBnwkTAbw?t=795)）：留著 legacy boot，通常就等於可以不經驗證開機，除非那條路也特別處理過。決定走哪條，其他都關掉。
3. **關掉用不到的功能**：
   - **特別是檔案系統**。攻擊者可以換掉儲存（實體攻擊的一種），放一個特製的檔案系統。U-Boot 對那種不常用的檔案系統的實作可能有 bug，**就是開了一扇門**（[▶ 13:45](https://youtu.be/H_dBnwkTAbw?t=825)）。
   - 這個階段不用網路開機的話，**網路也關掉**。
4. **環境變數**：
   - 環境變數裡的值可能被拿來改變開機方式。
   - 要嘛整個**唯讀**；要嘛只讓**少數指定的變數可寫**，其他都不行。U-Boot 現在有這種機制，他們這幾年有參與（[▶ 14:17](https://youtu.be/H_dBnwkTAbw?t=857)）。
5. 範例：isar-cip-core 裡有通用的（但不是完全安全的）設定；Siemens IOT2050（TI 處理器）有實際範例。

### 6.3 簽、鎖、watchdog、測試

[▶ 14:49](https://youtu.be/H_dBnwkTAbw?t=889)

- **簽韌體、鎖住**：用廠商專屬的機制。
- **一定要開 watchdog**：
  - 在 **U-Boot 裡**開，Linux 起來後接手。
  - 【口頭】不在 U-Boot 開、等到更後面才開，中間就會有一段「黑洞」。
- **測試，不要盲信**（[▶ 15:19](https://youtu.be/H_dBnwkTAbw?t=919)）：
  - 【口頭】U-Boot 的 UEFI secure boot 還很新。他們最近測試時**真的找到一個 bug**，現在已經修了，用最新版就有。
  - 系統測試要密集檢查這一層有沒有剩下的安全漏洞。

---

## 7. UEFI payload：EFI Boot Guard 與 UKI 的坑

[▶ 15:51](https://youtu.be/H_dBnwkTAbw?t=951)

**EFI Boot Guard**：U-Boot 之後跑的 UEFI payload，就是他們的 A/B bootloader。Arm／Arm64 版很容易就能 build。

### 7.1 坑一：objcopy 做不出 Arm 的 UKI

[▶ 16:22](https://youtu.be/H_dBnwkTAbw?t=982)

- x86 上用 systemd 的做法：一個小 stub，加上 kernel、initrd、cmdline，Arm 上再加 **DTB**，用 `objcopy` 拼成 UKI。
- UKI 同時是 PE binary（Windows 格式）、ELF、UEFI binary。
- **一般 toolchain／發行版給的 `objcopy` 還不支援**（[▶ 16:52](https://youtu.be/H_dBnwkTAbw?t=1012)）。
  - Yocto 可以用最新 toolchain 繞過；用發行版當 build 系統的話就麻煩。
  - 他們的解法：自己用 **Python** 寫 UKI 產生器，拼出 PE 的各個 section（[▶ 18:27](https://youtu.be/H_dBnwkTAbw?t=1107)）。

### 7.2 坑二：一個 UKI 只能放一個 DTB

[▶ 16:52](https://youtu.be/H_dBnwkTAbw?t=1012)

- 理想上（SystemReady 模式），DTB 由韌體提供，完整描述裝置。
- **現實**：裝置在現場很多年，可能一開始用 BSP kernel、後來換 mainline kernel；一開始用非官方的 DT binding、後來換成官方的。所以**要規劃 kernel 和 DTB 綁在一起**（[▶ 17:24](https://youtu.be/H_dBnwkTAbw?t=1044)）。
  - 【口頭】這種綁法「不流行，但在可見的未來還避免不了」。
- 一個裝置一個 DTB 沒問題。但**一個 image 要涵蓋幾種小差異的板子**時，就需要多個 DTB（[▶ 17:57](https://youtu.be/H_dBnwkTAbw?t=1077)）。
- **解法**：
  - UKI 裡放**多個 DTB**。
  - 開機時挑一個**跟韌體原本提供的 DTB 相符**的（[▶ 18:27](https://youtu.be/H_dBnwkTAbw?t=1107)）。
  - 以後也會送到 systemd-boot。
- **前提**：韌體要能把它動態加進 DTB 的資訊（例如記憶體大小）傳下去 → **EFI DT fixup protocol**（[▶ 18:59](https://youtu.be/H_dBnwkTAbw?t=1139)）。
  - U-Boot 有實作，systemd-boot、EFI Boot Guard 都支援。
  - **EDK2 還不支援**。正在努力加進 EBBR 規範。

> ⚠️ 逐字稿缺字：「EVBR」推測是 EBBR（Embedded Base Boot Requirements）。

---

## 8. OS 這半邊：A/B 更新

[▶ 20:00](https://youtu.be/H_dBnwkTAbw?t=1200)（換 Christian 講）

- **UEFI 這一段現在是跨架構通用的**：同樣的元件部署到不同架構，最多改一點設定（例如開不開 watchdog）。
- 接下來講三件事：UKI 怎麼找到並掛載 rootfs、怎麼加完整性保護、韌體更新。

**A/B 方案**（[▶ 20:34](https://youtu.be/H_dBnwkTAbw?t=1234)）：
1. 有兩份 rootfs，一份是目前開機用的。
2. 執行中更新**另一份**。
3. 試開新的那份：
   - 開成功 → 變成預設。
   - 失敗 → **回滾**到原本那份，繼續跑或回報後台（[▶ 21:08](https://youtu.be/H_dBnwkTAbw?t=1268)）。

- 這需要 bootloader 深度配合：**開硬體 watchdog**、A/B 切換。
  - 【口頭】例如把 x86 kernel 裝到 Arm 系統上，根本開不起來，**只能靠 watchdog** 救（[▶ 21:39](https://youtu.be/H_dBnwkTAbw?t=1299)）。
- 用 **SWUpdate** 的流程，已經預先整合在 CIP core 裡。
- 【口頭】有了這條通道，也可以拿來更新套件、container image 等，不只韌體（[▶ 22:10](https://youtu.be/H_dBnwkTAbw?t=1330)）。

---

## 9. UKI 怎麼找到自己的 rootfs

[▶ 22:40](https://youtu.be/H_dBnwkTAbw?t=1360)

**前提**：kernel 和它的 rootfs 是**一包**。某個 kernel 屬於 A 或 B 其中一份 rootfs。

**為什麼不能直接寫 `root=/dev/...`**：
1. **A/B 時你不知道**現場那台現在走哪條路，除非去問它（[▶ 23:10](https://youtu.be/H_dBnwkTAbw?t=1390)）。所以要跟 A/B 無關。
2. **secure boot 時，不能把不可信的資訊餵進開機鏈**，所以不能依賴放在某處的設定檔。

**選項**：

| 做法 | 問題 |
|---|---|
| 檔案系統 UUID：initramfs 掃磁碟，找跟 kernel 相符的 UUID | 不是每種檔案系統都支援 |
| 分區 UUID | 也不一定有；而且**每次更新都要寫分割表**，應該避免（[▶ 23:40](https://youtu.be/H_dBnwkTAbw?t=1420)） |
| **他們的做法**：在 rootfs 的 `/etc/os-release` 加自訂標籤 **`IMAGE_UUID`** | 見下 |

**他們的做法**（[▶ 23:40](https://youtu.be/H_dBnwkTAbw?t=1420)）：
1. 同一個 UUID 也刻在 UKI 的 initrd 裡。
2. initrd 逐一掛載每個檔案系統，看 `/etc/os-release` 的 UUID 跟自己的對不對得上。
3. 對上了，就是自己的 rootfs，繼續開機。
4. **UUID 在 UKI 裡，所以被 secure boot 保護**（[▶ 24:12](https://youtu.be/H_dBnwkTAbw?t=1452)）。

**什麼情況會被繞過**（[▶ 24:44](https://youtu.be/H_dBnwkTAbw?t=1484)）：
- 只靠 UUID，**rootfs 本身沒被保護**。
- 攻擊者只要保留 `os-release` 裡的那個 UUID，**其他想怎麼改都可以**，照樣開得起來。
- → 需要第 10 節。

> ⚠️ 逐字稿缺字：「ETCOS release／EDCOS release」＝`/etc/os-release`。

---

## 10. 加上 dm-verity

[▶ 24:44](https://youtu.be/H_dBnwkTAbw?t=1484)

需要：**強制驗證真實性**，而且 rootfs 很可能要**唯讀**。

**dm-verity**（[▶ 25:15](https://youtu.be/H_dBnwkTAbw?t=1515)）：
- device mapper 疊在 block 裝置上，用 Merkle tree 保護完整性。
- 底層任何改動都會一路傳到最上面，**root hash 就不一樣了**。

**整合方式**：
1. build 時算出 rootfs 的 **root hash**，放進 initrd，initrd 放進 UKI（所以被簽）。
2. 開機時掃磁碟，讀每個 dm-verity 裝置的 **metadata**，找 root hash 跟 UKI 裡相符的那個（[▶ 25:46](https://youtu.be/H_dBnwkTAbw?t=1546)）。
3. **好處**：不用一個個掛載檔案系統，讀 metadata 就知道。

- **root hash 本身就可以當 UUID**，取代上一節的 `IMAGE_UUID`。這是 Q&A 裡講的「捷徑」（見第 12 節）。

---

## 11. 上游與參考實作：isar-cip-core

[▶ 26:16](https://youtu.be/H_dBnwkTAbw?t=1576)

- 要對齊的東西很多。【口頭】不是火箭科學，但要把零件排好。
- **送上游 = 把大家共享的大圖寫成程式碼**，不讓它變成部落知識（tribal knowledge）（[▶ 26:47](https://youtu.be/H_dBnwkTAbw?t=1607)）。
- 這些剛好碰到 CIP 很多工作組的核心，所以先送到 **CIP 的 isar-cip-core**。
  - 用 Isar 做的，但 script、設定可以照搬到 Yocto 等其他 build 系統（[▶ 27:17](https://youtu.be/H_dBnwkTAbw?t=1637)）。
- **還沒完全整合的**：secure boot 的**技術面**有了，**流程面**（金鑰管理等）沒有，要接到你公司自己的流程（[▶ 27:49](https://youtu.be/H_dBnwkTAbw?t=1669)）。
- 有 QEMU demo（所有架構）和一個實體板子。
- **meta-iot2050**（Siemens SIMATIC IOT2050 的 layer）：跟 isar-cip-core 的差異，就是「拿一台新設備做成最終產品要多少工」的例子（[▶ 28:19](https://youtu.be/H_dBnwkTAbw?t=1699)）。

**總結**（[▶ 28:52](https://youtu.be/H_dBnwkTAbw?t=1732)）：
- 【口頭】secure boot 加韌體更新不是火箭科學，但「可能不適合拿來過一個輕鬆的星期五，除非你想毀了週末」。
- 大部分零件都是開源的，只是要找到、驗證、排好。
- 更重要的是**測試和長期維護**：不是一次性的範例，而是長期測試、維護的東西（[▶ 29:26](https://youtu.be/H_dBnwkTAbw?t=1766)）。

---

## 12. Q&A

【Q&A】**Q：（關於「slide 13」，問題聽不清，從答案看是問 UUID 和 root hash 的關係）**（[▶ 29:26](https://youtu.be/H_dBnwkTAbw?t=1766)）
- 自訂的 UUID 是隨機產生的。開機時逐一掛載檔案系統找它（[▶ 30:03](https://youtu.be/H_dBnwkTAbw?t=1803)）。
- **root hash 本身就像一個 UUID**。用它就不用打開 dm-verity 裝置、掛載、看 `os-release`，直接讀 metadata，是捷徑（[▶ 30:39](https://youtu.be/H_dBnwkTAbw?t=1839)）。
- 也可以用 UUID 配 dm-verity，但那樣要打開 block 裝置：root hash 對不上就打不開，再試下一個。

【Q&A】**Q：每個分區都掛載一次要多久？**（[▶ 30:39](https://youtu.be/H_dBnwkTAbw?t=1839)）
- 不久。講者說可以算是「過早最佳化」（[▶ 31:15](https://youtu.be/H_dBnwkTAbw?t=1875)）。

【Q&A】**Q：bootloader 怎麼更新？**（[▶ 31:15](https://youtu.be/H_dBnwkTAbw?t=1875)）
- bootloader 只是 ESP 上的一個 EFI binary，可以用 SWUpdate 換檔案。
- 但這是**敏感操作**：弄壞 bootloader 就沒救了。
- **bootloader 本身沒有 A/B**（[▶ 31:45](https://youtu.be/H_dBnwkTAbw?t=1905)）：
  - 一定有一個不動的核心 bootloader。上面可以再 chain boot，例如放兩個 EFI Boot Guard。
  - 但更新那個核心還是問題，**放兩個也解決不了：永遠有一個單一失效點**。
  - 除非 UEFI 韌體支援兩個 ESP 之類的。有這種方案，但不是一般情況，也不是一般廠商會賣你的（[▶ 32:19](https://youtu.be/H_dBnwkTAbw?t=1939)）。

【Q&A】**Q：為什麼不更新 GPT？GPT 本來就有兩份。**（[▶ 32:19](https://youtu.be/H_dBnwkTAbw?t=1939)）
- 寫入新的分區 image 可能帶來新的 UUID，要讓 GPT 認得就得改 GPT（看實作）。**這樣不好。**
- 而且不是每個 block 裝置都用 GPT。
- 提問者：GPT 有兩份，算是 A/B。
- 講者：有兩份，能用就好；但如果把分割表弄壞了，系統就掛了。**最好別碰**（[▶ 32:51](https://youtu.be/H_dBnwkTAbw?t=1971)）。
- **原則**：EFI Boot Guard 也有兩個分區放設定。**無論如何都不動目前已知能開的那條路**，永遠寫另一份。依這個原則，GPT 這種單一失效點也不該碰（[▶ 33:27](https://youtu.be/H_dBnwkTAbw?t=2007)）。

【Q&A】**Q：（聽不清，從答案看是問 A/B 狀態為什麼不放 UEFI 變數）**（[▶ 33:59](https://youtu.be/H_dBnwkTAbw?t=2039)）
- 他們想過像 systemd-boot 那樣用 UEFI 變數放設定。
- 最後沒這樣做：**不知道 UEFI 變數背後的儲存有多可靠**。放在磁碟上，磁碟壞了反正也全壞了，**不要依賴你控制不了的東西**（[▶ 34:37](https://youtu.be/H_dBnwkTAbw?t=2077)）。

【Q&A】**Q：一個刻意設計的例子：更新只改了 DTB，root hash 一樣，兩份 image 的 root hash 相同，怎麼辦？**（[▶ 34:37](https://youtu.be/H_dBnwkTAbw?t=2077)）
- root hash 一樣，兩份都可用。
- 看更新流程怎麼接：例如更新了 kernel B，它掃磁碟時可能找到 rootfs A，而不是它應該用的 B（[▶ 35:12](https://youtu.be/H_dBnwkTAbw?t=2112)）。這可能是個問題，看你怎麼設計。
- 但**就完整性保護來說沒差**：root hash 相同，兩個分區都是合法的。

【Q&A】**Q：UKI 不支援多個 DTB，為什麼不用 FIT image？**（[▶ 35:46](https://youtu.be/H_dBnwkTAbw?t=2146)）
- 那就**離開 UEFI 這個領域**，回到傳統開機鏈了。可以，FIT 也有這種機制，但不是目標。
- 目標是 UEFI 這一側全部一樣，甚至往 RISC-V 延伸，把它標準化（[▶ 36:16](https://youtu.be/H_dBnwkTAbw?t=2176)）。
- 【口頭】代價是：不做那種「一秒以內開機」的最佳化，有一定的複雜度。但在他們的領域這不是主要考量。他們要的是**更普及、更穩健、更統一**，而不是更最佳化。

【Q&A】**Q：（聽不清，從答案看是問能不能換掉 SWUpdate）**（[▶ 36:51](https://youtu.be/H_dBnwkTAbw?t=2211)）
- 這套機制跟 update agent 無關，例如 RAUC 也行，只要實作出來。
- 要做的是：update agent 跟 bootloader 溝通（開 watchdog、A/B 切換）。SWUpdate 已經整合好；其他甚至專屬的 update agent 也可以，自己實作那些功能就好（[▶ 37:27](https://youtu.be/H_dBnwkTAbw?t=2247)）。

【Q&A】**Q：多個 DTB 的 UKI 具體怎麼運作？**（[▶ 37:59](https://youtu.be/H_dBnwkTAbw?t=2279)）
- UKI 的 header stub 是一個 UEFI binary：找出 binary 裡有哪些東西（kernel、initrd、幾個 DTB），挑出相符的 DTB，用傳統方式開機（[▶ 38:30](https://youtu.be/H_dBnwkTAbw?t=2310)）。
- 這一步已經在 UEFI 領域之外了。但整個 UKI 是一個 UEFI binary，所以**韌體會驗整個 binary 是否完整**。

【Q&A】**Q：（聽不清，從答案看是建議把東西都放進 kernel）**（[▶ 38:30](https://youtu.be/H_dBnwkTAbw?t=2310)）
- 有這種機制，也許可以往那個方向演進，但不確定 kernel command line 要怎麼處理（[▶ 39:16](https://youtu.be/H_dBnwkTAbw?t=2356)）。
- 這不是唯一的路，只是他們現在實際選的一條。很樂意以後從鏈裡拿掉東西，例如 EFI Boot Guard 被取代的話就丟掉。
- **想拿掉 EFI Boot Guard 的條件**（[▶ 39:46](https://youtu.be/H_dBnwkTAbw?t=2386)）：
  - A/B 切換邏輯如果寫進 UEFI 規範，韌體就能做。
  - watchdog：現在用硬體 watchdog。UEFI 有一個軟體 watchdog（其實只是 timer）。如果規範納入硬體 watchdog，每個系統都有，他們就能丟掉 EFI Boot Guard。
  - 也可以寫 DXE（UEFI driver）來做，但那通常跟某塊板子的 UEFI 實作綁在一起。所以現在交給 EFI Boot Guard，**只是過渡**（[▶ 40:20](https://youtu.be/H_dBnwkTAbw?t=2420)）。

【Q&A】**Q：（聽不清，從答案看是問 dm-crypt 那部分）**（[▶ 40:52](https://youtu.be/H_dBnwkTAbw?t=2452)）
- 內部有，**還沒公開**，之後一定會有。
- 難的不是技術，是**流程**：怎麼把簽章、金鑰管理接進來，又做成別人能重用的範本，不把自己的做法強加給全世界（[▶ 41:22](https://youtu.be/H_dBnwkTAbw?t=2482)）。

---

## 13. 一頁速查表

**整條鏈（Arm 版）**

```
ROM ─廠商專屬→ U-Boot（UEFI 提供者；公鑰編進 binary 或放在安全的 UEFI 變數）
  └UEFI secure boot→ EFI Boot Guard（A/B、開 watchdog）
       └→ UKI（kernel＋cmdline＋initrd＋多個 DTB；initrd 內含 IMAGE_UUID 或 root hash）
            └initrd 掃磁碟：找 root hash 相符的 dm-verity 裝置 → rootfs
            └（可寫部分：dm-crypt，金鑰來自 TPM／OP-TEE，尚未公開）
```

**U-Boot 強化清單**：不能互動｜只開 UEFI｜關掉不用的檔案系統和網路｜環境唯讀或只放行少數變數｜在 U-Boot 開 watchdog｜實際測試。

| 問題 | 答案 |
|---|---|
| 為什麼要 UKI？ | 只簽 kernel 的話，initrd、cmdline 沒被保護 |
| 為什麼不用 `root=/dev/...`？ | A/B 不知道現在走哪條；不能把不可信的設定餵進開機鏈 |
| 只靠 UUID 會被怎麼繞過？ | 保留 UUID、其他亂改 → 要 dm-verity |
| 為什麼不改 GPT？ | 單一失效點；永遠不碰已知能開的那條路 |
| bootloader 能 A/B 嗎？ | 一般情況不行，永遠有一個單一失效點 |
| Arm UKI 的兩個坑？ | objcopy 不支援（自己用 Python 做）；只能一個 DTB（放多個、靠 DT fixup protocol 挑） |

---

## 14. 延伸連結

- MT8189 上的 dm-verity＋內建 initramfs、dm-crypt：[`../verified-boot-notes/verity-boot.md`](../verified-boot-notes/verity-boot.md)、[`../verified-boot-notes/dm-crypt.md`](../verified-boot-notes/dm-crypt.md)
- MT8189 的 A/B 選邊在 `misc`、U-Boot `setenv verify n` 的洞：[`../verified-boot-notes/fit-sign.md`](../verified-boot-notes/fit-sign.md)
- OP-TEE（平台祕密）：[`../tf-a-and-op-tee-note/optee-intro.md`](../tf-a-and-op-tee-note/optee-intro.md)

---

## 附：一句話總結

> **讓 U-Boot 當 UEFI 提供者，Arm 就能沿用 x86 那套：U-Boot 驗 EFI Boot Guard（A/B＋watchdog），Boot Guard 驗 UKI，UKI 用簽進去的 root hash 找到並驗證自己的 dm-verity rootfs。前提是把 U-Boot 鎖死，並解決 Arm UKI 的 objcopy 和多 DTB 問題。**

---

## ⚠️ 待確認清單

1. 會議名稱：只知道是 Linux Foundation 頻道 2022-10-08 上傳，講者說兩年前講過（ELC 2020）。沒有投影片或議程頁可對照。

---

*筆記依據 Jan Kiszka、Christian Storm〈Implementing UEFI-based Secure Boot + OTA Update for Embedded ARM Devices〉錄影整理（Whisper `turbo` 轉錄，41:52）。沒有投影片。*
