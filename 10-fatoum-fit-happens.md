---
talk: "FIT Happens: How Secure Boot Wasn't"
speaker: Ahmad Fatoum（Pengutronix）
conference: Open Source Summit + Embedded Linux Conference Europe 2026（sched 議程 osselceu2026 有此場）
year: 2026
video: https://youtu.be/mMlSsVGGAsI
slides: 待補（sched 擋自動抓取，找不到官方投影片）
---

# FIT Happens: How Secure Boot Wasn't [▶ 影片](https://youtu.be/mMlSsVGGAsI)

> **演講**：Ahmad Fatoum（Pengutronix），Linux Foundation 頻道 2026-11-03 上傳。
> **來源**：YouTube 錄影（38:12）用 Whisper `turbo` 轉成逐字稿，再加上影片說明欄（官方摘要，提到 CVE-2026-33243）。**沒有投影片**，講者指著圖說的地方（FIT 二進位格式圖、哪些部分被簽的上色圖）都看不到。
> **標記說明**：`【口頭】` 這場沒有投影片，正文幾乎全是口頭，只標實務經驗和意見。`【說明欄補充】` 是影片說明欄有的。`【Q&A】` 是現場提問（有些提問沒收音）。`⚠️ 逐字稿缺字` 是 Whisper 聽錯。`⚠️ 待確認` 是查不清楚的地方。
> **攻防內容的寫法**：只寫漏洞成因、攻擊的「類型」、修補與防禦教訓，不寫可以照做的偽造步驟。

---

## 目錄

