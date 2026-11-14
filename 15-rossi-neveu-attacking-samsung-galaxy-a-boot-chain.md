---
talk: Attacking Samsung Galaxy A* Boot Chain, and Beyond
speaker: Maxime Rossi Bellom、Raphaël Neveu（Quarkslab）；共同研究 Damiano Melotti、Gabrielle Viala
conference: Black Hat USA 2024
year: 2024
video: https://youtu.be/qU9SzAo1G-s
slides: https://i.blackhat.com/BH-US-24/Presentations/BH-USA-24-Rossi-AttackingSamsung.pdf
---

# Attacking Samsung Galaxy A* Boot Chain, and Beyond [▶ 影片](https://youtu.be/qU9SzAo1G-s)

> **演講**：Maxime Rossi Bellom、Raphaël Neveu（Quarkslab），Black Hat USA 2024（投影片檔名 BH-USA-24）。Black Hat 頻道 2025-03-21 上傳。
> **來源**：YouTube 錄影（38:32）用 Whisper `turbo` 轉成逐字稿，再加上 Black Hat 官方投影片（87 頁）和影片說明欄。
> **分工**：Maxime 講 LK 的兩個漏洞（normal world），Raphaël 講 ATF 的兩個漏洞和 Keystore（secure world）。
> **標記說明**：`【口頭】` 是投影片沒有的。`【投影片補充】` 是投影片有、講者沒講的。`【Q&A】` 是現場提問。`⚠️ 逐字稿缺字` 是 Whisper 聽錯。
> **攻防內容的寫法**：只寫漏洞成因、攻擊鏈的「階段」、修補與防禦教訓。投影片上的 SMC ID、位址、heap 指標操作、分割表改寫的具體步驟**不收錄**。
> README 把講者寫成「D. Komaromy」，是錯的。
> **跟 MT8189 的關係**：這台手機用 **MediaTek SoC**，開機鏈（BootROM → preloader → ATF → TEE → LK）跟 MT8189 的 BootROM → BL2 → BL31 → OP-TEE → U-Boot 結構相同；其中一個 ATF 漏洞是 **MediaTek 自己引入、影響很多 MediaTek SoC**。

---

## 目錄

