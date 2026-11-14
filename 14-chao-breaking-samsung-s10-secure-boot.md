---
talk: "Breaking Samsung's Root of Trust: Exploiting Samsung S10 Secure Boot"
speaker: Jeff Chao（Jeffxx；Trapa Security，HITCON CTF、Chroot）
conference: Black Hat USA 2020（線上）
year: 2020
video: https://youtu.be/BwFtOrkKlbo
slides: https://i.blackhat.com/USA-20/Wednesday/us-20-Chao-Breaking-Samsungs-Root-Of-Trust-Exploiting-Samsung-Secure-Boot.pdf
---

# Breaking Samsung's Root of Trust: Exploiting Samsung S10 Secure Boot [▶ 影片](https://youtu.be/BwFtOrkKlbo)

> **演講**：Jeff Chao（Jeffxx，Trapa Security；前 TeamT5），Black Hat USA 2020。Black Hat 頻道 2021-02-26 上傳。
> **來源**：YouTube 錄影（36:36）用 Whisper `turbo` 轉成逐字稿，再加上 Black Hat 官方投影片（77 頁）。
> **標記說明**：`【口頭】` 是投影片沒有的。`【投影片補充】` 是投影片有、講者沒講的。`【Q&A】` 是現場（線上）提問。`⚠️ 逐字稿缺字` 是 Whisper 聽錯。`⚠️ 待確認` 是查不清楚的地方。
> **攻防內容的寫法**：只寫漏洞成因、攻擊鏈的「階段」、修補方式和防禦教訓。投影片上的記憶體位址、緩衝區大小、heap 利用細節、逐步操作都**不收錄**。
> README 把講者寫成「G. Beniamini et al.」，是錯的；投影片和逐字稿都是 Jeff Chao。

---

## 目錄

