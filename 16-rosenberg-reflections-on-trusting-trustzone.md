---
talk: Reflections on Trusting TrustZone
speaker: Dan Rosenberg（Azimuth Security）
conference: Black Hat USA 2014
year: 2014（2014-08-06）
video: https://youtu.be/7w40mS5yLjc
slides: https://www.blackhat.com/docs/us-14/materials/us-14-Rosenberg-Reflections-on-Trusting-TrustZone.pdf
whitepaper: https://www.blackhat.com/docs/us-14/materials/us-14-Rosenberg-Reflections-On-Trusting-TrustZone-WP.pdf
---

# Reflections on Trusting TrustZone [▶ 影片](https://youtu.be/7w40mS5yLjc)

> **演講**：Dan Rosenberg（Azimuth Security），Black Hat USA 2014。Black Hat 頻道 2015-03-19 上傳。
> **來源**：YouTube 錄影（39:25）用 Whisper `turbo` 轉成逐字稿，再加上 Black Hat 官方投影片（33 頁）和白皮書（5 頁，2014-07-01，只寫漏洞、不寫利用方法）。
> **標記說明**：`【口頭】` 是投影片沒有的。`【投影片補充】`、`【白皮書補充】` 是投影片／白皮書有、講者沒講的。`⚠️ 逐字稿缺字` 是 Whisper 聽錯。`⚠️ 待確認` 是查不清楚的地方。
> **攻防內容的寫法**：寫漏洞成因、攻擊鏈的「階段」、教訓。投影片和白皮書上的具體欄位值、溢位用的數字**不收錄**。
> **年代提醒**：2014 年、32 位元 ARM、Qualcomm QSEE。照講者當時講的寫。
> 錄影沒有 Q&A。

---

## 目錄

