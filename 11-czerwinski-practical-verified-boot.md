---
talk: Practical Application of Verified Boot
speaker: Rouven Czerwinski（Pengutronix e.K.）
conference: Open Source Summit Europe 2024（sched 議程 osseu2024 有此場）
year: 2024
video: https://youtu.be/6rGKI5KblZ4
slides: 待補（sched 擋自動抓取，找不到官方投影片；講者說投影片裡有 GitHub 整合範例連結）
---

# Practical Application of Verified Boot [▶ 影片](https://youtu.be/6rGKI5KblZ4)

> **演講**：Rouven Czerwinski（Pengutronix），Open Source Summit Europe 2024，Linux Foundation 頻道 2024-10-04 上傳。
> **來源**：YouTube 錄影（42:02）用 Whisper `turbo` 轉成逐字稿，再加上影片說明欄（官方摘要）。**沒有投影片**，講者指著圖說的地方（信任鏈圖、HSM 外型、Yocto 設定範例）都看不到。
> **標記說明**：`【口頭】` 這場沒有投影片，正文幾乎全是口頭，只標實務經驗和意見。`【說明欄補充】` 是影片說明欄有、演講沒細講的。`【Q&A】` 是現場提問。`⚠️ 逐字稿缺字` 是 Whisper 聽錯。`⚠️ 待確認` 是查不清楚的地方。
> **重點**：這場的技術內容不多，主要是**一個真實專案的教訓**：文件、交接、金鑰管理、生產、客退品、GPLv3。

---

## 目錄