- [0. 這場演講要做什麼](#0-這場演講要做什麼)
- [1. FIT 怎麼來的](#1-fit-怎麼來的)
- [2. FIT 的範圍越長越大](#2-fit-的範圍越長越大)
- [3. 簽章怎麼加上去的：簽 image（不安全）](#3-簽章怎麼加上去的簽-image不安全)
- [4. 簽 configuration：好一點，但還有空隙](#4-簽-configuration好一點但還有空隙)
- [5. FIT 被攻破的模式](#5-fit-被攻破的模式)
- [6. CVE-2026-33243：hashed-nodes 混淆](#6-cve-2026-33243hashed-nodes-混淆)
- [7. 提案：整個 FIT 一起簽](#7-提案整個-fit-一起簽)
- [8. 在那之前：流程上該做的事](#8-在那之前流程上該做的事)
- [9. 測試：你有測過「沒簽的 FIT 會被拒絕」嗎？](#9-測試你有測過沒簽的-fit-會被拒絕嗎)
- [10. Q&A](#10-qa)
- [11. 一頁速查表](#11-一頁速查表)
- [12. 延伸連結](#12-延伸連結)

---

## 0. 這場演講要做什麼

[▶ 00:00](https://youtu.be/mMlSsVGGAsI?t=0)

- Pengutronix 這幾年大部分客戶專案都用某種 verified boot。x86 上多半是 UKI，**Arm 上大量用 FIT**。
- 流程：
  1. FIT 的歷史。
  2. FIT 的範圍怎麼越長越大。
  3. 簽章怎麼「硬加」到格式上。
  4. 這些年怎麼被攻破。
  5. 他的改進提案，以及之後怎麼安全地繼續用 FIT。

【說明欄補充】FIT 是 U-Boot 偏好的開機 image 格式，支撐了數十億個嵌入式 Linux 開機流程，barebox 也採用。用 FDT 格式帶來彈性和程式碼重用，也成了很多細微安全漏洞的來源；最嚴重的是 **CVE-2026-33243**，一個存在十年的漏洞，讓數百萬台裝置的 verified boot 可以被繞過。

---

## 1. FIT 怎麼來的

[▶ 00:33](https://youtu.be/mMlSsVGGAsI?t=33)

【口頭】講者說「打個折聽，那時我才 13 歲，不在場」。

**前身 uImage 的限制**（[▶ 01:05](https://youtu.be/mMlSsVGGAsI?t=65)）：
- 前面只有 **64 byte header**。
- 後期有 multi-file image：開頭列幾個大小，後面接幾個 image。
- 問題：
  - 只有 **CRC32**，放不下較長的密碼學雜湊。
  - 只有**一個** load address。
  - 不能「有 kernel 和 DTB，但沒有 ramdisk」：大小為 0 的 ramdisk 會被當成清單結束。

**需求**（[▶ 01:38](https://youtu.be/mMlSsVGGAsI?t=98)）：
- **每個 image 各自**有 load address、雜湊。
- **可開機的 configuration**：某些 image 的組合。板子 1 用這三個，板子 2 用那兩個。全部放在同一個檔案，一個檔案部署到很多種硬體。

**為什麼選 device tree 當格式**（[▶ 02:08](https://youtu.be/mMlSsVGGAsI?t=128)）：
1. **無限彈性**：任意巢狀（【口頭】現在 FIT 解析限制 64 層），任意多個字串名稱的 key-value。
2. **現成工具**：dtc、libfdt。
3. **bootloader 程式碼大小很寶貴**：bootloader 本來就要用 libfdt 修改 DT 再交給 kernel（例如 Arm 的 bootargs 寫在 DT 裡），**那就用同一套去解析放 kernel 的 image**。「一石多鳥」（[▶ 03:09](https://youtu.be/mMlSsVGGAsI?t=189)）。

**長什麼樣**（[▶ 03:41](https://youtu.be/mMlSsVGGAsI?t=221)）：
- 右邊 images（kernel、ramdisk、任意多個 DTB），左邊 configurations。
- bootloader 讀 DT，決定開哪個 configuration。
  - 【口頭】講者喜歡用 configuration 的 **`compatible`**：bootloader 自己的 DT 有板子的 compatible，拿去比對 FIT 裡各 configuration 的 compatible（[▶ 04:12](https://youtu.be/mMlSsVGGAsI?t=252)）。
- 產生方式：
  - Linux 約 6.10 起，arm64 有 `make image.fit` 目標，產生含所有 DTB、kernel（可選 ramdisk）的 FIT（[▶ 04:44](https://youtu.be/mMlSsVGGAsI?t=284)）。
  - 手寫 `.its`，用 `/incbin/` 直接把 binary 塞進去。
  - build 系統包裝：ptxdist、Yocto（OE-core 的 `kernel-fitimage.bbclass`、meta-oe 的 `fitimage.bbclass`）。
  - `mkimage` 也能直接從命令列參數產生（[▶ 05:15](https://youtu.be/mMlSsVGGAsI?t=315)）。

**二進位格式**（[▶ 05:45](https://youtu.be/mMlSsVGGAsI?t=345)）：
- 就是一個 FDT：header、memory reservation block（FIT 用不到，空的）、structure block（所有節點和屬性，**kernel、DTB、ramdisk 的內容都以屬性值內嵌**）、strings block（屬性名稱集中放一次，intern 起來）。
- **缺點：FDT 和 FIT 長得一模一樣，分不出來**。要真的解析、用經驗法則判斷，例如有沒有 `/configurations` 節點（[▶ 06:17](https://youtu.be/mMlSsVGGAsI?t=377)）。

> ⚠️ 逐字稿缺字：「libfttt」＝libfdt；「Pingotronics」＝Pengutronix；「PDXtest」＝ptxdist；「Bearbox」＝barebox。

---

## 2. FIT 的範圍越長越大

[▶ 06:47](https://youtu.be/mMlSsVGGAsI?t=407)

1. **FIT 當分割表**：
   - image 資料不放在 DT 屬性裡，而是放在 DT 之外，只記 `data-offset`、`data-size`。
   - 可以有內嵌的、也可以有外部的「分區」（[▶ 07:19](https://youtu.be/mMlSsVGGAsI?t=439)）。
   - **副作用**：FDT header 的 `totalsize` 不再等於 FIT 大小，只是 DT 那部分的大小。要知道整個 FIT 多大，**得走過每個 image、把 offset＋size 加起來找最大的**。不解析 DT 就不知道 FIT 有多大（[▶ 07:52](https://youtu.be/mMlSsVGGAsI?t=472)）。
2. **U-Boot 自己也放在 FIT 裡**（[▶ 08:23](https://youtu.be/mMlSsVGGAsI?t=503)）：
   - SPL 不只要載 U-Boot proper 和 DTB，還有 TF-A、OP-TEE 等，需要容器格式，就用 FIT。
   - **問題**：SPL 跑在**最高權限**。如果攻擊 U-Boot proper 時 OP-TEE 已經載好，TrustZone 還碰不到；但 SPL 本身就在最高權限。
   - 【口頭】**更糟的是**：SPL 空間很緊，所以 libfdt 裡一些「檢查 DT 是否損壞」的檢查**在 SPL 被省掉了**，而它偏偏是更關鍵的那段。U-Boot proper 裡有這些檢查（[▶ 08:57](https://youtu.be/mMlSsVGGAsI?t=537)）。

---

## 3. 簽章怎麼加上去的：簽 image（不安全）

[▶ 08:57](https://youtu.be/mMlSsVGGAsI?t=537)

- 一開始 FIT 只有雜湊和 CRC 寫在 DT 裡，沒有簽章。【口頭】大約五年後才加上簽章。
- 最早是**簽個別 image**：只簽 image 節點的 **`data` 屬性內容**，**其他都沒簽，包括 load 和 entry address**（[▶ 09:27](https://youtu.be/mMlSsVGGAsI?t=567)）。

**為什麼這樣根本不安全**（[▶ 09:59](https://youtu.be/mMlSsVGGAsI?t=599)）：
- 沒簽的欄位（例如 entry）可以被改，**讓執行跳到攻擊者放進 FIT 的其他資料**。
- U-Boot 對 entry **沒有邊界檢查**。
- 就算加了邊界檢查也沒用：kernel image 有 10～20 MB 的可執行碼，裡面有太多跳躍指令可以利用（[▶ 10:30](https://youtu.be/mMlSsVGGAsI?t=630)）。
- 【口頭】「這根本上不安全，我不認為救得回來。」
- 【口頭】barebox 從沒實作 image 簽章。講者理解當時的顧慮是 mix-and-match 攻擊，但「跟 entry 這個問題比起來，那只是小問題」。他自己也是在 U-Boot 郵件列表上讀到才知道。

**誰還在用**（[▶ 11:01](https://youtu.be/mMlSsVGGAsI?t=661)）：
- OE-core 的 `uboot-sign.bbclass` 開 `SPL_SIGN_ENABLE` 時就是這樣簽。所以 SPL 載的 **TF-A、OP-TEE、FDT、U-Boot 都可以被輕易換掉**。
  - 建議：做降級保護、修掉、**撤銷簽章金鑰**。
  - 講者回報了，Marta 正在修（patch 到第 3、4 版）。
- **`mkimage -F auto`** 產生的 FIT 也是這種（[▶ 11:31](https://youtu.be/mMlSsVGGAsI?t=691)）。
  - 【口頭】大家用 `-F auto` 是因為它順便能修補 U-Boot 的 DT。可以那樣用，但**不要用它產生的 FIT**。
- 一些上游 U-Boot SPL 透過 `board_fit_image_post_process`（weak 函式）讓 SoC 程式碼自己驗 FIT。【口頭】講者認為那是錯的，沒細看，「應該有人去看」（[▶ 12:01](https://youtu.be/mMlSsVGGAsI?t=721)）。
- arm64 上 entry 其實會被忽略，但可以把 OS 改成預設啟用的 VxWorks，entry 又會被用到（[▶ 12:01](https://youtu.be/mMlSsVGGAsI?t=721)）。

---

## 4. 簽 configuration：好一點，但還有空隙

[▶ 12:01](https://youtu.be/mMlSsVGGAsI?t=721)

- 雜湊還是只蓋 `data`，但**簽章在 configuration 節點上**，涵蓋一組節點：根節點 `/`、`/configurations`、這個 configuration、它用到的所有 image 及其 hash 節點（[▶ 12:33](https://youtu.be/mMlSsVGGAsI?t=753)）。
- strings block 也要雜湊，但**只雜湊開頭一段**：之後新增的 configuration 可能帶表裡沒有的屬性名，所以只雜湊到某個點為止。

**還能動的地方**（[▶ 13:04](https://youtu.be/mMlSsVGGAsI?t=784)）：
- entry 改不了了。
- 但**可以**：加額外的 image、加額外的 configuration、在 `/images` 下加屬性（不能加在 image 節點本身）。
- 講者的圖（看不到）：**FDT header 完全沒檢查**；有些節點只檢查「存在」，不檢查內容；只有部分被驗證，其他完全沒驗證。

【口頭】正常情況下沒差，「但事情很少是正常的」。barebox 和 U-Boot 都是 C 寫的，有很多 C 專案共同的問題，例如大量未定義行為；他秀出的只是修過的那些，「還有多少，留給大家當練習」（[▶ 13:34](https://youtu.be/mMlSsVGGAsI?t=814)）。

---

## 5. FIT 被攻破的模式

[▶ 14:04](https://youtu.be/mMlSsVGGAsI?t=844)

**核心問題**：
- FIT 很難安全地解析。「不就是個 DT 嗎？」——但**在驗證簽章之前，你已經解析了它的一大部分**。
- **攻擊者只有一個目標：讓 FIT 的使用者把節點搞混。**

**混淆的基本型**（[▶ 14:34](https://youtu.be/mMlSsVGGAsI?t=874)）：
- 程式碼裡有兩條路：「**簽過的、要拿來驗的**是哪個節點」和「**要開機的**是哪個節點」。
- 只要能利用兩條路用的 API 不同，讓它們指到不同節點，就可能繞過開機驗證。

**手段類型**（[▶ 15:06](https://youtu.be/mMlSsVGGAsI?t=906)）：
1. **記憶體安全問題**：buffer overflow 之類。
2. **API 本身的模糊性**：
   - U-Boot 用 libfdt，barebox 用從 kernel 移植的 `of_*` 函式，**兩者原本都不是設計來處理不可信輸入的**。
   - 【口頭】**FIT 可能是唯一真正「不可信」的 device tree**（[▶ 15:37](https://youtu.be/mMlSsVGGAsI?t=937)）。TF-A 收到 DT 會直接信任，因為給它 DT 的 BL2 本來就在最高權限，沒必要防它；kernel 也不會假設 bootloader 是惡意的。
   - 所以這些 API 有「方便」的行為（[▶ 16:11](https://youtu.be/mMlSsVGGAsI?t=971)）：
     - libfdt：要 `memory` 節點，找不到時會給你 `memory@0`（**unit address 寬鬆比對**）。
     - kernel 的 `of_*`：要名叫 `kernel` 的節點，找不到小寫的會給你大寫的（**大小寫不敏感**）。
   - **這兩個看似瑣碎的行為，各自都曾是完整的 FIT 簽章繞過漏洞**：
     - unit address：**U-Boot** 的 FIT 驗證完全失效，barebox 沒事。
     - 大小寫：**barebox** 失效，U-Boot 沒事。
     - 【口頭】「每個人都有份。」
3. **騙走訪 DT 的程式**（[▶ 16:43](https://youtu.be/mMlSsVGGAsI?t=1003)）：節點名稱裡放 `/`、字串不以 null 結尾……不同 API 處理方式不同。
4. **「必要但不可信」的資料**（[▶ 17:13](https://youtu.be/mMlSsVGGAsI?t=1033)）：
   - FIT 的 **default configuration** 由攻擊者選（當然得是驗證過的 configuration）。
   - **`hashed-nodes`** 也是不可信的。

---

## 6. CVE-2026-33243：hashed-nodes 混淆

[▶ 17:13](https://youtu.be/mMlSsVGGAsI?t=1033)

【口頭】「可能是這幾年最大的 FIT 安全漏洞」，而且「簡單得令人意外」。

**成因**（[▶ 17:44](https://youtu.be/mMlSsVGGAsI?t=1064)）：
- 簽章節點裡的 **`hashed-nodes`** 屬性告訴驗證程式「**要雜湊哪些節點**」。
- 但 **`hashed-nodes` 本身沒被雜湊、沒被任何簽章涵蓋**。
- 攻擊者可以把原本合法的 image 搬到別的位置，在原位放一個惡意的 image，再改 `hashed-nodes`，讓它指向搬走的那個合法 image。
- 結果：**驗證時雜湊的是舊的合法 image，開機時用的卻是新的惡意 image**（[▶ 18:14](https://youtu.be/mMlSsVGGAsI?t=1094)）。
- **完全不需要記憶體安全漏洞**，所以適用範圍非常廣。

**根本原因**：
- 「**決定要雜湊什麼**」和「**決定要開什麼**」用了兩種不同的依據。
- 其實資訊是重複的：configuration 節點本身就有 `kernel`、`fdt` 等屬性指向 image，**開機用的就是它們，應該檢查的也是它們**。
- **bootloader 不該去信 `hashed-nodes`**（[▶ 18:46](https://youtu.be/mMlSsVGGAsI?t=1126)）。

**修補**：U-Boot、barebox、FIT 規範都修了。【口頭】應該只有 U-Boot 和 barebox 實作 configuration 簽章，所以受影響的大概就這兩個。

**影響**（[▶ 18:46](https://youtu.be/mMlSsVGGAsI?t=1126)）：
- 講者寫了 security advisory 說明影響範圍。
- 【口頭】**U-Boot SPL 用 configuration 簽章的話，OP-TEE 大概也能被攻擊。**

**宣傳做得夠不夠**（[▶ 19:19](https://youtu.be/mMlSsVGGAsI?t=1159)）：
- 現場：有用 FIT 做 verified boot 的人舉手 → 沒聽過這個漏洞的繼續舉手。
- 有不少人沒聽過。【口頭】「我們應該做得更好。」（第 8 節）

---

## 7. 提案：整個 FIT 一起簽

### 7.1 現況

[▶ 19:50](https://youtu.be/mMlSsVGGAsI?t=1190)

- FIT 還在長：分區可以互相重疊；FIT 當分割表再加 dm-verity，甚至有 kernel driver 把 FIT 當分割表掛起來；U-Boot 正在加支援。
- 【口頭】「該保持 FIT 安全，但不是以犧牲新功能為代價，對吧？」（語帶反諷）
- 他去年「Bootloaders under fire」演講的願望清單，很多實現了（[▶ 20:21](https://youtu.be/mMlSsVGGAsI?t=1221)）：
  - barebox security policy 上游了。
  - OSS-Fuzz 有 barebox 和 U-Boot 支援，FIT 程式碼也在被 fuzz。
  - 但：U-Boot 的 fuzzer 遇到要算雜湊就失敗（攻擊者明明可以輕易算雜湊）（[▶ 20:52](https://youtu.be/mMlSsVGGAsI?t=1252)）。
  - **兩邊的 fuzzer 都找不到第 6 節那種漏洞**，因為它不是記憶體安全問題。他在 barebox 做了有希望的東西，想抓這種混淆攻擊。
  - 清單上有一條「FIT image：解析前先驗證整個 image」。【口頭】當時想的是記憶體安全，「沒想到大門開得這麼大」（[▶ 21:22](https://youtu.be/mMlSsVGGAsI?t=1282)）。

### 7.2 已有的「整個簽」做法

[▶ 21:22](https://youtu.be/mMlSsVGGAsI?t=1282)

| 做法 | 狀況 |
|---|---|
| U-Boot 在 **i.MX8M** 上 | 把整個 FIT 當韌體簽，交給 boot ROM 驗。利用「FIT header 之後的節點可以搬」塞進讓 ROM 認得的東西。**這樣做的人沒被 CVE 影響**，但通常只用在 SPL，開 kernel 時還是受影響（「EL2 被攻破，EL3 沒有」）（[▶ 21:52](https://youtu.be/mMlSsVGGAsI?t=1312)） |
| Android Verified Boot | 可以加 trailer 驗整個 FIT。**U-Boot 的實作有 TOCTOU 漏洞**，別急著用（[▶ 22:22](https://youtu.be/mMlSsVGGAsI?t=1342)） |
| U-Boot `CONFIG_IMAGE_PRE_LOAD_SIG` | 有四年了，但不在規範裡、幾乎沒文件、不向後相容，不利推廣 |

### 7.3 需求

[▶ 22:53](https://youtu.be/mMlSsVGGAsI?t=1373)

- 通用、有文件、**向後相容**。
- 專注在主要用途：**安全的 kernel 開機容器**。
- 要有吸引力，讓不在乎「整個簽」的人也想用：
  1. 能**偵測**這是 FIT。
  2. 能知道 FIT 的**大小**。
  3. 能在後面**附加不被驗證的 metadata**。
  4. **最關鍵：驗證之前不做任何 DT 解析**。「不然整個可以丟掉了。」

### 7.4 格式提案

[▶ 23:27](https://youtu.be/mMlSsVGGAsI?t=1407)

1. FDT header 裡有一個現在沒人用的欄位 **`boot_cpuid_phys`**。提案放一個 **`FIT` magic**。
2. 有 magic 時，bootloader 預期**緊接著一個 `struct fit_header`**：
   - 也有一個 FIT magic 交叉檢查。
   - **external data size**：知道 FIT 多大，才知道要雜湊多少（[▶ 23:57](https://youtu.be/mMlSsVGGAsI?t=1437)）。
   - 前後相容用的 flags。
3. 有 FIT header，就有一個 **metadata trailer**：放在最後、很簡單的 **TLV** 格式，放 detached 簽章或其他不該被雜湊的東西。
4. **驗證流程**（[▶ 24:27](https://youtu.be/mMlSsVGGAsI?t=1467)）：
   - 只讀大約 8 個固定位置的整數。64 位元的限制在 48 位元，沒做溢位檢查的話，只要檢查最高兩個 byte。
   - **雜湊 → 驗證 → 之後才解析。**
   - 對照：舊的 configuration 簽章，驗簽章是「第 4 步」，在解析 DT 之後。

**相容性**（[▶ 24:59](https://youtu.be/mMlSsVGGAsI?t=1499)）：

| bootloader | FIT | 結果 |
|---|---|---|
| 新 | 舊 | 過渡期可以繼續支援 configuration 簽章 |
| 舊 | 新 | 沒問題：FIT header 加在 FDT header 之後，格式允許 |
| 新 | 新 | 用整個 FIT 的簽章 |

**推行**：現場的 FIT **同時簽 configuration 和整個 image**。過渡期後，用 bootloader policy **不再接受只有 configuration 簽章**。

**進度**（[▶ 25:31](https://youtu.be/mMlSsVGGAsI?t=1531)）：
- 寫了規範草案，跟 Simon（U-Boot 維護者）討論過，大致有共識：加這個 TLV。
- 【口頭】TLV 跟 DT 的功能有點重疊，但無法避免：如果做成相容 DT，大家就會直接用 libfdt。**他不要 intern 字串這些 DT 的複雜度出現在驗證之前**。「不是不能做得安全，而是經驗顯示這很難，我們該畫條線。」（[▶ 26:01](https://youtu.be/mMlSsVGGAsI?t=1561)）
- FIT 規範 GitHub 上的 **PR 44**。徵求合作或贊助（[▶ 26:31](https://youtu.be/mMlSsVGGAsI?t=1591)）。

---

## 8. 在那之前：流程上該做的事

[▶ 26:31](https://youtu.be/mMlSsVGGAsI?t=1591)

【口頭】**漏洞一定會發生，不管用哪種格式。**

1. **bootloader 更新要更容易**（[▶ 27:01](https://youtu.be/mMlSsVGGAsI?t=1621)）：
   - 他們多數專案用 **RAUC**，它支援的 bootloader 更新方式比較多。
   - 你的更新系統能**斷電安全地**更新 bootloader 的話，就該這樣做。
2. **security advisory**：
   - 【口頭】他花很多時間研究這些漏洞，不能期望使用者讀 commit message 就懂影響。
   - 嚴重的漏洞寫了 advisory，發在 barebox 的 GitHub。影響 U-Boot 的那個請 U-Boot 維護者簽核（[▶ 27:33](https://youtu.be/mMlSsVGGAsI?t=1653)）。
3. **申請 CVE**：
   - 【口頭】bootloader 圈裡通常只有資安研究者想申請時才申請。但寫了好的 advisory，就該申請 CVE，讓大家有理由去看。
4. **LTS**：
   - barebox 有 LTS 版。Yocto 的那一版把 barebox 放進 OE-core，那一版是 LTS，會 backport 嚴重安全修補和一般 bug 修正（[▶ 28:07](https://youtu.be/mMlSsVGGAsI?t=1687)）。
5. **migration guide**：
   - barebox 每月發版，每版都有 migration guide。
   - 【口頭】**這對安全很重要**：很多軟體的預設值當初選了，後來證明是壞的，卻不敢改，怕打壞現有使用者——結果讓更多未來的使用者受害（[▶ 28:38](https://youtu.be/mMlSsVGGAsI?t=1718)）。
   - 有 migration guide，他們就敢改。例子：barebox 以前可以在 shell 用 `boot`/`bootm` **暫時提高** FIT 簽章檢查等級（還有 build 時開關、執行時全域開關）。這讓「我現在到底在哪個等級」很難想清楚，**他們直接拿掉了**，寫在 migration notes 裡（[▶ 29:10](https://youtu.be/mMlSsVGGAsI?t=1750)）。
   - 【口頭】安全相關的東西，該養成**改預設值**的習慣（[▶ 29:41](https://youtu.be/mMlSsVGGAsI?t=1781)）。

---

## 9. 測試：你有測過「沒簽的 FIT 會被拒絕」嗎？

[▶ 29:41](https://youtu.be/mMlSsVGGAsI?t=1781)

- 【口頭】測 FIT 的陷阱太難了。
- 現場問：**有誰測過沒簽的 FIT 真的會被拒絕？** 大約 **6 個人**舉手（[▶ 30:11](https://youtu.be/mMlSsVGGAsI?t=1811)）。
- 希望更容易做到：也能確認 backport 修補後真的不受影響。

**LLM 讓這件事更急迫**（[▶ 30:41](https://youtu.be/mMlSsVGGAsI?t=1841)）：
- 【口頭】現在利用漏洞變得很容易：把簽好的 FIT、開源 repo、修補 patch 丟給 LLM，叫它做一個「有漏洞的 bootloader 會接受」的重現檔，它會照做，不需要什麼特殊的資安模型。
- 為了證明，他在 3 月用 vibe coding 做了一個網頁（「獻給我的貓」），**在瀏覽器裡**對上傳的 FIT 套用各種已知的偽造方法，下載偽造後的檔案（[▶ 31:11](https://youtu.be/mMlSsVGGAsI?t=1871)）。
  - 【口頭】「當然只能負責任地用在自己的裝置上。」
  - 目的：**驗證自己的系統是安全的。安全靠隱匿，對防守方沒有幫助**（[▶ 31:42](https://youtu.be/mMlSsVGGAsI?t=1902)）。
  - （工具網址不收錄。）

---

## 10. Q&A

【Q&A】**Q：（沒收音，從答案看是問整個 FIT 簽章能不能支援後量子密碼）**（[▶ 32:44](https://youtu.be/mMlSsVGGAsI?t=1964)）
- 他的整個 FIT 簽章想支援這個。舊格式當然也能改成支援任何東西。U-Boot 郵件列表上有一系列 patch 想加某種後量子密碼。
- 【口頭】他同意郵件列表上的意見：**應該用 Mbed TLS**。不該由 bootloader 自己維護後量子密碼（[▶ 33:14](https://youtu.be/mMlSsVGGAsI?t=1994)）。
  - U-Boot、barebox 都從 kernel 匯入密碼學程式碼，但修補通常不會跟著來，只是個案處理。他寧可用 Mbed TLS：能直接更新、API 穩定。
  - 例子：這週有人送了 barebox 的 Authenticode（UEFI PE 簽章）支援，他的回應是「不，用 Mbed TLS，沒理由匯入或自己寫 PKCS#7 解析器」（[▶ 33:45](https://youtu.be/mMlSsVGGAsI?t=2025)）。

【Q&A】**評論：除了核心工作，廠商常加一些 debug 專用功能，也能用來繞過，應該納入整體評估。**（[▶ 34:16](https://youtu.be/mMlSsVGGAsI?t=2056)）
- 同意。他去年講過 barebox **security policies**：一個通用的結構，把 debug 用的功能關在閘門後面。應該有更結構化的方式做這件事（[▶ 34:48](https://youtu.be/mMlSsVGGAsI?t=2088)）。

【Q&A】**Q：（沒收音，從答案看是問 UKI）**（[▶ 35:20](https://youtu.be/mMlSsVGGAsI?t=2120)）
- 他第一張投影片就預期有人會說 UKI。
- 【口頭】**經由 UEFI 開 kernel 有很多強化機制**：MMU 可以保持開啟、W^X（寫和執行互斥）能正常運作、kernel 可以做 KASLR。
- 所以就算不想走完整 UKI，「**在 FIT 裡用 EFI**」也很值得研究。他之後想研究（[▶ 35:53](https://youtu.be/mMlSsVGGAsI?t=2153)）。

【Q&A】**Q：（從答案看是問他怎麼驗證這些攻擊）**（[▶ 36:31](https://youtu.be/mMlSsVGGAsI?t=2191)）
- 他在顧問公司，有很多客戶。用那個網頁產生偽造的檔案（也可以上傳整個 U-Boot，它會找出裡面的 FIT 來改），**在真的硬體上開機**。今年也花了幾週讀 FIT 程式碼（[▶ 37:05](https://youtu.be/mMlSsVGGAsI?t=2225)）。
- 他開始做一個虛擬開機鏈 **bootjig**，模擬從 bootloader 到 kernel 的 secure boot 鏈，希望之後開源。
- 【口頭】目的：現在只 fuzz **解析器**，但解析器只是一部分。他想從外部對**磁碟 image** 做 fuzz，整條鏈一起測，找出更多問題並驗證修補（[▶ 37:35](https://youtu.be/mMlSsVGGAsI?t=2255)）。

---

## 11. 一頁速查表

**FIT 簽章方式與弱點**

| 方式 | 簽了什麼 | 問題 |
|---|---|---|
| 簽 image | 只有 `data` 屬性 | load／entry 等沒簽 → 可以讓執行跳到未簽資料。**根本不安全，不要用**（`uboot-sign` 的 `SPL_SIGN_ENABLE`、`mkimage -F auto` 產生的就是這種） |
| 簽 configuration | 根、`/configurations`、該 config、用到的 image 及 hash 節點、部分 strings | 驗證前要先解析 DT；FDT header、部分節點內容沒驗；**`hashed-nodes` 本身沒被保護 → CVE-2026-33243** |
| 提案：整個 FIT | header 後所有資料 | 驗證前只讀固定欄位，不解析 DT（PR 44，尚未定案） |

**混淆攻擊的模式**：讓「驗哪個節點」和「開哪個節點」指到不同地方。來源：API 的寬鬆比對（unit address、大小寫）、字串／名稱處理差異、攻擊者能選的資料（default config、`hashed-nodes`）。

**防禦教訓**
1. bootloader 不要信 `hashed-nodes`，要依 configuration 的 `kernel`/`fdt` 屬性決定雜湊什麼。
2. 驗證前不要解析不可信的結構（「解析前先驗證」）。
3. SPL 跑在最高權限，卻省掉了 libfdt 的檢查 → SPL 的 FIT 最危險。
4. **實際測試「沒簽／被改的 FIT 會被拒絕」**，修補 backport 後也要測。
5. bootloader 要能斷電安全地更新；漏洞要有 advisory＋CVE；壞的預設值要敢改。
6. 密碼學交給 Mbed TLS 這類維護良好的函式庫。

---

## 12. 延伸連結

- MT8189 上的 FIT 簽章（configuration 簽章、`required`、`setenv verify n`）：[`../verified-boot-notes/fit-sign.md`](../verified-boot-notes/fit-sign.md)
- 用本場的教訓檢查自己的 FIT：看 `fit-sign.md` 裡用的是 image 還是 configuration 簽章、U-Boot 版本有沒有 CVE-2026-33243 的修補（這是延伸建議，不是講者說的）

---

## 附：一句話總結

> **FIT 拿 device tree 當容器很方便，但驗證前就得解析一個不可信的 DT，於是「驗的節點」和「開的節點」可以被搞混。簽 image 根本不安全，簽 configuration 也因為 `hashed-nodes` 沒被保護而出了 CVE-2026-33243。講者提議改成「先驗整個檔案、再解析」，在那之前要讓 bootloader 好更新，並實際測試偽造的 FIT 會被拒絕。**

---

## ⚠️ 待確認清單

1. 沒有投影片：FIT 二進位格式圖、「哪些部分被簽」的上色圖、去年的願望清單投影片都沒有看到。

---

*筆記依據 Ahmad Fatoum〈FIT Happens: How Secure Boot Wasn't〉錄影（Whisper `turbo` 轉錄，38:12）與影片說明欄整理。沒有投影片。*