- [0. 這場演講要做什麼](#0-這場演講要做什麼)
- [1. 裝置與 MediaTek 開機鏈](#1-裝置與-mediatek-開機鏈)
- [2. 漏洞一：LK 的 JPEG 載入 heap overflow](#2-漏洞一lk-的-jpeg-載入-heap-overflow)
- [3. 漏洞二：Odin 認證繞過](#3-漏洞二odin-認證繞過)
- [4. 串起來：從 USB 到 root](#4-串起來從-usb-到-root)
- [5. 進入 secure world：ATF 的 SMC handler](#5-進入-secure-worldatf-的-smc-handler)
- [6. 漏洞三、四：ATF 越界讀取＋任意實體位址映射](#6-漏洞三四atf-越界讀取任意實體位址映射)
- [7. 偷 Keystore 金鑰](#7-偷-keystore-金鑰)
- [8. 下一步：key attestation（未完成）](#8-下一步key-attestation未完成)
- [9. 結論](#9-結論)
- [10. Q&A](#10-qa)
- [11. 一頁速查表](#11-一頁速查表)
- [12. 延伸連結](#12-延伸連結)

---

## 0. 這場演講要做什麼

[▶ 00:00](https://youtu.be/qU9SzAo1G-s?t=0)

- 一串漏洞：**經由 USB 埠**拿下 Samsung Galaxy A 系列手機，最後**洩漏存在 secure world 的祕密**。
- 研究去年在 Quarkslab 開始。

**研究的起點**（[▶ 00:31](https://youtu.be/qU9SzAo1G-s?t=31)）：
- 他們去年在 REcon 講過 Android 怎麼加密使用者資料。為此買了 Galaxy A22。
- 這台已知有 **BootROM 漏洞**，可以用開源工具 **MTKClient** 利用（[▶ 01:07](https://youtu.be/qU9SzAo1G-s?t=67)）。
- 用它繞過 secure boot 第一段，再修改系統，拿到暴力破解使用者密碼所需的所有材料。

---

## 1. 裝置與 MediaTek 開機鏈

[▶ 01:07](https://youtu.be/qU9SzAo1G-s?t=67)（p.4–8）

**裝置**（p.4）：Samsung Galaxy **A225F**（約 300 歐元），**MediaTek SoC MT6769V**，Android，MediaTek 和 Samsung 的程式混在一起，TrustZone OS 是 Samsung 的 **TEEGRIS**。
- 能用 MTKClient 繞過 secure boot → 【口頭】除錯 exploit 很方便（[▶ 01:41](https://youtu.be/qU9SzAo1G-s?t=101)）。
- 【口頭】所有漏洞都在這台上驗證過，但**同系列其他機型也適用，包括 BootROM 漏洞已經修好的機型**。

**MediaTek secure boot 流程**（p.5–6 是圖；[▶ 02:15](https://youtu.be/qU9SzAo1G-s?t=135)）：

```
BootROM（唯讀，secure EL3）
  └→ preloader（第二階段 bootloader）
       ├→ ATF（secure monitor；完整開機後權限最高的軟體）
       ├→ TEE（TEEGRIS）
       └→ LK（Little Kernel，第三階段 bootloader）→ Android
```

**LK**（p.7；[▶ 02:45](https://youtu.be/qU9SzAo1G-s?t=165)）：
- 原本開源，Android 圈很常用。負責開 Android 或其他模式（recovery）。
- 實作 **Android Verified Boot v2**：驗 Android image（`boot`、`vbmeta` 分區），有防降版。

**Samsung 改過的 LK**（p.8；[▶ 03:20](https://youtu.be/qU9SzAo1G-s?t=200)）：**閉源**，加了：
- **Odin**：經 USB 燒分區的復原協定。
- **Knox security bit**：bootloader 解鎖時讓保固失效。【口頭】「這是保護 Samsung，不是保護使用者。」
- 一個 **JPEG 解析／繪製器**：在螢幕顯示 logo 和錯誤訊息。

---

## 2. 漏洞一：LK 的 JPEG 載入 heap overflow

### 2.1 為什麼盯上 JPEG

[▶ 03:53](https://youtu.be/qU9SzAo1G-s?t=233)（p.9–10）

- JPEG 放在 **`up_param` 分區**的一個 TAR 封存檔裡。
- **封存檔有簽章，但開機時從不檢查。**
- → 任何能改內部儲存的人，都能換掉這些 JPEG。
- JPEG 解析本來就難。【口頭】他們引用 Binarly 的 **LogoFAIL**：在很多開機鏈的影像解析器裡找到大量漏洞（[▶ 04:26](https://youtu.be/qU9SzAo1G-s?t=266)）。

### 2.2 成因

[▶ 04:26](https://youtu.be/qU9SzAo1G-s?t=266)（p.11–17）

1. 在 heap 上配一個**固定大小**的緩衝區。
2. 讀 JPEG 的函式有一個「最大大小」參數：讀之前看 TAR header 裡的檔案大小，超過就報錯。
3. **但呼叫時這個參數傳的是 0，而函式的邏輯是「大小為 0 就跳過檢查」**（[▶ 05:28](https://youtu.be/qU9SzAo1G-s?t=328)）。
4. → 檔案照讀，**heap overflow**。【口頭】「找得很快。」

### 2.3 為什麼能利用

[▶ 05:28](https://youtu.be/qU9SzAo1G-s?t=328)（p.19–23）

- LK 的 heap 演算法 **miniheap**：雙向鏈結串列，所有 chunk 在同一個記憶體池，header 有 prev、next、長度。溢位會蓋到下一個 chunk 的 header（[▶ 05:58](https://youtu.be/qU9SzAo1G-s?t=358)）。
- 配置時從 free list 移除 chunk 的 unlink 操作沒有檢查 → 控制 header 就能做到**任意寫入**（[▶ 06:33](https://youtu.be/qU9SzAo1G-s?t=393)）。
- **LK 幾乎沒有緩解措施**（p.22；[▶ 07:08](https://youtu.be/qU9SzAo1G-s?t=428)）：

| 緩解措施 | LK 有嗎 |
|---|---|
| ASLR（位址隨機化） | 沒有 |
| stack canary | 沒有 |
| heap 演算法邊界檢查 | 沒有 |
| heap 不可執行 | **沒有，heap 可以執行** |

- 結果：利用策略「相當簡單」，可以在 LK 裡執行程式碼（細節不收錄）。

### 2.4 影響

[▶ 08:14](https://youtu.be/qU9SzAo1G-s?t=494)（p.31）

- **SVE-2023-2079 / CVE-2024-20832**。
- LK 裡執行程式碼。
- **持久**：重開機、恢復原廠設定都還在。因為 `up_param` 分區**恢復原廠設定時不會被清掉**。
- LK 負責開 Android，稍微修改就能**完全控制 normal world（EL1/EL0）**（[▶ 08:46](https://youtu.be/qU9SzAo1G-s?t=526)）。
- 影響他們看過的**所有 MediaTek SoC 的 Samsung 手機**，包括 MTKClient 不能用的。
- **限制**：要能寫 `up_param` 分區。

---

## 3. 漏洞二：Odin 認證繞過

[▶ 08:46](https://youtu.be/qU9SzAo1G-s?t=526)（p.32–48）

**問題**：怎麼在沒有權限的情況下，把惡意 JPEG 寫進 `up_param`？→ 看 **Odin**（也在 LK 裡）。
- 官方客戶端閉源，有一個開源客戶端 **Heimdall**，他們的 PoC 用它（[▶ 09:21](https://youtu.be/qU9SzAo1G-s?t=561)）。

**Odin 的認證怎麼決定**（p.34–36；[▶ 09:54](https://youtu.be/qU9SzAo1G-s?t=594)）：
- 燒之前會**認證** image：每個 image 尾巴要有簽章。
- 依賴兩個內部結構：
  1. **PIT**（Partition Information Table）：存在 eMMC 固定位置，描述分區。**不在 PIT 裡的分區不能燒**。PIT 可以更新，但要簽章。
  2. 一個**全域陣列**：說明每個 image 該怎麼認證。**不在陣列裡的 image 就不認證**（[▶ 10:26](https://youtu.be/qU9SzAo1G-s?t=626)）。
- 比對兩者 → 有幾個分區**可以不經認證就燒**（p.36 列了 5 個）。`up_param` 不在其中（它要認證）。
- 但其中包括 **GPT**（主、備兩份 header）（[▶ 11:01](https://youtu.be/qU9SzAo1G-s?t=661)）。
- → **不需認證，就能經 USB 改寫這台手機的分割表。**

**成因：PIT 和 GPT 兩套分區描述**（p.38–42；[▶ 11:33](https://youtu.be/qU9SzAo1G-s?t=693)）：
- PIT 用在 Samsung 的功能（Odin、JPEG 載入），GPT 用在其他地方（例如載入 Android image）。
- **LK 載入 PIT 的程式會去 GPT 裡找有沒有叫 `pit` 的分區，有的話就從那裡讀**（[▶ 12:07](https://youtu.be/qU9SzAo1G-s?t=727)）。
- **GPT 可以不經認證改寫** → 攻擊者能讓 LK 改用一份**自己提供的 PIT** → PIT 決定哪個分區叫 `up_param` → 惡意 JPEG 就被當成 `up_param` 讀進來。（具體改寫步驟不收錄。）

**影響**（p.48；[▶ 13:39](https://youtu.be/qU9SzAo1G-s?t=819)）：
- **SVE-2024-0234 / CVE-2024-20865**。
- 繞過 Odin 認證，**能燒 eMMC 上任何東西**，包括 `up_param`。
- 影響大多數 MediaTek SoC 的 Samsung 手機。

**教訓**（以下**不是逐字稿內容**，是整理的）：
- 「哪些東西要驗」不能用「白名單外的就不驗」，要預設全部都驗。
- 同一個資訊（分區配置）有兩個來源，而且一個受保護、一個不受保護時，攻擊者就會從不受保護的那個進來。

---

## 4. 串起來：從 USB 到 root

[▶ 14:12](https://youtu.be/qU9SzAo1G-s?t=852)（p.49–50；demo）

**Demo**：
1. 一開始用 adb 連線，**沒有 `su`**（正常 Android）。
2. 關機，開進 Odin 模式，執行 exploit 燒分區。
3. 中間會再進一次下載模式：再燒一個用 **Magisk** 改過的 `boot` 分區，拿 root（[▶ 15:19](https://youtu.be/qU9SzAo1G-s?t=919)）。
4. 螢幕出現 **Doge**（他們的 JPEG）→ exploit 成功。
5. 開機後 adb `su` → **root**（[▶ 15:53](https://youtu.be/qU9SzAo1G-s?t=953)）。
- 【口頭】「Samsung 可以改進的一點是開機時間。」

**小結**（p.50；[▶ 16:23](https://youtu.be/qU9SzAo1G-s?t=983)）：
- 兩個漏洞串起來 → LK 裡執行程式碼，持久，經 USB 觸發，完全控制 normal world。
- **但還拿不到 secure world 裡的祕密**（[▶ 16:57](https://youtu.be/qU9SzAo1G-s?t=1017)）。

---

## 5. 進入 secure world：ATF 的 SMC handler

[▶ 16:57](https://youtu.be/qU9SzAo1G-s?t=1017)（p.51–57；換 Raphaël 講）

**ATF 是什麼**（[▶ 17:27](https://youtu.be/qU9SzAo1G-s?t=1047)）：
- secure monitor，normal world 進 secure world 的通道。
- 例如 Android app 要 secure world 做加密運算，就請 ATF 轉交。用 **SMC** 指令觸發 EL3 例外，ATF 依 SMC ID 和暫存器參數決定做什麼（[▶ 18:04](https://youtu.be/qU9SzAo1G-s?t=1084)）。

**為什麼研究 ATF**（p.54；[▶ 18:42](https://youtu.be/qU9SzAo1G-s?t=1122)）：
- 跑在 **EL3，最高權限** → 這裡的 bug 可能是毀滅性的。
- 從 normal world 經 SMC 就能碰到（要 kernel 權限，而他們已經是 root）。
- 程式碼簡單，逆向容易。
- 但大量跟硬體的未知暫存器互動 → fuzzing 很難模擬，所以**用靜態分析**（[▶ 19:12](https://youtu.be/qU9SzAo1G-s?t=1152)）。

**取出 ATF**（p.55；[▶ 19:12](https://youtu.be/qU9SzAo1G-s?t=1152)）：
- Android ROM image 裡的 `tee-verified.img`，裡面有 ATF、TEEGRIS kernel 等。
- 檔案由多個 entry 組成，每個有自己的 header（magic、大小、名稱）。第一個 entry 剛好就是 ATF（[▶ 19:46](https://youtu.be/qU9SzAo1G-s?t=1186)）。
- 跳過 header 後看到 MediaTek 的 magic 字串，就是 ATF 的開頭（[▶ 20:22](https://youtu.be/qU9SzAo1G-s?t=1222)）。

**SMC handler**（p.56–57；[▶ 20:22](https://youtu.be/qU9SzAo1G-s?t=1222)）：
- 兩個：一個給 secure world 呼叫，一個給 **normal world（kernel）** 呼叫。後者是重點。
- SMC 的參數**直接來自 normal world，完全由攻擊者控制**（[▶ 20:52](https://youtu.be/qU9SzAo1G-s?t=1252)）。

---

## 6. 漏洞三、四：ATF 越界讀取＋任意實體位址映射

### 6.1 漏洞三：越界讀取（Samsung 引入）

[▶ 20:52](https://youtu.be/qU9SzAo1G-s?t=1252)（p.58–61）

- **成因**：某個 SMC 用攻擊者給的參數當**陣列索引**讀一個全域陣列，**完全沒檢查範圍** → 越界讀取（[▶ 21:24](https://youtu.be/qU9SzAo1G-s?t=1284)）。
- 效果：一次洩漏 4 byte，**可以讀出 ATF 虛擬位址空間裡的任何東西**（[▶ 21:58](https://youtu.be/qU9SzAo1G-s?t=1318)）。
- 限制：只能讀 ATF 自己的資料，**讀不到 TEEGRIS、trusted application 等其他 secure world 元件**。
- **SVE-2023-2215 / CVE-2024-20820**。p.61：**只有某些 Samsung 裝置有（包括 A225F），是 Samsung 引入的**。

### 6.2 漏洞四：任意實體位址映射（MediaTek 引入）

[▶ 21:58](https://youtu.be/qU9SzAo1G-s?t=1318)（p.63–68）

- **成因**：另一個 SMC 會呼叫一個（他們叫 `spm_actions` 的）函式，最後呼叫 mmap。**位址參數完全由攻擊者控制、沒有任何檢查**，只限制大小不超過 1 MB（[▶ 23:04](https://youtu.be/qU9SzAo1G-s?t=1384)）。
- 深入看，這個位址是**實體位址** → **能把任何實體位址映射進 ATF 的虛擬位址空間**。
- **跟漏洞三串起來 → 能讀 secure world 的任何東西**，包括 TEEGRIS kernel、trusted application（[▶ 23:35](https://youtu.be/qU9SzAo1G-s?t=1415)）。
- 限制：映射後不能解除，最多連續 8 次（第 9 次會當機），所以**最多洩漏 8 MB**。【口頭】對他們要做的事已經夠了。
- **CVE-2024-20021**。p.68：**由 MediaTek 引入，影響大量 MediaTek SoC**。

**教訓**（以下**不是逐字稿內容**，是整理的）：
- **EL3 的每個 SMC handler 都必須把 normal world 傳進來的每個參數當成不可信**：索引要檢查範圍、位址要檢查是不是允許的區域。
- 一個「只能讀自己」的小 bug，加上一個「能映射任何位址」的 bug，就變成整個 secure world 外洩。
- **平台專屬的 SiP SMC**（廠商自己加的）是 ATF 最容易出事的地方，因為它不在上游 TF-A 的審查範圍內。

---

## 7. 偷 Keystore 金鑰

[▶ 24:07](https://youtu.be/qU9SzAo1G-s?t=1447)（p.69–73）

**Android Keystore**（p.70；[▶ 24:07](https://youtu.be/qU9SzAo1G-s?t=1447)）：
- 提供金鑰儲存和加密服務給 normal world。
- 金鑰以**加密的 key blob** 存在 Android 檔案系統，**Android 沒辦法處理原始金鑰，只有 secure world 解得開**。
- 三種保護等級：純軟體、**TEE（預設）**、硬體（StrongBox）。他們針對 TEE 等級。
- 原則：**原始金鑰永遠不離開 TrustZone 提供的受保護環境**（[▶ 24:45](https://youtu.be/qU9SzAo1G-s?t=1485)）。

**運作流程**（[▶ 24:45](https://youtu.be/qU9SzAo1G-s?t=1485)）：
1. normal world 送 **begin operation** 請求，附上 key blob。
2. secure world 的 Keymaster TA 解開 key blob，**原始金鑰放進 secure memory**。
3. 之後送幾次 update（選演算法、參數……）。這段期間**金鑰一直在記憶體裡**（[▶ 25:20](https://youtu.be/qU9SzAo1G-s?t=1520)）。
4. TA 回傳結果，金鑰從記憶體清掉。

**PoC 的階段**（p.72；[▶ 25:53](https://youtu.be/qU9SzAo1G-s?t=1553)）：
1. 匯入一把金鑰到 Keystore，用它加密一段資料。
2. 在 begin operation 之後**暫停執行**，確保金鑰還在 secure memory。
3. 用兩個 ATF 漏洞洩漏那塊記憶體（8 MB）。
4. 在洩漏的資料裡逐一嘗試，找出能解開密文的金鑰。

**Demo**（[▶ 26:30](https://youtu.be/qU9SzAo1G-s?t=1590)）：
- 用 **Frida** 在 normal world hook 函式、在 begin operation 後暫停，再跑洩漏 script。
- 加密字串「Quarkslab」。一次只能洩漏 4 byte，所以要送很多次 SMC，要一點時間（[▶ 27:37](https://youtu.be/qU9SzAo1G-s?t=1657)）。
- 最後**找到金鑰**。【口頭】demo 用的是全是 A 的金鑰，方便展示；用產生的金鑰也一樣行（[▶ 29:17](https://youtu.be/qU9SzAo1G-s?t=1757)）。

---

## 8. 下一步：key attestation（未完成）

[▶ 29:17](https://youtu.be/qU9SzAo1G-s?t=1757)（p.74–85）

【口頭】在 OffensiveCon 講到上一節就結束了，但有人問「那 key attestation 呢？」

**Key attestation**（p.75；[▶ 29:53](https://youtu.be/qU9SzAo1G-s?t=1793)）：
- 證明一把金鑰對存在安全硬體（TrustZone 或安全晶片）裡。
- 附帶裝置狀態：**bootloader 有沒有鎖、verified boot 狀態**、各種 ID（IMEI 等）。
- SafetyNet 之類的框架用它判斷裝置有沒有被攻破（例如銀行 app 不想在 root 過的裝置上跑）（[▶ 30:24](https://youtu.be/qU9SzAo1G-s?t=1824)）。

**測試**（p.76–77；[▶ 30:59](https://youtu.be/qU9SzAo1G-s?t=1859)）：
- 用開源 app 產生並檢查 attestation：**看起來一切正常，exploit 沒被偵測到**。
- 用另一個基於 **SafetyNet** 的開源 app：**偵測到了**。
  - 【口頭】可能是 SafetyNet 偵測 Magisk 的經驗法則；也可能是 attestation 裡有 **boot 分區的雜湊**，他們改了 boot 分區所以雜湊變了。確切原因不清楚（[▶ 31:32](https://youtu.be/qU9SzAo1G-s?t=1892)）。

**憑證鏈**（p.78–81；[▶ 31:32](https://youtu.be/qU9SzAo1G-s?t=1892)）：

| 層 | 金鑰 | 特性 |
|---|---|---|
| 根 | 自簽的根憑證 | 私鑰在 Google |
| **GAK**（Google Authenticated Key） | 存在裝置 Keystore | **很多台裝置共用同一把**（至少他們看過的兩台 A22 5G 一樣，推測整個型號都一樣）（[▶ 32:03](https://youtu.be/qU9SzAo1G-s?t=1923)） |
| Android Keystore key | 存在裝置 | 每台不同 |
| 應用程式金鑰 | 跟 attestation 一起產生 | — |

- **為什麼盯 GAK**（[▶ 33:06](https://youtu.be/qU9SzAo1G-s?t=1986)）：拿到它，就能自己產生「合法」的 attestation、**自己決定裡面寫什麼**（例如 bootloader 已鎖）；而且因為很多台共用，**洩漏一次就能替很多裝置偽造**。
- GAK 也以一般 Keystore 的格式存在檔案系統，所以策略跟第 7 節類似。
- **現況：還卡在第一步**（要偽造一個合法的 begin 請求，需要更多逆向）。【口頭】「不算失敗，是未完成的事。」（[▶ 34:41](https://youtu.be/qU9SzAo1G-s?t=2081)）

**教訓**（以下**不是逐字稿內容**）：attestation 的信任建立在「金鑰離不開 TEE」上。只要 TEE 記憶體能被讀出，而且某一層金鑰是多台共用的，一台被攻破就能連累同型號所有裝置的 attestation。

---

## 9. 結論

[▶ 34:41](https://youtu.be/qU9SzAo1G-s?t=2081)（p.86）

- **四個漏洞**：
  1. Odin 認證繞過 → 經 USB 觸發
  2. LK 程式碼執行，有持久性
  3. ＋4. 洩漏 secure world 記憶體，包括 Keystore 金鑰
- 能不能洩漏 attestation 金鑰：還不清楚。
- **影響**：所有 MediaTek SoC 的 Samsung 手機，主要是中低階機。
- 【口頭】**漏洞都很簡單**，code review（有些用 fuzzing）就能找到，**但影響非常大**，部分原因是 **LK 和 ATF 都沒有緩解措施**（[▶ 35:44](https://youtu.be/qU9SzAo1G-s?t=2144)）。
- 全部回報給 Samsung，**都已修補**。【口頭】感謝 Samsung 安全團隊處理得很快。

---

## 10. Q&A

【Q&A】**Q：結論說只有中低階機，高階機呢？**（[▶ 36:16](https://youtu.be/qU9SzAo1G-s?t=2176)）
- 這些 bug 只適用 MediaTek SoC 的手機，不確定 Samsung 有沒有用 MediaTek 的高階機。「也許下次可以帶高階機的 bug 來。」（[▶ 36:56](https://youtu.be/qU9SzAo1G-s?t=2216)）
- 都修好了，記得更新韌體。

【Q&A】**Q：MediaTek 打算加緩解措施（ASLR 之類）嗎？**（[▶ 37:28](https://youtu.be/qU9SzAo1G-s?t=2248)）
- 很難替他們回答。講者預期會有。
- 【口頭】他認為有些高階裝置已經有了（[▶ 37:59](https://youtu.be/qU9SzAo1G-s?t=2279)）。

---

## 11. 一頁速查表

**攻擊鏈（四個漏洞）**

```
USB（Odin 模式）
 └[漏洞二] GPT 可免認證改寫 → LK 改讀攻擊者的 PIT → 惡意 JPEG 被當成 up_param
     └[漏洞一] LK JPEG 載入：最大大小傳 0 → 跳過檢查 → heap overflow → LK 執行程式碼（持久）
         └→ 開 Android 時加 Magisk → root（normal world EL1）
             └[漏洞三] ATF SiP SMC：索引沒檢查 → 讀 ATF 全部記憶體（Samsung 引入）
             └[漏洞四] ATF SiP SMC：實體位址沒檢查 → 映射任何實體位址（MediaTek 引入）
                 └→ 讀 TEEGRIS／Keymaster 記憶體 → 在 begin operation 後抓到 Keystore 金鑰
```

| CVE | 元件 | 成因 | 誰引入 |
|---|---|---|---|
| CVE-2024-20865（SVE-2024-0234） | Odin（LK） | 不在認證陣列裡的分區就不驗；GPT 可改，PIT 從 GPT 找 | Samsung |
| CVE-2024-20832（SVE-2023-2079） | LK JPEG | 大小 0 跳過檢查；簽章不驗 | Samsung |
| CVE-2024-20820（SVE-2023-2215） | ATF SMC | 陣列索引沒檢查 | Samsung（部分機型） |
| CVE-2024-20021 | ATF SMC | mmap 的實體位址沒檢查 | **MediaTek（很多 SoC）** |

**防禦教訓**
1. **簽了就要驗**：`up_param` 有簽章卻不驗，等於沒簽。
2. **預設要驗**：「沒列到的就不驗」的白名單設計會被鑽。
3. 同一份配置資訊（PIT／GPT）不能有一個受保護、一個不受保護的來源。
4. bootloader 和 EL3 也需要基本緩解：ASLR、canary、heap 不可執行、heap 完整性檢查。
5. **EL3 SMC handler 的每個參數都不可信**：範圍、位址都要檢查。廠商自加的 SiP SMC 最危險。
6. 持久性來自「恢復原廠不清的分區」：裡面的東西更要驗。

---

## 12. 延伸連結

- MT8189 的 BL31（TF-A）SiP SMC 與 SMC 流程：[`../tf-a-and-op-tee-note/smc-call-flow.md`](../tf-a-and-op-tee-note/smc-call-flow.md)、[`../tf-a-and-op-tee-note/tfa-intro.md`](../tf-a-and-op-tee-note/tfa-intro.md)
- MT8189 的 secure memory 劃分：[`../tf-a-and-op-tee-note/secure-memory.md`](../tf-a-and-op-tee-note/secure-memory.md)
- 延伸建議（不是講者說的）：MT8189 用的 TF-A 2.6 有沒有 CVE-2024-20021 那個 `spm_actions` 類型的 SiP SMC，可以在 `plat/mediatek/` 底下查。

---

## 附：一句話總結

> **從 USB 進 Odin，利用「GPT 不用驗」換掉 PIT、讓 LK 讀進惡意 JPEG 觸發 heap overflow，拿下 normal world；再用兩個 ATF SiP SMC 沒檢查參數的 bug（其中一個是 MediaTek 引入、影響很多 SoC），讀出整個 secure world，偷到 Keystore 金鑰。漏洞都很簡單，卻因為 LK 和 ATF 毫無緩解措施而影響巨大。**

---

*筆記依據 Maxime Rossi Bellom、Raphaël Neveu〈Attacking Samsung Galaxy A* Boot Chain, and Beyond〉（Black Hat USA 2024）錄影（Whisper `turbo` 轉錄，38:32）與 Black Hat 官方投影片整理。*