- [0. 這場演講要做什麼](#0-這場演講要做什麼)
- [1. 為什麼叫 verified boot：x86 vs Arm](#1-為什麼叫-verified-bootx86-vs-arm)
- [2. 故事：一個 i.MX6UL 專案的興衰](#2-故事一個-imx6ul-專案的興衰)
- [3. PKCS#11 與 HSM](#3-pkcs11-與-hsm)
- [4. 教訓一：專案知識、交接、誰做決定](#4-教訓一專案知識交接誰做決定)
- [5. 教訓二：開發用 bootloader 怎麼簽](#5-教訓二開發用-bootloader-怎麼簽)
- [6. 教訓三：生產與佈建](#6-教訓三生產與佈建)
- [7. 教訓四：要寫下來的文件](#7-教訓四要寫下來的文件)
- [8. GPLv3 的 Tivoization 條款](#8-gplv3-的-tivoization-條款)
- [9. 客退品（field return）：NXP 的做法](#9-客退品field-returnnxp-的做法)
- [10. Yocto 整合：signing.bbclass](#10-yocto-整合signingbbclass)
- [11. 結論](#11-結論)
- [12. Q&A](#12-qa)
- [13. 一頁速查表](#13-一頁速查表)
- [14. 延伸連結](#14-延伸連結)

---

## 0. 這場演講要做什麼

[▶ 00:31](https://youtu.be/6rGKI5KblZ4?t=31)

- 講者背景：Pengutronix 嵌入式 Linux 顧問。從測試起家，後來做 OP-TEE 和安全好幾年，也做系統整合。
- 【口頭】開場梗：「One does not simply implement verified boot」（魔戒的波羅莫）。
  - 大家以為很簡單：找承包商說「我們要 verified boot」。
  - 【口頭】現在常見的理由是**歐盟 Cyber Resilience Act**。
  - 但一點都不簡單，這場要說明為什麼。

【說明欄補充】摘要還說會講：用 Yocto 的 `signing.bbclass` 搭配 NXP CST 簽 bootloader；用一個「將要上游」的 fitimage class 驗 kernel；用 dm-verity class 範例驗檔案系統；部署鎖死系統的常見陷阱；在鎖死裝置上用 GPLv3。演講中 fitimage class 和 dm-verity class 只帶過（見第 10 節）。

---

## 1. 為什麼叫 verified boot：x86 vs Arm

### 1.1 用詞

[▶ 01:01](https://youtu.be/6rGKI5KblZ4?t=61)

- 「secure boot」這個詞已經被 x86 用掉了（筆電上的 UEFI secure boot）。
- Arm 上每家廠商各做各的：
  - NXP：舊 SoC 是 **HAB**，新的 i.MX9 是 **AHAB**（HAB 的延伸）。
  - Rockchip：要 NDA，【口頭】連名字都找不到。
  - TI：也叫「Secure Boot」，但跟 x86 那個完全無關。
- 所以他用 **verified boot** 泛指各家實作（[▶ 02:04](https://youtu.be/6rGKI5KblZ4?t=124)）。

### 1.2 x86 secure boot

[▶ 02:04](https://youtu.be/6rGKI5KblZ4?t=124)

- ROM 實作先驗 UEFI：Intel 叫 **Boot Guard**，AMD 也有對應的擴充。
  > ⚠️ 逐字稿缺字：AMD 那個 Whisper 聽成「guard me」，原字不確定。⚠️ 待確認
- UEFI 再驗 kernel，kernel 驗檔案系統。
- 有自己的 CA。Linux 上用 **`sbctl`** 把自己的憑證裝進 UEFI（[▶ 02:37](https://youtu.be/6rGKI5KblZ4?t=157)）。
  > ⚠️ 逐字稿缺字：「SPCTL」＝sbctl。
- 授權問題和複雜度一樣存在，但**至少所有 x86 平台是統一的**。
- **一定要設 UEFI 密碼**：沒有密碼的話，任何人都能把裝好的憑證刪掉，BIOS 就什麼都開了（[▶ 03:11](https://youtu.be/6rGKI5KblZ4?t=191)）。

### 1.3 Arm verified boot

[▶ 03:42](https://youtu.be/6rGKI5KblZ4?t=222)

- 也是 ROM code（廠商實作，可能要 NDA）。
- bootloader 不一定只有 U-Boot：可能包含 TF-A，也可能是 barebox 或 Linux 開機系統。**ROM 要驗 bootloader**。
- U-Boot 和 barebox 的標準做法：用 **FIT image** 驗 kernel、DTB、initramfs（[▶ 04:13](https://youtu.be/6rGKI5KblZ4?t=253)）。

**fuse**（[▶ 04:13](https://youtu.be/6rGKI5KblZ4?t=253)）：
- 幾乎所有廠商實作都要燒 fuse。fuse 燒了變 1，**永遠回不去 0**。
- NXP：先建 CA（最上面是 root 憑證），算憑證的雜湊，燒進 SoC（[▶ 04:43](https://youtu.be/6rGKI5KblZ4?t=283)）。
- **一次性操作，非常重要**：
  - 燒錯 fuse 會讓板子**徹底變磚**。
  - 如果連 NXP 那個**鎖定 fuse** 也燒了，就**沒辦法用別的軟體救回來**（[▶ 05:13](https://youtu.be/6rGKI5KblZ4?t=313)）。
- **不能在現場換憑證**。對照 x86：只要有 UEFI 密碼，理論上可以到現場換掉憑證（很貴，但做得到）。

---

## 2. 故事：一個 i.MX6UL 專案的興衰

[▶ 05:43](https://youtu.be/6rGKI5KblZ4?t=343)

### 2.1 2019～2021：做好了

平台：NXP i.MX6UL，用 HAB。

| 元件 | 用途 |
|---|---|
| HAB | ROM 驗 bootloader |
| **OP-TEE** | 存雲端認證資訊（雲端後台要裝置提供認證） |
| **AppArmor** | 多一層：控制 user space 程式能存取什麼（[▶ 06:14](https://youtu.be/6rGKI5KblZ4?t=374)） |
| **RAUC** | 更新 |
| Yocto | 整個系統在 Yocto 裡 build，保證 image 一定能開機 |
| **Nitrokey HSM** | 存簽章金鑰 |

**信任鏈**（[▶ 06:45](https://youtu.be/6rGKI5KblZ4?t=405)）：

```
ROM ─驗→ bootloader（內含 OP-TEE）
           ├載入 OP-TEE（TrustZone secure world），再回到 bootloader
           └驗→ FIT（DTB＋initramfs＋kernel）
                 └kernel 用 dm-verity 驗 rootfs
```

### 2.2 2022～2023：人都走了

[▶ 07:20](https://youtu.be/6rGKI5KblZ4?t=440)

1. 2022 年：客戶團隊不存在了。成員因外部或專案壓力陸續離職，最後**整個據點被賣給另一家公司**。
2. Yocto 停在 2021 年他們最後碰的狀態（[▶ 07:52](https://youtu.be/6rGKI5KblZ4?t=472)）。
3. 他們問客戶要不要繼續開發、更新 Yocto、寫開機文件……**沒人回**。專案負責人跟著據點一起被賣掉了。
4. 2023 年底：**一個全新的團隊**出現，問：「verified boot、HSM、PKCS#11，這些是什麼？我們看不懂，能解釋嗎？」（[▶ 07:52](https://youtu.be/6rGKI5KblZ4?t=472)）

### 2.3 新團隊的需求

[▶ 11:05](https://youtu.be/6rGKI5KblZ4?t=665)

- 他們發現必須更新 2021 年出貨的軟體，因為「到處都是漏洞」。
- **想把 USB HSM 換成雲端 HSM**（[▶ 11:39](https://youtu.be/6rGKI5KblZ4?t=699)）：
  - 很棘手：現場裝置依賴的金鑰在硬體 HSM 裡，**不能匯出**。
  - 【口頭】「怎麼匯出？就是不可能。我們試著解釋，他們很難理解為什麼。」
- 有 **SBOM**（軟體物料清單）需求 → 必須更新 Yocto。
- 「順便問一下，這些東西到底怎麼搭在一起的？能再解釋一次嗎？」

---

## 3. PKCS#11 與 HSM

[▶ 08:30](https://youtu.be/6rGKI5KblZ4?t=510)

**PKCS#11**：硬體安全模組（HSM）的標準程式介面。
- 通常用法：在 HSM 上產生非對稱金鑰對，**私鑰在裝置上產生、永遠不能匯出**。
- 想法：能簽軟體的那個重要裝置，簽完就從電腦拔下來**鎖進保險箱**（[▶ 09:00](https://youtu.be/6rGKI5KblZ4?t=540)）。

**軟體支援很廣**（[▶ 09:00](https://youtu.be/6rGKI5KblZ4?t=540)）：
- Chromium、nginx、SSH、wpa_supplicant 等。
- OpenSSL、GnuTLS 也能用。
- **OpenSSL 3 的 provider 介面**比舊的（已棄用的）engine 介面好很多：私鑰不放檔案，改寫一個 **PKCS#11 URI**，指向裝置和裝置裡的某把金鑰（[▶ 09:34](https://youtu.be/6rGKI5KblZ4?t=574)）。
- 【口頭】他們當年還在用舊的 engine 介面。

**HSM 外型**（[▶ 10:04](https://youtu.be/6rGKI5KblZ4?t=604)）：

| 外型 | 用法 |
|---|---|
| PCIe 卡 | 插在安全的伺服器裡；在卡上產生金鑰，用管理軟體做遠端智慧卡認證 |
| USB（YubiKey、Nitrokey HSM） | 最簡單。拔下來鎖保險箱。要有一套程序：誰知道怎麼開保險箱、拿出來、build、簽、交付（[▶ 10:34](https://youtu.be/6rGKI5KblZ4?t=634)） |
| 機架式 | 上百萬台裝置的大專案。放在安全的資料中心，透過網路把要簽的東西送過去，簽好送回來 |

---

## 4. 教訓一：專案知識、交接、誰做決定

### 4.1 鎖死的系統，沒有文件就打不開

[▶ 12:15](https://youtu.be/6rGKI5KblZ4?t=735)

- 【口頭】給他一台**沒有** verified boot 的嵌入式 Linux，他大概能搞懂：開機、進 bootloader、加 `init=/bin/bash`，就拿到 root shell。
- 但**故意設計成封閉的系統**非常難（[▶ 12:45](https://youtu.be/6rGKI5KblZ4?t=765)）：
  - 有時連 bring-up 都不行。
  - 你手上這台是什麼？用 release 金鑰簽的量產機，還是用開發金鑰的開發機？要用哪把金鑰？怎麼更新？有沒有更新 daemon？
  - 能進 console 就算好運了。**有些裝置連開發用的都鎖得進不去**（為了測 release 設定），而且**沒人寫下「這台已經燒死、不能再用」**（[▶ 13:20](https://youtu.be/6rGKI5KblZ4?t=800)）。
  - bootloader 鎖住、不能改設定、不能 `init=/bin/bash`、不能換 kernel。可能有 log 給人診斷，但什麼都不能改。

**最低限度**（[▶ 13:50](https://youtu.be/6rGKI5KblZ4?t=830)）：
- 一定要辦**交接工作坊**，寫下能做什麼、哪些裝置還能用。不然你的裝置就再也進不去了。
- 更好：安排**交接期**，讓舊團隊在離開前回答問題、教新人怎麼存取這些裝置。

### 4.2 承包商不能替你做的決定

[▶ 14:21](https://youtu.be/6rGKI5KblZ4?t=861)

- 客戶常以為：「承包商會做好，我們只要說要 secure boot。」
- 承包商能做的：簽 bootloader 的程序、驗 FIT、做簽好的 image、驗檔案系統。
- **專案的技術決定要由裝置廠商自己做**（[▶ 14:53](https://youtu.be/6rGKI5KblZ4?t=893)）：
  - 承包商常常不清楚產品會怎麼被用。
  - 【口頭】很多人想做「平台」而不是特定用途的裝置，公司內部有 4、5、6、10 個利害關係人想拿它做不同的事。
  - 專案總有一天會進入支援階段，承包商不再深入參與（[▶ 15:27](https://youtu.be/6rGKI5KblZ4?t=927)）。
- **金鑰管理也不能交給承包商**：軟體要在**你的**基礎設施裡簽，裝置要在**你的**基礎設施裡燒 fuse（[▶ 16:00](https://youtu.be/6rGKI5KblZ4?t=960)）。

---

## 5. 教訓二：開發用 bootloader 怎麼簽

[▶ 16:00](https://youtu.be/6rGKI5KblZ4?t=960)

開發時需要一個**開放、可重新設定、什麼都能開**的 bootloader（改參數、測東西）。兩種選擇：

| 選擇 | 優點 | 缺點 |
|---|---|---|
| **開發用 bootloader 用 release 金鑰簽** | 客退品回來，直接用開發 bootloader 開機，支援很方便 | **只要有人拿到這個 bootloader，現場所有裝置都可能被攻破**（[▶ 16:31](https://youtu.be/6rGKI5KblZ4?t=991)） |
| **開發用 bootloader 用專門的開發金鑰簽** | 開發金鑰外洩也沒關係（只有 10～20 台開發機，永遠不會出貨），**可以放進 CI build**（[▶ 17:02](https://youtu.be/6rGKI5KblZ4?t=1022)） | 會多出一批「開發機」。要清楚標示，之後每個開發者用新軟體時都要記得用開發金鑰（[▶ 17:35](https://youtu.be/6rGKI5KblZ4?t=1055)） |

**「什麼都簽」的事故**（[▶ 17:35](https://youtu.be/6rGKI5KblZ4?t=1055)）：
- 某專案在 CI 裡也設了 release 裝置的 pipeline。
- 有人 check in 了一個**帶開發選項、完全開放**的 bootloader 設定。
- CI：「合法設定，可以 build。」→ 產出一個**用 release 金鑰簽的、完全開放的 bootloader**。
- 而且因為 CI 在雲端，**它就在網路上了**。他們費了很大功夫把 artifact 刪掉（[▶ 18:09](https://youtu.be/6rGKI5KblZ4?t=1089)）。
- 教訓：有 CI 參與時，用 release 金鑰要**非常非常小心**。

---

## 6. 教訓三：生產與佈建

### 6.1 工廠可信嗎

[▶ 18:09](https://youtu.be/6rGKI5KblZ4?t=1089)

- 【口頭】（Anakin 梗圖）「我們有 verified boot 了。」「但工廠可信嗎？……可信吧？」
- 某專案把生產外包到另一個國家，然後決定「我們不完全信任那間工廠，雖然是自己的」（[▶ 18:45](https://youtu.be/6rGKI5KblZ4?t=1125)）。
- 那就要設計流程：**能在那裡生產板子，但不在那裡佈建（provision）裝置**。
- 否則有人可以在工廠換掉金鑰、模仿你的軟體 → 裝置可能被裝上有害的東西（[▶ 19:17](https://youtu.be/6rGKI5KblZ4?t=1157)）。

### 6.2 佈建步驟

[▶ 19:47](https://youtu.be/6rGKI5KblZ4?t=1187)

在**可信的環境**裡：
1. 把 release 金鑰燒進裝置（fuse）。
2. 測 release 金鑰能正常運作。
3. 順便做其他初始化：
   - OP-TEE 常要跟 eMMC 的 **RPMB** 分區交換金鑰。
   - 也許把 eMMC 設成 **pseudo-SLC** 模式，讓它壽命長一點（[▶ 20:23](https://youtu.be/6rGKI5KblZ4?t=1223)）。
4. **裝置私鑰**（例如雲端認證用）：
   - 可以把私鑰載進裝置。
   - 更好：**在裝置上產生**，私鑰永遠不離開裝置。

- 【口頭】這些都要在可信的環境做，「不然就只能碰運氣了」。

### 6.3 要產生幾把金鑰

[▶ 20:23](https://youtu.be/6rGKI5KblZ4?t=1223)

同樣的問題適用在雲端 API 認證和更新：
- 全部裝置一把？
- 每個硬體版本一把？
- 每批生產一把？
- 每台一把？

取捨：越細，部署越難、但私鑰被攻破時損害越小（[▶ 20:54](https://youtu.be/6rGKI5KblZ4?t=1254)）。**不管選哪個，都要寫下來。**

---

## 7. 教訓四：要寫下來的文件

[▶ 21:26](https://youtu.be/6rGKI5KblZ4?t=1286)

【口頭】常見情況：「我們需要時間寫文件。」「沒關係，之後會有時間。」→ 然後就沒有了。

至少要寫（[▶ 22:02](https://youtu.be/6rGKI5KblZ4?t=1322)）：
1. **release 金鑰怎麼產生、怎麼佈建到裝置上**。有 HSM 產生金鑰的步驟，別人要做另一個產品會容易很多。
2. **怎麼分辨開發機和量產機**：大紅貼紙？線上系統？QR code？選哪個都行，但要想過、寫下來。
3. **客退品怎麼處理**（[▶ 22:32](https://youtu.be/6rGKI5KblZ4?t=1352)）：看你當初開發 bootloader 怎麼簽（第 5 節），可能直接開開發 bootloader，也可能要跑這個 secure boot 實作專屬的客退流程。
4. **定期測試、驗證這些步驟**：兩年前工作坊寫的東西，可能已經不適用現在的軟體（[▶ 23:05](https://youtu.be/6rGKI5KblZ4?t=1385)）。

---

## 8. GPLv3 的 Tivoization 條款

[▶ 23:05](https://youtu.be/6rGKI5KblZ4?t=1385)

- GPLv3 有 **Tivoization 條款**：在裝置上部署 GPLv3 軟體，就要提供「在這台裝置上跑修改版」所需的資訊。
- 最壞的情況：等於要**交出 secure boot 的私鑰**，否則沒人能換裝置上的軟體（[▶ 23:39](https://youtu.be/6rGKI5KblZ4?t=1419)）。

兩種解法：

| 解法 | 評價 |
|---|---|
| **不用任何 GPLv3 軟體** | 【口頭】他覺得還是不好，而且越來越難避免。2019 年那個專案還做得到，現在不確定 |
| **在 bootloader 做「解鎖模式」** | 客戶決定不再用你的基礎設施時，裝置**刪除所有金鑰（或讓它無法存取）**，然後解鎖，讓客戶跑自己的 GPLv3 軟體（[▶ 24:10](https://youtu.be/6rGKI5KblZ4?t=1450)） |

- 【口頭】某場車用演講的例子：你可以把車「弄壞」到不能再用原本的服務，但至少能跑自己的軟體，這是合法的做法（[▶ 24:41](https://youtu.be/6rGKI5KblZ4?t=1481)）。

---

## 9. 客退品（field return）：NXP 的做法

[▶ 24:41](https://youtu.be/6rGKI5KblZ4?t=1481)

- 每家實作不同。【口頭】其他 SoC 的做法他很想知道。
- **NXP**（[▶ 25:14](https://youtu.be/6rGKI5KblZ4?t=1514)）：
  1. 要簽一個 bootloader，裡面**包含那顆 SoC 的 unique ID**。所以客退品回來時，要先知道焊在上面的處理器的 unique ID。
  2. 這個 bootloader 讓裝置**再燒一個 fuse，完全停用 secure boot**。
  3. 之後就能開任何 bootloader。
- 流程複雜，可能要自動化：支援部門不見得會跑整套 Yocto 來簽 bootloader。可以做一個簡單的入口網站：輸入 SoC ID，內部庫存同時標記「這台不能再用」（[▶ 25:50](https://youtu.be/6rGKI5KblZ4?t=1550)）。

（為什麼這不是安全漏洞，見 Q&A。）

---

## 10. Yocto 整合：signing.bbclass

[▶ 25:50](https://youtu.be/6rGKI5KblZ4?t=1550)

- 同事 **Jan Lübbe** 寫的 **`signing.bbclass`**：在 Yocto recipe 裡用 PKCS#11。
  - recipe 裡只要寫要用哪些 **PKCS#11 URI**，build 時在背景存取 HSM（[▶ 26:21](https://youtu.be/6rGKI5KblZ4?t=1581)）。
  - 【口頭】連複雜的 HSM 都很容易整合進 Yocto build。
- **從 Mickledore 起就在 meta-oe**，所以最新 LTS **Scarthgap** 也有。【口頭】「這是更新到最新 LTS 的好理由。」
- 用途：整條鏈都能用，一直到 kernel 驗檔案系統之前：bootloader 簽章、更新簽章、FIT 簽章，全部自動存取 HSM。
- GitHub 上有整合範例（連結在投影片上，看不到）。

**設定的樣子**（[▶ 26:55](https://youtu.be/6rGKI5KblZ4?t=1615)；投影片看不到，以下是口頭描述）：
1. 指定要用哪個 HSM：用序號識別，加一個要用特殊跳脫方式寫的參數，可以帶 PIN，並指向 PKCS#11 C API 的實作函式庫。
2. 設定要用哪些物件（[▶ 27:27](https://youtu.be/6rGKI5KblZ4?t=1647)）：
   - 4 把 **SRK**（Super Root Key，NXP verified boot 用）。
   - CSF（Command Sequence File）金鑰和 image 金鑰。
   - FIT 簽章金鑰、更新簽章金鑰。
- 【口頭】**開發時金鑰可以放在 BSP 裡，不必接外部 HSM；要換成真的 HSM（例如 USB 接在電腦上），只要改這些設定**（[▶ 27:57](https://youtu.be/6rGKI5KblZ4?t=1677)）。

---

## 11. 結論

[▶ 27:57](https://youtu.be/6rGKI5KblZ4?t=1677)

1. **文件、文件、更多文件**：最初做了哪些決定、哪些裝置還能用、怎麼用、怎麼燒錄、怎麼讓 build 系統做出完整 image。
2. **交接流程**：特別是承包商離開或新成員加入時。【口頭】客戶的人常常只待兩三年（[▶ 28:28](https://youtu.be/6rGKI5KblZ4?t=1708)）。
3. **非常小心佈建**。
4. **記住（寫下）客退品怎麼處理**（[▶ 29:04](https://youtu.be/6rGKI5KblZ4?t=1744)）。

---

## 12. Q&A

【Q&A】**Q：NXP 簽章／HSM 存取是指簽給裝置用的資料，還是裝置上用 PKCS#11？**（[▶ 29:45](https://youtu.be/6rGKI5KblZ4?t=1785)）
- **兩者都是**。
- `signing.bbclass` 用接在開發電腦上的外部 HSM 簽給裝置的 artifact。
- 裝置上如果有 OP-TEE，有一個 **PKCS#11 TA**，裝置也能用 PKCS#11 做雲端認證（[▶ 30:20](https://youtu.be/6rGKI5KblZ4?t=1820)）。

**追問：OP-TEE 會連網嗎？**
- 不會。OP-TEE 產生金鑰，幫 Linux user space 簽請求。
- 例如 client 憑證認證：用 OpenSSL 的 PKCS#11 provider，讓軟體不用 rootfs 裡的私鑰，改用 OP-TEE 裡的私鑰。要簽的資料交給 OP-TEE，**OP-TEE 簽，Linux 看不到過程**，再把簽好的資料交回來（[▶ 30:51](https://youtu.be/6rGKI5KblZ4?t=1851)）。

【Q&A】**觀眾提醒：大家常忘了降級攻擊。bootloader 有漏洞、更新了之後，要確定沒人能把有漏洞的舊版裝回去。**（[▶ 30:51](https://youtu.be/6rGKI5KblZ4?t=1851)）
- 講者：沒錯。**目前這套方案沒有 bootloader 的降級保護**。他有想法，但還沒實作（[▶ 31:54](https://youtu.be/6rGKI5KblZ4?t=1914)）。

【Q&A】**Q：GPLv3 不是只要求能部署修改版，裝置不用保固，但要保留功能嗎？**（[▶ 31:54](https://youtu.be/6rGKI5KblZ4?t=1914)）
- 講者不是律師，沒辦法給確定答案。
- 他的理解：**GPL 不要求保留功能**，只要你的軟體能在裝置上跑。但這不是法律建議（[▶ 32:25](https://youtu.be/6rGKI5KblZ4?t=1945)）。

【Q&A】**Q：NXP 可以替客退品停用 HAB，為什麼這不是安全漏洞？**（[▶ 32:55](https://youtu.be/6rGKI5KblZ4?t=1975)）
- 因為要有**私鑰**（得是當初部署軟體的人），**還要有那顆 SoC 的 unique ID**（[▶ 33:28](https://youtu.be/6rGKI5KblZ4?t=2008)）。
- **沒有通用的解鎖 bootloader**：能把裝置轉成「客退、HAB 停用」狀態的 bootloader，必須專為那一台做。

**追問：停用後能再啟用嗎？**
- **不行**（至少 NXP HAB）。停用時要燒一個 fuse，標示「這是客退品」，燒了就永遠回不去（[▶ 33:59](https://youtu.be/6rGKI5KblZ4?t=2039)）。

【Q&A】**Q：PKCS#11 支援撤銷嗎？**（[▶ 33:59](https://youtu.be/6rGKI5KblZ4?t=2039)）
- 據他所知**不支援**。
- PKCS#11 常用在 client 憑證認證，那裡有 CA 架構，可以用憑證撤銷清單（CRL）撤銷；但 PKCS#11 本身沒有（[▶ 34:31](https://youtu.be/6rGKI5KblZ4?t=2071)）。

【Q&A】**Q：build release 時，PKCS#11 那一套怎麼保護？**（[▶ 34:31](https://youtu.be/6rGKI5KblZ4?t=2071)）
- 看你選哪種 HSM（[▶ 35:57](https://youtu.be/6rGKI5KblZ4?t=2157)）。
- 例如 USB HSM：可以用一台**不連網**的電腦，只把需要的原始碼複製過去 build 整套軟體（如果要非常安全的話）。

【Q&A】**Q：CI 是整個開發團隊都能存取的，怎麼讓某些人碰不到金鑰？**（[▶ 36:32](https://youtu.be/6rGKI5KblZ4?t=2192)）
- 講者：**不要讓 CI 簽**。他強烈建議不要，這是很好的緩解（[▶ 37:02](https://youtu.be/6rGKI5KblZ4?t=2222)）。
- 不一定做得到：有人堅持要 CI 能用 release 金鑰。那是開發時別人做的決定，他們也左右不了。

【Q&A】**觀眾補充：FIT 規範現在已經在 U-Boot 之外獨立維護，Linux 也有 build FIT 的目標了。**（[▶ 37:48](https://youtu.be/6rGKI5KblZ4?t=2268)）
- 講者：很好、很有用（[▶ 38:18](https://youtu.be/6rGKI5KblZ4?t=2298)）。

【Q&A】**觀眾：你講的都是 NXP。**（[▶ 38:18](https://youtu.be/6rGKI5KblZ4?t=2298)）
- 講者：他主要做 NXP，Pengutronix 很多專案用 NXP。很想知道 TI，特別是新的 AM62 系列怎麼做（[▶ 38:57](https://youtu.be/6rGKI5KblZ4?t=2337)）。
- 觀眾：看過 TI 的 secure boot 規格，印象是**沒有客退用的「再停用 secure boot」機制**。
- 觀眾補充：TI 這部分**大量是 NDA**（[▶ 39:32](https://youtu.be/6rGKI5KblZ4?t=2372)）。
- 講者：【口頭】做開源軟體的跟 NDA 很衝突。NXP 的流程能公開講，是因為大部分都在開源軟體裡；其他廠商簽了 NDA，連「有沒有簽」都不能說，只能跟同樣簽了的同事討論（[▶ 40:05](https://youtu.be/6rGKI5KblZ4?t=2405)）。
- 另一位觀眾：有 TI EVK，沒簽 NDA，也沒拿到 secure boot 文件（[▶ 40:37](https://youtu.be/6rGKI5KblZ4?t=2437)）。
- 另一位觀眾：Raspberry Pi 的新 **RP2350**（Cortex-M）要公開所有 secure boot 文件。講者：很棒，可惜不適合跑 Linux，希望大顆的 Cortex-A Pi 也能這樣（[▶ 41:08](https://youtu.be/6rGKI5KblZ4?t=2468)）。

---

## 13. 一頁速查表

**技術鏈（這個專案）**：ROM（HAB，fuse 存 CA 憑證雜湊＋鎖定 fuse）→ bootloader（內含 OP-TEE）→ FIT（kernel＋DTB＋initramfs）→ dm-verity rootfs；OP-TEE 存雲端金鑰；AppArmor；RAUC；簽章金鑰在 Nitrokey HSM（PKCS#11）。

**非技術的坑**

| 坑 | 該怎麼做 |
|---|---|
| 團隊離開，沒人知道裝置怎麼開 | 交接工作坊＋交接期；寫下哪些裝置還能用 |
| 想把 HSM 換掉 | HSM 裡的私鑰匯不出來，現場裝置綁著它，換之前要想清楚 |
| 開發 bootloader 用 release 金鑰簽 | 方便客退，但外洩 = 全部裝置淪陷；改用開發金鑰＋標示開發機 |
| CI 能用 release 金鑰 | 會簽出開放的 bootloader 並上網；不要讓 CI 簽 release |
| 工廠不可信 | 生產可以外包，佈建（燒 fuse、產生裝置金鑰）留在可信環境 |
| 幾把金鑰 | 全部一把／每版／每批／每台，取捨後寫下來 |
| GPLv3 | 不用 GPLv3，或做「刪金鑰後解鎖」模式 |
| 客退品 | NXP：簽含 SoC unique ID 的 bootloader，燒 fuse 永久停用 HAB；流程要自動化、要定期驗證 |
| 降級攻擊 | 目前沒保護舊版 bootloader 被裝回去（觀眾提醒） |

---

## 14. 延伸連結

- MT8189 實驗用的是 layer 裡公開的測試金鑰、FIT 私鑰在 meta-rity 公開（正是第 5 節「開發金鑰」的情況）：[`../verified-boot-notes/vb-intro.md`](../verified-boot-notes/vb-intro.md)、[`../verified-boot-notes/fit-sign.md`](../verified-boot-notes/fit-sign.md)
- OP-TEE、RPMB 金鑰交換：[`../tf-a-and-op-tee-note/optee-intro.md`](../tf-a-and-op-tee-note/optee-intro.md)

---

## 附：一句話總結

> **verified boot 的技術鏈（HAB → bootloader＋OP-TEE → FIT → dm-verity）做得出來，難的是之後：裝置鎖死後沒有文件和交接就沒人打得開；金鑰怎麼簽、誰能碰、在哪裡佈建、客退品和 GPLv3 怎麼處理，都必須由裝置廠商自己決定並寫下來。**

---

## ⚠️ 待確認清單

1. [▶ 02:04](https://youtu.be/6rGKI5KblZ4?t=124) AMD 對應 Intel Boot Guard 的功能名稱，Whisper 聽成「guard me」。
2. 沒有投影片：信任鏈圖、HSM 外型、`signing.bbclass` 設定範例、GitHub 範例連結都沒有看到。

---

*筆記依據 Rouven Czerwinski〈Practical Application of Verified Boot〉（Open Source Summit Europe 2024）錄影（Whisper `turbo` 轉錄，42:02）與影片說明欄整理。沒有投影片。*