- [0. 這場演講要做什麼](#0-這場演講要做什麼)
- [1. 背景：Samsung Knox 的 trusted boot](#1-背景samsung-knox-的-trusted-boot)
- [2. 威脅情境：關機、鎖著、不知道密碼](#2-威脅情境關機鎖著不知道密碼)
- [3. 攻擊面：S-Boot 的 Odin 下載模式](#3-攻擊面s-boot-的-odin-下載模式)
- [4. 漏洞一：Odin 燒錄指令沒檢查大小](#4-漏洞一odin-燒錄指令沒檢查大小)
- [5. 漏洞二：修補被另一個參數繞過](#5-漏洞二修補被另一個參數繞過)
- [6. 漏洞三：PIT 指令的 heap overflow（S10）](#6-漏洞三pit-指令的-heap-overflows10)
- [7. 拿到 S-Boot 執行權之後](#7-拿到-s-boot-執行權之後)
- [8. 結論與時間線](#8-結論與時間線)
- [9. Q&A](#9-qa)
- [10. 一頁速查表](#10-一頁速查表)
- [11. 延伸連結](#11-延伸連結)

---

## 0. 這場演講要做什麼

[▶ 00:31](https://youtu.be/BwFtOrkKlbo?t=31)（p.3）

1. Demo 影片：漏洞可以被利用的情境。
2. Samsung 的安全框架 **Knox**，以及前人對 Knox 的研究。
3. 他找到的漏洞，以及怎麼用它們攻破 secure boot。
4. 攻破 secure boot 之後，**即使不知道密碼**還能造成什麼傷害。

（[▶ 01:06](https://youtu.be/BwFtOrkKlbo?t=66)～[▶ 03:23](https://youtu.be/BwFtOrkKlbo?t=203) 是 demo 影片，Whisper 轉出來是無意義的文字，略過。）

---

## 1. 背景：Samsung Knox 的 trusted boot

[▶ 03:23](https://youtu.be/BwFtOrkKlbo?t=203)（p.5–11）

**Knox**：建在 TrustZone 上、非常龐大複雜的整機安全強化。包括 TIMA（TrustZone 為基礎的完整性量測架構）、即時 kernel 保護、週期性 kernel 量測、SELinux 強化等，防提權和未授權存取資料。這場只談 **secure boot**（[▶ 03:53](https://youtu.be/BwFtOrkKlbo?t=233)）。

**開機鏈**（p.7；[▶ 04:27](https://youtu.be/BwFtOrkKlbo?t=267)）：

| 段 | 做什麼 |
|---|---|
| 硬體 **PBL**（Primary Boot Loader） | 驗並載入 S-Boot。驗章金鑰在製造時存進硬體。**PBL 改不了**，所以只能開官方簽的 S-Boot |
| **S-Boot**（Samsung 的第二階段 bootloader） | 設好 monitor mode 的 handler 後降權；請 EL3 初始化 TEE OS；驗並載入 hypervisor（`uh.bin`）；驗並載入 kernel（`boot.img`） |
| kernel＋dm-verity | 驗並掛載 `system.img`、`vendor.img` |

**驗證失敗時，S-Boot 不是拒絕開機**（[▶ 05:01](https://youtu.be/BwFtOrkKlbo?t=301)）：
- 如果 boot image 簽章不對，S-Boot **還是會開**，但多做一件事：**燒掉 Knox bit**。

**Knox bit（warranty bit）**（p.8；[▶ 05:39](https://youtu.be/BwFtOrkKlbo?t=339)）：
- 一次性 fuse，燒了不能恢復。
- Samsung 保固看這個 bit。
- 燒了之後，TrustZone 裡一些服務就**不能啟動**：Knox Container、Samsung Pay、Trusted Key Store 等。

**敏感資料保護**（p.9–10；[▶ 06:16](https://youtu.be/BwFtOrkKlbo?t=376)）：
- Galaxy S9 起，儲存預設加密。**第一次解鎖螢幕後才解密**。
- 加密金鑰在 TrustZone 的應用程式（trustlet）裡。**就算有 root，沒解鎖也解不開儲存**。
- 很多關鍵資料只有 trustlet 解得開；Knox bit 燒了，大多數就不能用了（[▶ 06:50](https://youtu.be/BwFtOrkKlbo?t=410)）。

**所以要拿到敏感資料，兩條路**（[▶ 07:24](https://youtu.be/BwFtOrkKlbo?t=444)）：
1. 提權到 **secure world**。
2. 讓裝置以為 **Knox bit 還沒被燒**。

> ⚠️ 逐字稿缺字：「NUCS／Lux／next bit／Nux bit」＝Knox、Knox bit；「PVL」＝PBL；「Trostone／TrustLong」＝TrustZone。

### 1.1 前人研究

[▶ 07:24](https://youtu.be/BwFtOrkKlbo?t=444)（p.13–15）

| 研究 | 從哪到哪 |
|---|---|
| Black Hat USA 2017，returnsme：攻破 Knox 即時 kernel 保護 | non-secure EL0 → non-secure EL1 |
| Black Hat Europe 2017，騰訊實驗室：攻 Samsung Pay trustlet | non-secure EL0 → secure EL1（投影片寫 secure EL0） |
| 2019（Black Hat USA 2019），Quarkslab | non-secure EL0 → **secure EL3**（Kinibi，S8 以前） |

**共同點**：全部都**至少要 non-secure EL0 的權限**，也就是手機要開著、能跑程式（[▶ 08:28](https://youtu.be/BwFtOrkKlbo?t=508)）。

> 前人研究的 EL 對應，口頭和投影片有一處不同（騰訊那個：口頭 secure EL1，p.14 secure EL0），兩邊都記下來。

---

## 2. 威脅情境：關機、鎖著、不知道密碼

[▶ 09:02](https://youtu.be/BwFtOrkKlbo?t=542)（p.16–17）

- **如果手機是關機的，也不知道密碼呢？**
- 這場的目標：從**手機外面**（鎖著的手機）打進 **non-secure EL1**，並讓 TrustZone 裡的敏感資料**仍然拿得到**。

---

## 3. 攻擊面：S-Boot 的 Odin 下載模式

[▶ 09:02](https://youtu.be/BwFtOrkKlbo?t=542)（p.18–19、21）

- 一般流程：S-Boot 設好 secure monitor、初始化硬體、驗 boot image、開 kernel。
- **開機時按住「音量下＋電源」，S-Boot 會進 Odin 模式**（[▶ 09:37](https://youtu.be/BwFtOrkKlbo?t=577)）。
  - 用途：讓使用者手動燒官方韌體。
  - 不只驗簽章，**也檢查版本號**：不能燒舊版或非官方韌體（**防降版**）。
- 【口頭】**這開出了一條和 S-Boot 互動的通道**。他在 Odin 模式裡找到好幾個能任意執行程式碼的漏洞（[▶ 10:12](https://youtu.be/BwFtOrkKlbo?t=612)）。

**Odin 請求的格式**（p.21；[▶ 10:44](https://youtu.be/BwFtOrkKlbo?t=644)）：一個整數 opcode（選功能：初始化／設定、燒分割表 PIT、燒 image……），一個 sub-op（設定、讀取、初始化……），再加幾個參數。

---

## 4. 漏洞一：Odin 燒錄指令沒檢查大小

[▶ 11:15](https://youtu.be/BwFtOrkKlbo?t=675)（p.20–28）

**成因**：
- 燒 image 的指令，**image 大小由使用者提供，完全沒檢查**。
- 決定緩衝區位置的邏輯有**整數溢位**，攻擊者可以選擇用哪個緩衝區位置。
- 緩衝區後面放的是 **S-Boot 的程式碼、資料、stack、heap**。沒有大小檢查，就能整片覆蓋（[▶ 11:51](https://youtu.be/BwFtOrkKlbo?t=711)）。

**攻擊鏈的階段**（細節不收錄）：
1. S8 起，Samsung 把 MMU 表收緊，程式碼段設成唯讀。
2. **但 USB 控制器用 DMA 直接寫記憶體，不受 MMU 權限限制**（[▶ 11:51](https://youtu.be/BwFtOrkKlbo?t=711)）。
3. 還要處理 CPU cache 和 DMA 寫入不一致的問題（[▶ 12:23](https://youtu.be/BwFtOrkKlbo?t=743)）。
4. 結果：在 S-Boot 裡任意執行程式碼。只適用 S8 以前（[▶ 14:01](https://youtu.be/BwFtOrkKlbo?t=841)）。

**為什麼 S9 以後不行、以及嘗試**（p.28–32；[▶ 14:33](https://youtu.be/BwFtOrkKlbo?t=873)）：
- S9 起 Odin 加了**平行下載**功能（要多開兩顆 CPU 核心），緩衝區搬到離 S-Boot 程式碼很遠的地方。
- 核心開不起來時會**退回一般下載模式**，緩衝區又回到原位。
- 他找到 S-Boot 有一個 **UART 除錯模式**，裡面的測試指令可以讓「已開核心數」一直累加，使之後開核心失敗（[▶ 15:41](https://youtu.be/BwFtOrkKlbo?t=941)）。
- 但進 UART 模式要靠 USB 線上**特定的電阻值**。S7 有人成功過；S8 起換成 Type-C，他試了各種 Type-C 做法都失敗（[▶ 16:48](https://youtu.be/BwFtOrkKlbo?t=1008)）。
- 【口頭】試了半年，放棄（[▶ 17:20](https://youtu.be/BwFtOrkKlbo?t=1040)）。

**回報與修補**（p.34–38；[▶ 17:20](https://youtu.be/BwFtOrkKlbo?t=1040)）：
- 2019 年 8 月回報，幾天後 Samsung 說**重複了**（別人已報過）。【口頭】「真是一大打擊」，他轉去研究別的。
- 修補：2019 年 10 月安全更新，**SVE-2019-15230**「Bootloader 中可能的整數溢位」。
- 【口頭】看描述，他猜原報告者沒發現這個 bug 能導致任意程式碼執行（[▶ 17:56](https://youtu.be/BwFtOrkKlbo?t=1076)）。
- 修補說是修了「無號比較」問題，但實際上 Samsung **還加了大小檢查**防溢位（[▶ 18:26](https://youtu.be/BwFtOrkKlbo?t=1106)）。

> 投影片 p.34 寫「2019 年 8 月回報」，p.76 時間線寫「2019-10-02 回報漏洞一」。兩者不同。⚠️ 待確認

---

## 5. 漏洞二：修補被另一個參數繞過

[▶ 18:26](https://youtu.be/BwFtOrkKlbo?t=1106)（p.42–49）

**成因**：
- 看完修補，他想有沒有辦法繞過那個新檢查（[▶ 19:01](https://youtu.be/BwFtOrkKlbo?t=1141)）。
- USB 接收的大小，是用另一個全域值做對齊算出來的。
- 那個值**可以透過 Odin 請求設定**（從 debug 訊息看，是「資料封包大小」），而且**沒有任何檢查**（[▶ 19:33](https://youtu.be/BwFtOrkKlbo?t=1173)）。
- 把封包大小設大，就繞過 2019 年 10 月的檢查，**再利用同一個緩衝區**，跟漏洞一一樣拿到執行權。

**修補**：2020 年 1 月，**SVE-2019-15872**，加了檢查限制資料封包大小的上限（[▶ 20:05](https://youtu.be/BwFtOrkKlbo?t=1205)）。

**教訓**（以下**不是逐字稿內容**，是依這兩個漏洞整理的）：修補只檢查了「使用者直接給的大小」，沒有檢查「影響最後大小的所有輸入」。一個修補要看整條資料流。

---

## 6. 漏洞三：PIT 指令的 heap overflow（S10）

[▶ 20:37](https://youtu.be/BwFtOrkKlbo?t=1237)（p.52–62）

【口頭】看到漏洞二的修補，他靈光一閃，**三小時後**想出另一個利用方式。這次**能打 S10**。

**成因**：
1. Odin 有一個燒**分割表（PIT）**的指令。PIT 很小，所以放在一個小的 **heap 緩衝區**，不是前面那個大緩衝區（[▶ 20:37](https://youtu.be/BwFtOrkKlbo?t=1237)）。
2. 有檢查確保大小不超過 heap 緩衝區。
3. **但漏洞二的修補只把「資料封包大小」限制在一個上限，那個上限比 PIT 的 heap 緩衝區大**（[▶ 21:14](https://youtu.be/BwFtOrkKlbo?t=1274)）→ 有機會 heap overflow。
4. 接收程式只有在「第一次沒收到足夠資料」時，才會用封包大小再收一次（[▶ 21:46](https://youtu.be/BwFtOrkKlbo?t=1306)）。而 USB 接收函式會一直等到收滿才回來，就算傳得很慢也一樣。
5. 【口頭】他們其實**一開始就發現這個 bug，但以為沒辦法利用**（沒辦法讓接收「收不滿就回來」），所以把時間花在漏洞一上（[▶ 22:54](https://youtu.be/BwFtOrkKlbo?t=1374)）。
6. **關鍵想法：在傳輸中途拔掉再插回 USB 線**，第一次接收就會在資料不足時回來，走到第二次接收，造成 heap overflow（[▶ 23:25](https://youtu.be/BwFtOrkKlbo?t=1405)）。
7. 之後是傳統的 heap 利用：S-Boot 的 heap **沒有檢查雙向鏈結串列**，可以偽造 chunk，最後蓋掉 stack 上的返回位址，取得執行權（[▶ 24:05](https://youtu.be/BwFtOrkKlbo?t=1445)）。（細節不收錄。）

**修補**：p.76 時間線：2020-01-21 回報，2020-05-06 修補，**SVE-2020-16712**。

**教訓**（以下**不是逐字稿內容**，是整理的）：
- 「實體上中斷傳輸」也是一種輸入。接收函式在錯誤路徑上的行為要跟正常路徑一樣嚴格。
- heap 實作缺少基本的完整性檢查（unlink 檢查），讓溢位很容易變成任意寫入。

---

## 7. 拿到 S-Boot 執行權之後

[▶ 25:43](https://youtu.be/BwFtOrkKlbo?t=1543)（p.63–74）

### 7.1 讓手機繼續開機，Knox bit 不被燒

[▶ 26:17](https://youtu.be/BwFtOrkKlbo?t=1577)

- 漏洞把 S-Boot 的資料、stack、heap 弄亂了，很難復原，所以**重新跑 S-Boot 的開機流程**。
- 他們只有 non-secure EL1，而 TrustZone 有些東西已經初始化過、**不能初始化兩次**，所以要**跳過 TrustZone 相關的呼叫**，讓 TrustZone 保持穩定（p.65）。
- 繼續開機，一直到 **kernel 已經載入記憶體、通過驗證**之後，**把記憶體裡的 kernel 換成自己的**，再開機（[▶ 26:49](https://youtu.be/BwFtOrkKlbo?t=1609)）。
- 結果：拿到 non-secure EL1（root），而且因為沒有走「驗證失敗」那條路，**Knox bit 沒被燒，TrustZone 裡的資料都還在**（[▶ 27:57](https://youtu.be/BwFtOrkKlbo?t=1677)）。

**這就是 TOCTOU**：S-Boot 驗的是載入時的 kernel，跑的卻是驗完後被換掉的 kernel。講者沒用這個詞。

### 7.2 但手機還是鎖著的

[▶ 27:57](https://youtu.be/BwFtOrkKlbo?t=1677)（p.69–74）

- 沒有螢幕密碼，**儲存還是加密的**。金鑰在 **gatekeeper trustlet** 裡。Samsung Pay trustlet 裡的信用卡資料也拿不到。
- 幾種方式（[▶ 28:31](https://youtu.be/BwFtOrkKlbo?t=1711)）：
  1. **等使用者自己解鎖**（demo 影片就是這個情境）。
  2. 待在 non-secure kernel，**攔截／竊聽 normal world 和 secure world 之間的所有請求**。
  3. **攻擊 trustlet**：Knox bit 沒燒，secure world 的資料還在，暴露了攻擊面（[▶ 29:04](https://youtu.be/BwFtOrkKlbo?t=1744)）。
     - 【口頭】他們團隊 2019 年找到十幾個漏洞，2020 年還在找；其他研究者找到的多十倍。**這些全都至少要 non-secure 的權限**，而現在他們有了（[▶ 29:35](https://youtu.be/BwFtOrkKlbo?t=1775)）。
     - 例子：2019 年 5 月回報的 gatekeeper trustlet 漏洞 **SVE-2019-14575**，可以暴力破解螢幕密碼。【口頭】依他們測試，**幾小時就能試完所有圖形密碼**（[▶ 30:05](https://youtu.be/BwFtOrkKlbo?t=1805)）。
     - 跟它組合，就能解鎖手機、拿到敏感資料。

---

## 8. 結論與時間線

[▶ 30:05](https://youtu.be/BwFtOrkKlbo?t=1805)（p.75–76）

- **資料存在 secure world，不代表 100% 安全。**
- **但確實讓攻擊變難**：要串好幾個漏洞才拿得到受保護的資料（[▶ 30:35](https://youtu.be/BwFtOrkKlbo?t=1835)）：
  1. **登陸**：遠端程式碼執行、本地 USB（secure boot）漏洞、或社交工程。
  2. 提權到 non-secure EL1。
  3. trustlet 的漏洞，進 secure world EL0。
  4. 從 secure EL0 提權到 secure EL1 或 EL3（要拿全部資料、控制整台時）。
- **少了任何一步（特別是 2、3、4），手機裡的資料就還是安全的**（[▶ 31:05](https://youtu.be/BwFtOrkKlbo?t=1865)）。

**時間線**（p.76）：

| 日期 | 事件 |
|---|---|
| 2019-10-02 | 回報漏洞一 |
| 2019-10-08 | 被告知漏洞一重複 |
| 2019-10-11 | 回報漏洞二 |
| 2020-01-06 | Samsung 修補，SVE-2019-15872 |
| 2020-01-21 | 回報漏洞三 |
| 2020-05-06 | Samsung 修補，SVE-2020-16712 |

---

## 9. Q&A

（線上會議，問題是講者唸出來的。）

【Q&A】**Q：使用者重開機的話，裝置會正常開回原本的韌體嗎？**（[▶ 32:24](https://youtu.be/BwFtOrkKlbo?t=1944)）
- 會。他們**沒有改韌體**，重開就是原本的韌體。

**推論**（以下**不是逐字稿內容**）：攻擊只存在於這一次開機的記憶體裡，不留痕跡，也代表每次都要重新攻擊一次。

【Q&A】**Q：Samsung 每款手機有不同硬體版本，你們打的是哪一款？**（[▶ 33:44](https://youtu.be/BwFtOrkKlbo?t=2024)）
- 打的是美國賣的硬體版本（[▶ 33:44](https://youtu.be/BwFtOrkKlbo?t=2024)）。
- S10、S9、S8 的 **Exynos** 版本都受影響（[▶ 34:18](https://youtu.be/BwFtOrkKlbo?t=2058)）。
  > ⚠️ 逐字稿缺字：「Xenose」推測是 Exynos。但前一句說打的是美國版，美國版 S10 通常是 Snapdragon，兩句可能有矛盾。⚠️ 待確認

【Q&A】**Q：怎麼看到開機資訊的？**（[▶ 34:18](https://youtu.be/BwFtOrkKlbo?t=2058)）
- 逆向 boot image（S-Boot）。demo 影片裡是進 Odin 模式就能看到開機模式資訊（[▶ 34:48](https://youtu.be/BwFtOrkKlbo?t=2088)）。

（另一題是問某兩個 SVE 編號，講者找不到，改用文字回答，沒錄到。）

---

## 10. 一頁速查表

**信任鏈與破口**

```
PBL（硬體，改不了）─驗→ S-Boot ─驗→ hypervisor、kernel ─dm-verity→ system/vendor
                         │
                         ├─ 驗證失敗：照樣開機，但燒 Knox bit（TrustZone 服務停用）
                         └─ Odin 下載模式（音量下＋電源）：USB 上的指令解析 ← 攻擊面
```

| 漏洞 | 成因 | 修補 |
|---|---|---|
| 一（S8 以前） | 燒錄指令的大小沒檢查＋整數溢位 → 覆蓋 S-Boot 記憶體；USB DMA 不受 MMU 唯讀保護 | SVE-2019-15230（2019-10），加大小檢查 |
| 二 | 修補沒管到另一個可由 Odin 設定的「封包大小」 | SVE-2019-15872（2020-01），限制封包大小 |
| 三（S10） | 封包大小上限仍大於 PIT 的 heap 緩衝區；中途拔 USB 線讓接收走第二條路 → heap overflow；heap 沒有 unlink 檢查 | SVE-2020-16712（2020-05） |

**防禦教訓**
1. **bootloader 的下載／燒錄模式是攻擊面**：所有從 USB 進來的大小、參數都要檢查，包括間接影響大小的參數。
2. **DMA 不受 CPU 的 MMU 權限限制**：把程式碼設成唯讀，擋不住 DMA 寫入（要靠 IOMMU 之類的機制）。
3. 修補要看整條資料流，不能只補報告裡那一個點。
4. **驗完再執行之間不能被換掉**（TOCTOU）：一旦 bootloader 被拿下，「驗證過的 kernel」可以在記憶體裡被替換，Knox bit 也不會燒。
5. 「驗證失敗就燒 fuse、但照樣開機」的設計，保護的是 TrustZone 資料；只要繞過驗證本身，這層保護就不起作用。
6. 縱深防禦有效：拿下 bootloader 後，還要 trustlet 漏洞才能解開加密資料。

---

## 11. 延伸連結

- TrustZone、EL 分層、secure world 才能存取的資料：[`../tf-a-and-op-tee-note/secure-memory.md`](../tf-a-and-op-tee-note/secure-memory.md)、[`../tf-a-and-op-tee-note/optee-intro.md`](../tf-a-and-op-tee-note/optee-intro.md)
- 同類的「下載模式」：MT8189 的 BootROM 下載模式與 LK（Download Agent），見 `../ufs-emmc-notes/lk-flash-ufs.md`（延伸建議，不是講者說的）

---

## 附：一句話總結

> **Samsung S-Boot 的 Odin 下載模式在處理 USB 指令時，大小檢查一錯再錯（修補兩度被繞過），讓攻擊者從關機、上鎖的手機拿下 bootloader，再在驗證後換掉 kernel、保住 Knox bit；但要真正解開資料，還得再串一個 trustlet 漏洞。**

---

## ⚠️ 待確認清單

1. 漏洞一的回報日期：p.34 寫 2019 年 8 月，p.76 時間線寫 2019-10-02。
2. [▶ 33:44](https://youtu.be/BwFtOrkKlbo?t=2024) 受影響版本：講者說打的是美國版，又說 Exynos 版都受影響。

---

*筆記依據 Jeff Chao〈Breaking Samsung's Root of Trust: Exploiting Samsung S10 Secure Boot〉（Black Hat USA 2020）錄影（Whisper `turbo` 轉錄，36:36）與 Black Hat 官方投影片整理。*