- [0. 這場演講要做什麼](#0-這場演講要做什麼)
- [1. TrustZone 是什麼、拿來做什麼](#1-trustzone-是什麼拿來做什麼)
- [2. 前人研究與動機](#2-前人研究與動機)
- [3. 目標與工具：Qualcomm QSEE](#3-目標與工具qualcomm-qsee)
- [4. 攻擊面與威脅模型](#4-攻擊面與威脅模型)
- [5. QSEE 的 SMC 介面與檢查](#5-qsee-的-smc-介面與檢查)
- [6. 漏洞：範圍檢查的整數溢位](#6-漏洞範圍檢查的整數溢位)
- [7. 從「寫死的 12 byte」到任意程式碼執行](#7-從寫死的-12-byte到任意程式碼執行)
- [8. Demo：永久解鎖 Verizon Moto X](#8-demo永久解鎖-verizon-moto-x)
- [9. 教訓](#9-教訓)
- [10. 一頁速查表](#10-一頁速查表)
- [11. 延伸連結](#11-延伸連結)

---

## 0. 這場演講要做什麼

[▶ 00:00](https://youtu.be/7w40mS5yLjc?t=0)

- 攻擊 TrustZone：Qualcomm 的 TrustZone kernel（QSEE）的一個漏洞，以及怎麼把它變成在 secure world 任意執行程式碼。
- 最後用它**永久解鎖一支不能解鎖的 Verizon Moto X 的 bootloader**。

---

## 1. TrustZone 是什麼、拿來做什麼

[▶ 00:35](https://youtu.be/7w40mS5yLjc?t=35)（p.2–4）

**架構**：
- 所有軟硬體分成 **normal world** 和 **secure world**。
- normal world：一般 OS（這場是 Android／Linux）、應用程式、系統服務。
- secure world：最常見的是一個 **TrustZone kernel**，上面跑幾個獨立的 **trustlet**（trusted application），常由第三方撰寫（[▶ 01:06](https://youtu.be/7w40mS5yLjc?t=66)）。
- 兩邊由 **monitor** 仲裁。
- **secure world 能存取所有軟硬體，normal world 不行**，只能經明確定義的通道溝通。secure world 可以把某些記憶體設成 secure-only，**連 kernel 都存取不到**。【口頭】很像 hypervisor（[▶ 01:40](https://youtu.be/7w40mS5yLjc?t=100)）。

**實際用途**（p.4；[▶ 02:10](https://youtu.be/7w40mS5yLjc?t=130)）：

| 用途 | 說明 |
|---|---|
| **DRM**（Widevine、PlayReady、DTCP-IP） | 【口頭】最常見。受保護的影音只在 secure world 解碼，使用者就算完全控制自己的 OS 也碰不到 |
| 安全金鑰儲存 | 投影片寫「dm-verify」，講者說是「Linux kernel 的全碟加密技術」。⚠️ 待確認：講者描述的比較像 dm-crypt，投影片的「dm-verify」原文照錄 |
| 行動支付 | 存敏感資訊 |
| 受保護的硬體 | 例如只跟 secure world 溝通的安全鍵盤：OS 被攻破時，PIN 輸入仍然安全（[▶ 02:41](https://youtu.be/7w40mS5yLjc?t=161)） |
| **管理 secure boot** | 很多廠商用軟體可燒的 fuse（Qualcomm 的 **QFuse**）實作 secure boot。TrustZone 能讀寫這些 fuse，所以常直接或間接參與管理 secure boot（[▶ 03:12](https://youtu.be/7w40mS5yLjc?t=192)） |
| kernel 完整性監控 | Samsung Knox 的 **TIMA**：在 secure world 定期掃描記憶體裡的 kernel，發現竄改就發出安全例外或重開機（[▶ 03:44](https://youtu.be/7w40mS5yLjc?t=224)） |

---

## 2. 前人研究與動機

[▶ 03:44](https://youtu.be/7w40mS5yLjc?t=224)（p.5–6）

**之前公開的研究很少**：
- Thomas Roth，2013，「Next Generation Mobile Rootkits」：用 TrustZone 當平台偷偷監視使用者，因為 kernel 看不進 TrustZone。【口頭】他提到可能用漏洞裝 rootkit，但沒講具體漏洞和利用（[▶ 04:14](https://youtu.be/7w40mS5yLjc?t=254)）。
- 講者自己 2013 年在 Azimuth 部落格：「Unlocking the Motorola Bootloader」，一個 Motorola 專屬的 TrustZone 漏洞，攻破 secure boot（[▶ 04:46](https://youtu.be/7w40mS5yLjc?t=286)）。
- XDA 等 root／改機社群的 HTC exploit：用過 TrustZone 相關攻擊，但沒文件、被混淆，沒人公開分析過。
- 【口頭】最近一兩個月前 REcon 上，Nathan Keltner 和 Charles Holmes 的「Here Be Dragons」：HTC 的 TrustZone 漏洞（[▶ 05:22](https://youtu.be/7w40mS5yLjc?t=322)）。

**動機**（[▶ 05:54](https://youtu.be/7w40mS5yLjc?t=354)）：
- **高價值目標**，很多方都在乎：
  - 內容提供者靠它防盜版。
  - Samsung 這類 OEM 靠它提供安全服務、搶企業市場。
  - 使用者靠它保護自己；改機社群則想**攻破 TrustZone 來繞過 secure boot**、裝自己的軟體。
- **公開檢視很少**，撐不起行銷文宣的「高度安全」宣稱（[▶ 06:28](https://youtu.be/7w40mS5yLjc?t=388)）。

---

## 3. 目標與工具：Qualcomm QSEE

[▶ 06:28](https://youtu.be/7w40mS5yLjc?t=388)（p.7–8）

- 目標：**QSEE**（Qualcomm Secure Execution Environment）。
- 理由：Qualcomm 在中高階 Android 手機佔多數，特別是北美和歐洲。【口頭】「你聽過的 Samsung、LG、Motorola、HTC 旗艦機，在歐美賣的，大概都用 Qualcomm 晶片，也就用 QSEE。」（[▶ 07:02](https://youtu.be/7w40mS5yLjc?t=422)）
  - p.7 列：Samsung GS4/GS5/Note3、LG Nexus 4/Nexus 5/G2/G3、Moto X、HTC One 系列……

**工具需求很少**（[▶ 07:02](https://youtu.be/7w40mS5yLjc?t=422)）：
- **TrustZone image 很容易拿到**：網路上有大量韌體封存檔，常常就是 tar 或 zip，直接取出；或在有 root 的裝置上用 `dd` 從磁碟讀出（[▶ 07:37](https://youtu.be/7w40mS5yLjc?t=457)）。
- 拿到後用 IDA Pro 逆向。
- 較早的 image 用 Qualcomm 專屬的 40 byte header；新的直接是 **ELF**（[▶ 08:10](https://youtu.be/7w40mS5yLjc?t=490)）。

---

## 4. 攻擊面與威脅模型

### 4.1 攻擊面

[▶ 08:43](https://youtu.be/7w40mS5yLjc?t=523)（p.9）

| 攻擊面 | 講者的評估 |
|---|---|
| **SMC 介面**（軟體例外） | **最有價值**。SMC 是特權指令（只有 kernel 能執行），類似 system call：kernel 用它請 TrustZone 做事（[▶ 09:16](https://youtu.be/7w40mS5yLjc?t=556)） |
| 硬體例外（IRQ、FIQ、external abort） | 介面窄，比較不可能有漏洞 |
| 共享記憶體介面 | Qualcomm 不太用；MobiCore 大量使用，是那邊的有趣目標（[▶ 09:47](https://youtu.be/7w40mS5yLjc?t=587)） |
| **eMMC flash 的內容** | TrustZone 常會讀磁碟內容並解析（例如為了 secure boot 驗證），**讀取和解析的漏洞可以被特製的磁碟內容觸發** |
| trustlet 專屬的呼叫 | 【口頭】他看了一些，**有很多低垂的果實**，可能因為第三方廠商沒有 Qualcomm 那樣的安全工程文化。但新版 TrustZone kernel 裡 trustlet **彼此隔離**，攻破一個不代表能碰到別的或 kernel（[▶ 10:19](https://youtu.be/7w40mS5yLjc?t=619)） |

### 4.2 攻擊者假設

[▶ 11:23](https://youtu.be/7w40mS5yLjc?t=683)（p.10）

1. **已經能在裝置上執行任意程式碼**：實務上幾乎沒有遠端攻擊面，很難想像手機的 TrustZone kernel 需要直接收遠端資料。
2. **有 kernel 權限**：可能是手機主人自己，也可能是攻擊者用 kernel exploit 提權（[▶ 11:56](https://youtu.be/7w40mS5yLjc?t=716)）。要能下 SMC 指令，否則幾乎沒辦法跟 TrustZone 互動。
3. **當機、DoS 不算安全問題**：kernel 本來就能讓裝置重開機、甚至弄壞它（[▶ 12:28](https://youtu.be/7w40mS5yLjc?t=748)）。

---

## 5. QSEE 的 SMC 介面與檢查

[▶ 13:01](https://youtu.be/7w40mS5yLjc?t=781)（p.11–15）

- QSEE 閉源，下面全是逆向的。但 **kernel 這端的 driver 是開源的**（Qualcomm CAF 樹的 `arch/arm/mach-msm/scm.c`），看它怎麼跟 TrustZone 溝通有幫助（[▶ 13:32](https://youtu.be/7w40mS5yLjc?t=812)）。
- kernel driver 叫 **SCM**（Secure Channel Manager）。【口頭】用的明明是 SMC 指令卻叫 SCM，「很容易搞混」。

**兩種呼叫慣例**（[▶ 14:04](https://youtu.be/7w40mS5yLjc?t=844)）：

1. **用暫存器**：r0 放 SMC 命令編號、旗標、參數個數，參數放 r1、r2……
2. **用命令結構**（重點）：r0 放一個**命令緩衝區的實體位址**（[▶ 14:35](https://youtu.be/7w40mS5yLjc?t=875)）。緩衝區裡依序是：
   - **request header**（由 kernel 填）：整個緩衝區長度、input 資料的 offset、**response header 的 offset**、命令 ID。
   - request buffer（輸入資料）。
   - **response header**（由 QSEE 處理完後填）：長度、output 的 offset、完成旗標。
   - response buffer（輸出資料）。

**QSEE 的五項檢查**（p.14；[▶ 16:09](https://youtu.be/7w40mS5yLjc?t=969)）：
- 從 TrustZone 的角度，**kernel 不可信**，所以要確認 kernel 沒有騙它去寫 secure memory。
- 檢查大意（不列具體數字）：
  1. 長度至少有 request header 那麼大。
  2. input 在緩衝區範圍內。
  3. input 不跟 request header 重疊。
  4. response header 整個在緩衝區範圍內。
  5. **整個命令緩衝區都在 non-secure memory**（[▶ 17:16](https://youtu.be/7w40mS5yLjc?t=1036)）。
- 第 5 項最重要：如果 kernel 給一個在 secure memory 的位址，QSEE 就可能去讀寫 secure memory（[▶ 17:49](https://youtu.be/7w40mS5yLjc?t=1069)）。

**secure memory 怎麼判斷**（p.15；[▶ 18:19](https://youtu.be/7w40mS5yLjc?t=1099)）：
- 完全用軟體：一份**寫死的區域清單**，每個區域有旗標表示記憶體屬性。
- 檢查函式逐一比對，確認指定範圍不跟任何受保護區域重疊。
- 【口頭】類似 Linux kernel 的 `access_ok()`：「這塊記憶體 TrustZone 可以安全地操作嗎？」

---

## 6. 漏洞：範圍檢查的整數溢位

[▶ 18:53](https://youtu.be/7w40mS5yLjc?t=1133)（p.16–20；白皮書第 5–6 節）

**檢查函式的邏輯**（p.17）：
- 上層函式收「起點、大小」，算出「終點＝起點＋大小」，交給下層函式。
- **下層函式發現「終點小於起點」時，以為呼叫者寫錯了，就把兩者對調**（[▶ 19:25](https://youtu.be/7w40mS5yLjc?t=1165)）。
- 【口頭】「這一點馬上跳出來，看起來是非常壞的主意。」（[▶ 20:02](https://youtu.be/7w40mS5yLjc?t=1202)）

**成因**（[▶ 20:35](https://youtu.be/7w40mS5yLjc?t=1235)）：
- 32 位元整數最大到 2^32−1，超過就**繞回 0**（整數溢位）。
- 「起點＋大小」兩個都是攻擊者給的。給一個很大的長度，**相加就溢位繞回**，算出來的終點比起點小（[▶ 21:06](https://youtu.be/7w40mS5yLjc?t=1266)）。
- 下層函式把它們對調 → **實際被檢查的是另一段完全不同的範圍**（[▶ 21:40](https://youtu.be/7w40mS5yLjc?t=1300)）。
- 結果：五項檢查都通過，但 **response header 的位置可以指到 secure memory 裡任何地方，包括 QSEE 本身的 image**（[▶ 22:44](https://youtu.be/7w40mS5yLjc?t=1364)）。

**能寫什麼**（p.19–20；[▶ 23:47](https://youtu.be/7w40mS5yLjc?t=1427)）：
- response header 的內容是**寫死的**：三個固定的 word（長度、offset、完成旗標）。
- → **能把三個固定的 word 寫到任意 secure memory。**

**影響範圍**【白皮書補充】：寫作時，所有支援 TrustZone、使用 Qualcomm Snapdragon 的已知 Android 裝置都有這個漏洞，只有 Samsung Galaxy S5 和 HTC One M8 已修補。

---

## 7. 從「寫死的 12 byte」到任意程式碼執行

[▶ 24:19](https://youtu.be/7w40mS5yLjc?t=1459)（p.21–29）

**有利條件**（p.21；[▶ 24:49](https://youtu.be/7w40mS5yLjc?t=1489)）：
- **QSEE 的記憶體配置是已知的**：image 沒加密地放在 eMMC 上，而且載入到固定的實體位址。所以雖然讀不到 secure memory，也知道裡面每樣東西在哪。
- 大部分 RAM 是 non-secure，有很大的草稿空間可用。

**直覺做法失敗**（p.22；[▶ 25:20](https://youtu.be/7w40mS5yLjc?t=1520)）：
- 像 kernel exploit 那樣，改 secure memory 裡的函式指標，讓它指向 non-secure 的 payload。
- **不成功**。【口頭】他推測 QSEE 有機制**禁止 TrustZone 執行 non-secure 頁面**，類似 user space 的 NX／DEP、kernel 的 PXN／SMEP，可能跟負責標記 secure 區域的 **XPU** 有關。但那是「沒有文件的黑洞」（[▶ 25:52](https://youtu.be/7w40mS5yLjc?t=1552)）。
  - 【口頭】「這是我害羞地問台下有沒有 Qualcomm 或 Arm 員工的時候……不過我想他們不能說。」

**難處**（p.23；[▶ 26:55](https://youtu.be/7w40mS5yLjc?t=1615)）：
- 寫入是 12 byte，內容不受控：想改一個 word 會連帶蓋掉相鄰的，可能不穩。
- 能寫的值只有 0、12、1，「詞彙非常有限」。
- → 要用這個原語**建出更有彈性的原語**。

**攻擊鏈的階段**（細節不收錄）：
1. **改掉「受保護區域清單」**（p.24–25；[▶ 28:02](https://youtu.be/7w40mS5yLjc?t=1682)）：
   - 用那 12 byte 蓋掉清單裡 **QSEE image 那一項**的旗標和範圍。
   - 從此 QSEE 檢查 kernel 給的指標時，**指向 QSEE image 的位址都會被當成「安全的 non-secure memory」**（[▶ 28:36](https://youtu.be/7w40mS5yLjc?t=1716)）。
   - → 任何會輸出資料的 SMC handler，都變成「寫任意值到 secure memory」的原語。挑一個適合的就好（[▶ 29:08](https://youtu.be/7w40mS5yLjc?t=1748)）。
2. **改 SMC handler 表**（p.27–28；[▶ 29:41](https://youtu.be/7w40mS5yLjc?t=1781)）：
   - QSEE 的 SMC 表是**變長**的項目（每項的長度由它的參數個數決定），依序走訪找相符的 SMC 編號。
   - 改掉某一項的參數個數，讓走訪程式算出的「下一項」落到**攻擊者控制的 non-secure memory**，在那裡放一個假項目（講者叫它 **SMC table extension attack**）（[▶ 31:14](https://youtu.be/7w40mS5yLjc?t=1874)）。
   - → 能用任意參數呼叫 QSEE 裡的任意函式。【口頭】「我認為這是取得 TrustZone 完全控制的優雅方式。」（[▶ 31:47](https://youtu.be/7w40mS5yLjc?t=1907)）
   - 注意：執行的仍是 **secure memory 裡的程式碼**，只是函式指標和參數由攻擊者決定，所以繞過了「不能執行 non-secure 頁面」的限制。

**能做什麼**（p.29；[▶ 32:21](https://youtu.be/7w40mS5yLjc?t=1941)）：
- 找到 QSEE 的 `memcpy`，**把整個 secure memory 複製到 non-secure 緩衝區** → 所有 DRM、安全金鑰儲存都破了。
- 關掉 TIMA，或任何 TrustZone 裡的安全功能。
- 呼叫 OEM 專屬功能，例如**永久解鎖 bootloader**。

---

## 8. Demo：永久解鎖 Verizon Moto X

[▶ 32:51](https://youtu.be/7w40mS5yLjc?t=1971)（p.30）

**Motorola 的 bootloader 解鎖機制**（[▶ 33:24](https://youtu.be/7w40mS5yLjc?t=2004)）：
1. 使用者從裝置取得一個 request token，送給 Motorola。
2. 如果裝置屬於核准的電信商，Motorola 回一個 response token。
3. 使用者把 token 交給 bootloader，**bootloader 請 TrustZone 燒一個 QFuse，永久解鎖**。
- **Verizon 和 AT&T 的機種，Motorola 不回 token**，所以無法解鎖（[▶ 33:57](https://youtu.be/7w40mS5yLjc?t=2037)）。
- 但只要有一個 TrustZone 漏洞，**就能自己呼叫「收到 token 後會做的那個功能」**。

**Demo**：
1. Verizon Moto X，Android 4.4，顯示未解鎖、保固還在。
2. 【口頭】「非常冒險的 demo：第一是現場，第二是一支手機只能做一次（永久燒 fuse），這支從沒測過。」「第二冒險的事。第一冒險的是用 OpenOffice 做投影片。」（[▶ 34:30](https://youtu.be/7w40mS5yLjc?t=2070)）
3. adb shell → 用一個最近的 Linux 漏洞提權到 root → 執行 exploit（[▶ 35:01](https://youtu.be/7w40mS5yLjc?t=2101)）。
4. 再看 bootloader 變數：**已解鎖**。可以用 fastboot 燒任何軟體了。
5. 【口頭】「據我所知，這是世界上唯一（或少數之一）解鎖的 Verizon Moto X。」（[▶ 35:37](https://youtu.be/7w40mS5yLjc?t=2137)）

---

## 9. 教訓

[▶ 35:37](https://youtu.be/7w40mS5yLjc?t=2137)（p.31–32）

1. **TrustZone image 沒加密，讓分析和利用容易很多**（[▶ 36:09](https://youtu.be/7w40mS5yLjc?t=2169)）。
   - 對照 iOS：TrustZone image 在磁碟上是加密的，沒有 Apple 外洩的韌體、也沒先攻破 iBoot 的話，連分析的材料都沒有。
2. **解析複雜資料結構是明顯的失敗點**（這裡是命令緩衝區）。研究者該重點檢視這種地方（[▶ 36:40](https://youtu.be/7w40mS5yLjc?t=2200)）。
3. **相信直覺**：看起來可疑的，很可能真的有問題。【口頭】他一看到組語裡「呼叫錯了就幫你對調參數」，就覺得不對，雖然當下不知道會怎樣，結果是非常嚴重的漏洞。
4. **單一失效點是壞主意**（[▶ 37:12](https://youtu.be/7w40mS5yLjc?t=2232)）：
   - Samsung 的 secure boot **沒有單一失效點**，沒有一個開關能讓你攻破某個東西就解鎖。
   - Motorola 的設計讓他們方便（不用為不同電信商出不同軟硬體），但**任何一個 TrustZone 漏洞都會導致永久解鎖**。【口頭】「對我這種喜歡裝東西的人很好，對 Motorola 的客戶不太好。」
5. **縮小攻擊面是好主意，但功能膨脹會把這個優勢完全吃掉**（[▶ 37:43](https://youtu.be/7w40mS5yLjc?t=2263)）。
   - 【口頭】TrustZone 的基本設計很好：硬體強制的安全邊界，加上一個最小、可信的核心。但廠商太熱衷，塞了太多功能，攻擊面大幅擴大，抵銷了「設計成很小」的優點。
6. **行銷消除不了軟體 bug**（[▶ 38:15](https://youtu.be/7w40mS5yLjc?t=2295)）。【口頭】他真的在媒體報導裡看過「TrustZone 100% 安全」。

---

## 10. 一頁速查表

**攻擊鏈**

```
kernel 權限（假設）
 └ SMC（命令結構）：長度＋起點整數溢位，範圍檢查「終點<起點就對調」
     └ 五項檢查全過 → QSEE 把寫死的 response header 寫到任意 secure memory（3 個固定 word）
         └ 改「受保護區域清單」裡 QSEE image 那項 → 輸出型 SMC 變成任意寫入
             └ 改變長的 SMC 表 → 假項目在 non-secure memory → 任意呼叫 QSEE 函式
                 └ memcpy 出整個 secure memory／關 TIMA／燒 QFuse 解鎖 bootloader
```

| 環節 | 成因 | 防禦教訓 |
|---|---|---|
| 範圍檢查 | 起點＋長度溢位；「終點<起點就對調」 | 檢查要先防溢位；錯誤輸入要拒絕，不要「幫忙修正」 |
| 受保護區域清單 | 存在可被寫入的 secure memory | 安全關鍵的資料結構要唯讀或受硬體保護 |
| 不能執行 non-secure 頁面 | 有效，擋下了最直接的利用 | 但用「呼叫 secure 裡現有的函式」就能繞過 |
| 變長的 SMC 表 | 走訪靠表內的長度欄位 | 分派表應該唯讀、固定格式 |
| image 沒加密、位址固定 | 攻擊者知道一切在哪 | 加密 image、位址隨機化提高門檻 |
| Motorola 解鎖設計 | TrustZone 能燒解鎖 fuse → 單一失效點 | 不要讓一個元件的任何漏洞就能永久改變裝置狀態 |

---

## 11. 延伸連結

- MT8189 上 OP-TEE／BL31 怎麼檢查 normal world 傳進來的記憶體（對照 QSEE 的「is non-secure memory」）：[`../tf-a-and-op-tee-note/smc-call-flow.md`](../tf-a-and-op-tee-note/smc-call-flow.md)、[`../tf-a-and-op-tee-note/secure-memory.md`](../tf-a-and-op-tee-note/secure-memory.md)
- 延伸建議（不是講者說的）：MT8189 的 RPMB key 由 BL31 的 HACC 導出，跟本場「TrustZone 管 fuse／金鑰」是同一類責任，見 `../rpmb-notes/rpmb-intro.md`。

---

## 附：一句話總結

> **QSEE 檢查 kernel 給的緩衝區在不在 non-secure memory 時，起點加長度會整數溢位，而檢查函式還會「好心」對調起終點，於是 secure memory 可以被寫入；講者一步步把這個只能寫三個固定值的原語，擴大成在 TrustZone 裡任意呼叫函式，最後永久解鎖了一支不能解鎖的手機。**

---

## ⚠️ 待確認清單

1. [▶ 02:41](https://youtu.be/7w40mS5yLjc?t=161) 「dm-verify」：p.4 原文如此，講者說是「全碟加密」，比較像 dm-crypt。

---

*筆記依據 Dan Rosenberg〈Reflections on Trusting TrustZone〉（Black Hat USA 2014）錄影（Whisper `turbo` 轉錄，39:25）、Black Hat 官方投影片與白皮書整理。*
