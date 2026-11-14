---
talk: Secure Boot on ARM systems – Building a complete Chain of Trust upon existing industry standards using open-source firmware
speaker: Matteo Carlini（Arm）
conference: Linaro Connect San Francisco 2017（SFO17-201）
year: 2017
video: https://youtu.be/MZ0PpzKPM5Q
slides: https://www.slideshare.net/slideshow/secure-boot-on-arm-systems-building-a-complete-chain-of-trust-upon-existing-industry-standards-using-opensource-firmware-sfo17201/80134470（Linaro 官方 SlideShare，26 頁；沒有 PDF，本筆記只用逐頁摘要）
---

# Secure Boot on ARM systems – Building a complete Chain of Trust [▶ 影片](https://youtu.be/MZ0PpzKPM5Q)

> **演講**：Matteo Carlini（Arm 韌體／boot／UEFI 軟體技術經理），Linaro Connect SFO17，場次 SFO17-201（2017 年 9 月）
> **來源**：YouTube 錄影（33:03）用 Whisper `turbo` 轉成逐字稿。投影片只有 Linaro SlideShare 頁面，下載不到 PDF，所以只用了逐頁摘要（`_work/slides/01-carlini-slideshare-outline.txt`）。
> **標記說明**：`【口頭】` 是投影片沒有的。`【投影片補充】` 是投影片有、講者沒講的。`【Q&A】` 是現場提問。`⚠️ 逐字稿缺字` 是 Whisper 聽錯。`⚠️ 待確認` 是查不清楚的地方。
> **年代提醒**：這是 2017 年的演講，內容照講者當時講的寫（例如「BL2 跑在 S-EL1」）。

---

## 目錄

- [0. 這場演講要做什麼](#0-這場演講要做什麼)
- [1. 兩套規範、兩段信任鏈](#1-兩套規範兩段信任鏈)
- [2. Arm TBB 的根據與 PKI](#2-arm-tbb-的根據與-pki)
- [3. TBB 一步一步怎麼驗：BL1 → BL2 → BL3x → BL33](#3-tbb-一步一步怎麼驗bl1--bl2--bl3x--bl33)
- [4. TF-A 實作了什麼](#4-tf-a-實作了什麼)
- [5. UEFI Secure Boot 的所有權模型](#5-uefi-secure-boot-的所有權模型)
- [6. 串起來：完整信任鏈與安全的 UEFI 變數](#6-串起來完整信任鏈與安全的-uefi-變數)
- [7. 其他做法：Android、U-Boot](#7-其他做法androidu-boot)
- [8. 下一步與開放問題](#8-下一步與開放問題)
- [9. Q&A](#9-qa)
- [10. 一頁速查表](#10-一頁速查表)
- [11. 延伸連結](#11-延伸連結)

---

## 0. 這場演講要做什麼

[▶ 01:08](https://youtu.be/MZ0PpzKPM5Q?t=68)

| 段落 | 內容 |
|---|---|
| 1 | Arm Trusted Board Boot（**TBB**）：PKI、信任鏈、TF-A 怎麼實作 |
| 2 | 跟 **UEFI Secure Boot** 比較，兩個怎麼合起來，用開源軟體做出完整信任鏈 |
| 3 | 簡單提 Android、U-Boot 的做法 |
| 4 | Arm 接下來的計畫 |

範圍：
- 【口頭】只談 Armv8-A，不談 M、R 系列（[▶ 03:15](https://youtu.be/MZ0PpzKPM5Q?t=195)）。
- 【口頭】**不談硬體**，不談怎麼做出防竄改的 root of trust。那是另一場（SFO17-304）（[▶ 03:49](https://youtu.be/MZ0PpzKPM5Q?t=229)）。

【口頭】為什麼要照標準、用開源？講者轉述前一天 keynote 的說法：照產業標準、用開源軟體做 secure boot，可以換到三件事（[▶ 02:14](https://youtu.be/MZ0PpzKPM5Q?t=134)）：
- 互通性
- 比較快上市
- 社群一起把安全性做好

> ⚠️ 逐字稿缺字：「Matteo Cardini」＝Carlini；「ARM Trusted Goal Boot」＝Trusted Board Boot。

---

## 1. 兩套規範、兩段信任鏈

[▶ 04:21](https://youtu.be/MZ0PpzKPM5Q?t=261)（投影片 6）

**TBB** 和 **UEFI Secure Boot** 是兩份不同的規範：
- 金鑰不同、憑證不同、PKI 也不同。
- 但目標一樣：驗證軟體 image 的真偽，建出信任鏈。

兩者驗的是**不同層**的 image：

| 規範 | 從哪驗到哪 |
|---|---|
| TBB | 從 BL1（上電後第一個韌體）驗到 BL33（normal world bootloader） |
| UEFI Secure Boot | 從 BL33（UEFI 韌體）開始，驗到 OS image |

**兩段接起來 = 從第一個韌體到 OS 的完整信任鏈。**

適用的市場（[▶ 02:44](https://youtu.be/MZ0PpzKPM5Q?t=164)）：
- 【口頭】企業伺服器、網通：UEFI 是第一選擇。
- 【口頭】嵌入式、行動裝置：TBB 可以搭配 verified boot 或 U-Boot 的做法。

---

## 2. Arm TBB 的根據與 PKI

### 2.1 規範

[▶ 05:25](https://youtu.be/MZ0PpzKPM5Q?t=325)（投影片 7）

TBB 根據兩份 Arm 文件：

| 縮寫 | 全名 | 管什麼 |
|---|---|---|
| **TBSA** | Trusted Base System Architecture | 硬體需求 |
| **TBBR** | Trusted Board Boot Requirements | 韌體需求 |

- 【口頭】兩份當時都還要簽 NDA 才能看，Arm 正在想辦法改。
- TF-A 實作的是 **TBBR client** 版。投影片 7：DEN0006C。

【口頭】伺服器方面的新消息（[▶ 06:34](https://youtu.be/MZ0PpzKPM5Q?t=394)）：
- 正在討論改 SBBR（Server Base Boot Requirements）1.1。
- 改的方向：**要求**從第一個韌體到 normal world bootloader，一定要有一條完整、一段接一段的信任鏈。
- **不指定**實作方式。TBB 和 TF-A 只是參考實作，第三方方案也可以。

> ⚠️ 逐字稿缺字：「TPSA and DBBR」＝TBSA 和 TBBR；「ndh」＝NDA；「sbdr」＝SBBR。

### 2.2 PKI：兩個天生可信的東西、每段兩張憑證

[▶ 07:04](https://youtu.be/MZ0PpzKPM5Q?t=424)（投影片 8）

**兩個「天生就信任」的元件**（implicitly trusted components）：

1. **硬體保護的 root of trust 公鑰**（ROTPK）。存在可信的暫存器裡。投影片 8 寫的是「ROTPK 的**雜湊**放在硬體」。
2. **BL1**：在 ROM 裡，受硬體保護，所以被當成可信。

**之後每個 BL3x image 都帶兩張憑證**：

| 憑證 | 裝什麼 | 用途 |
|---|---|---|
| **key certificate** | 這個 BL3x 專用的公鑰 | 拿來驗下面那張 content certificate |
| **content certificate** | 這個 BL3x image 的雜湊 | 跟實際 image 算出的雜湊比對 |

**兩組金鑰**（之後詳述）：
- trusted world key
- normal world key

**憑證格式**（[▶ 08:39](https://youtu.be/MZ0PpzKPM5Q?t=519)）：

- 所有公鑰、雜湊都放在**標準 X.509 憑證的 extension** 裡。
- 憑證都是**自簽**的，不需要 CA。
- 【口頭】為什麼不需要 CA：信任鏈靠的是「**檢查憑證裡的內容**」（上一段給的公鑰、雜湊對不對得上），不是靠「檢查發證者是不是有效的 CA」。

### 2.3 金鑰歸誰：為什麼有這麼多張憑證

[▶ 09:14](https://youtu.be/MZ0PpzKPM5Q?t=554)

照 TBBR：

- **ROTPK** 和 **trusted key certificate** 歸 **OEM**（產品廠商）。
- 其他 key certificate 存在的理由：**把簽章權限分出去**。例如交給 SoC 廠、trusted OS 廠、rich OS 廠，各自簽自己的 image。
- 【口頭】所以才會有那麼多種 key certificate。

---

## 3. TBB 一步一步怎麼驗：BL1 → BL2 → BL3x → BL33

[▶ 10:20](https://youtu.be/MZ0PpzKPM5Q?t=620)（投影片 9–14 是一系列圖，筆記只寫口頭流程）

### 3.1 BL1 驗 BL2（EL3）

[▶ 10:20](https://youtu.be/MZ0PpzKPM5Q?t=620)

1. 上電，執行 BL1。
2. 讀 **BL2 content certificate**，檢查裡面附的 ROTPK 對不對（跟硬體裡的比）。
3. 用這把 ROTPK 驗這張 content certificate 的簽章。
4. 從憑證拿出 BL2 的雜湊，跟 BL2 image 比對。

到這裡為止，只有這段程式跑在 EL3。

### 3.2 BL2 驗信任鏈的上層（S-EL1）

[▶ 11:23](https://youtu.be/MZ0PpzKPM5Q?t=683)

- 【口頭】**BL2 不跑在 EL3，跑在 S-EL1**。目的是盡量減少跑在 EL3 的程式碼（這是 2017 年的設計）。
- BL2 的工作：驗之後**所有**的 image。

步驟：

1. 讀最上層的 **trusted key certificate**，檢查裡面的 ROTPK。
2. 用 ROTPK 驗這張憑證。
3. 拿出兩把公鑰（都還是歸 OEM）：
   - **trusted world 公鑰**
   - **normal world 公鑰**

### 3.3 BL2 驗每個 BL3x（BL31、BL32）

[▶ 12:29](https://youtu.be/MZ0PpzKPM5Q?t=749)

對每個 BL3x：

1. 用 **trusted world 公鑰**驗這個 BL3x 的 **key certificate**。
2. 從 key certificate 拿出 **BL3x 公鑰**。
3. 用 BL3x 公鑰驗 **content certificate**。
4. 從 content certificate 拿出 BL3x 雜湊，跟實際 image 比對。

### 3.4 BL2 驗 BL33

[▶ 13:37](https://youtu.be/MZ0PpzKPM5Q?t=817)

- 還是 BL2 負責。
- BL33 用**另一組**憑證。【口頭】這樣簽章權可以交給 OS 廠。

步驟：

1. 用 **normal world 公鑰**驗 **BL33 key certificate**。
2. 拿出 BL33 公鑰。
3. 驗 BL33 content certificate。
4. 比對 BL33 雜湊。

全部驗完，才依序把執行權交給 BL31、BL32……最後是 BL33（[▶ 14:09](https://youtu.be/MZ0PpzKPM5Q?t=849)）。

**驗證失敗會怎樣**：講者沒有講。

---

## 4. TF-A 實作了什麼

[▶ 14:46](https://youtu.be/MZ0PpzKPM5Q?t=886)（投影片 15）

**實作了**：
- TBBR 規範的全部內容。
- 包括**非揮發計數器**（non-volatile counter）。【口頭】講者前面沒提到，它是用來**防 rollback**（防止刷回舊版）。

**沒實作**：
- 【口頭】**trusted debug certificate**：讓系統進 debug 模式用的。有人要的話可以排進 roadmap。

**平台**：
- AArch64、AArch32 上游都能跑 TBB。
- 有 Juno 和 FVP 的參考範例，包括 AArch32 版本。

【投影片補充】（投影片 15）
- build flag：`TRUSTED_BOARD_BOOT=1`、`GENERATE_COT=1`、`XXX_KEYS`。
- 工具：`cert_create`、`fiptool`。
- 【口頭】build flag 講者叫大家自己看 GitHub 上的 user guide，現場沒講。

**新消息**（[▶ 15:51](https://youtu.be/MZ0PpzKPM5Q?t=951)）：
- 上游已經整合 Arm **TrustZone CryptoCell**（CC-712）。
- 用它的**硬體 root of trust** 和**硬體加速**來驗 image。

---

## 5. UEFI Secure Boot 的所有權模型

[▶ 16:21](https://youtu.be/MZ0PpzKPM5Q?t=981)（投影片 16–19）

**三個角色**：

| 角色 | 是誰 |
|---|---|
| platform owner | 通常是 OEM 或最終使用者 |
| platform firmware | 任何符合 UEFI 的韌體 |
| software vendors | OS 或第三方軟體廠 |

**機制**：
- 一組已知的 key certificate。
- 一個**簽章資料庫**：允許清單 **db**、禁止清單 **dbx**。
- 跑在 BL33 的 UEFI 韌體用它們驗所有 UEFI 執行檔。
- 所有權模型也規定了怎麼從可信來源更新簽章資料庫。

### 5.1 兩種金鑰

[▶ 17:32](https://youtu.be/MZ0PpzKPM5Q?t=1052)

| 金鑰 | 誰持有 | 作用 |
|---|---|---|
| **PK**（Platform Key） | platform owner | **UEFI secure boot 真正的 root of trust** |
| **KEK**（Key Exchange Keys） | 各軟體廠 | 授權更新 db／dbx |

- **PK 為什麼是根**：用 PK 的私鑰，可以把所有公鑰（PK 自己、KEK）登錄（enroll）進韌體。
- 【口頭】照 UEFI 規範，這些金鑰**一定要存在硬體保護、防竄改的儲存**裡。

### 5.2 更新與驗證

[▶ 18:05](https://youtu.be/MZ0PpzKPM5Q?t=1085)

- platform owner 和軟體廠可以透過 UEFI runtime 的**變數 API**（`SetVariable()`）更新 db／dbx。
- 更新請求要能用已登錄的公鑰驗過。
- 開機時：
  - 簽章在**禁止清單**、或是**不認得的簽章**：image **不能執行**。
  - 簽章在**允許清單**：可以執行。

### 5.3 Arm 上的狀況

[▶ 19:13](https://youtu.be/MZ0PpzKPM5Q?t=1153)

- 【口頭】跟一年半前（約 2016 年 Las Vegas 的 Linaro Connect）講的一樣。
- 當時懸而未決的問題：**UEFI 變數要怎麼經由 secure world 更新？**
- 現在有答案了（第 6 節）。

【投影片補充】投影片 20 的 EDK2 回顧只有兩行，指向 Ard Biesheuvel 在 LCA14、LAS16 的兩場演講。

---

## 6. 串起來：完整信任鏈與安全的 UEFI 變數

[▶ 19:50](https://youtu.be/MZ0PpzKPM5Q?t=1190)（投影片 21–22）

### 6.1 完整信任鏈

投影片 21 把兩段合在一起：
- BL1 → BL2 → BL31／BL32 → BL33：由 TBB 驗。
- BL33（UEFI）→ OS：由 UEFI Secure Boot 驗。

### 6.2 從 normal world 安全地存取變數

[▶ 20:20](https://youtu.be/MZ0PpzKPM5Q?t=1220)

**在解什麼**：
- 金鑰和 db 要放在**只有 secure world 碰得到**的儲存。
- 但 OS 在 normal world 要能呼叫 `SetVariable()` 更新它們。

**流程**（講者假設金鑰已經放在某種硬體保護的儲存，硬體細節不談）：

1. normal world 的 OS 照常呼叫 runtime `SetVariable()`。
2. 進到 UEFI 韌體。
3. 韌體透過一個介面往下進 BL31。
   > ⚠️ 逐字稿缺字：講者說的是「RMM interface」。從上下文看比較可能是 MM（Management Mode）介面，但不確定。⚠️ 待確認
4. **新的部分**：BL31 裡的 **Secure Partition Manager**（SPM）把請求轉給一個跑在 **S-EL0** 的 **secure partition**。
5. 這個 secure partition 有 driver，去存取硬體上防竄改的變數儲存。

- 【口頭】SPM 是**共用框架**。它負責建立、管理、刪除 secure partition。
- 【口頭】RAS 錯誤處理是同一個框架的另一個用例。
- 【口頭】這些當時都在 Arm 內部開發中，很快要 upstream。之後會在 System Guidance 平台出完整範例，包括 EDK2、EDK2-platforms、TF-A 的 patch（[▶ 21:54](https://youtu.be/MZ0PpzKPM5Q?t=1314)）。

---

## 7. 其他做法：Android、U-Boot

[▶ 22:28](https://youtu.be/MZ0PpzKPM5Q?t=1348)（投影片 23）

- 【口頭】在行動裝置上，UEFI 某種程度上沒什麼意義。
- Android 和 U-Boot 各有自己的 verified boot。它們都有信任鏈、硬體 root of trust 的概念。

【投影片補充】投影片 23 的重點：
- Android Verified Boot：信任鏈從 OEM key 開始；有裝置鎖定狀態；Android 8.0 加了 rollback 保護。
- U-Boot Verified Boot：信任鏈從 U-Boot（BL33）裡的公鑰開始。

【口頭】講者丟出一個「挑釁」的想法（[▶ 23:34](https://youtu.be/MZ0PpzKPM5Q?t=1414)）：

- SUSE 的人已經把 **UEFI 介面做在 U-Boot 上**。
- 能不能更進一步：
  1. 在 U-Boot 上實作 `SetVariable`／`GetVariable`。
  2. 在支援 UEFI 的 U-Boot 上掛 **shim** 來管金鑰。
- 這會在嵌入式裝置上帶來很多要解決的問題。
- 但最終目標是：嵌入式和企業級的 secure boot 流程、API **收斂成一套**。

> ⚠️ 逐字稿缺字：「suzer guys」＝SUSE。

---

## 8. 下一步與開放問題

[▶ 24:04](https://youtu.be/MZ0PpzKPM5Q?t=1444)（投影片 24）

**Arm 的計畫**：

1. 做出並開源參考平台軟體（TF-A＋EDK2）。完整開機路徑跑在 System Guidance 平台上。
2. 研究以 U-Boot 為基礎的方案。
3. **韌體更新**：TF-A 有自己的韌體更新機制（FWU），UEFI 有簽章的 capsule update。要想辦法把兩個合起來，做出安全的韌體更新。
4. **規範**：
   - 重整 TBBR、在 SBBR 加入相關要求。
   - 可能出伺服器版 TBSA/TBBR，涵蓋 Arm 規範目前沒有的 TPM、PCR、measured boot。

**開放問題**（[▶ 25:40](https://youtu.be/MZ0PpzKPM5Q?t=1540)）：

- Arm 在**進 UEFI 之前**的環境，要標準化到什麼程度？
- 一方面想保留廠商差異化的空間。
- 另一方面，【口頭】**很多安全報告顯示：有些商用產品的實作，讓人能在 EL3 執行任意程式碼**，等於整個 TEE 都被攻破。
- Arm 至少想給一些指引：哪些 API 該實作、該放在哪個 exception level。

---

## 9. Q&A

【Q&A】**Q：image 驗證只支援一種雜湊，有沒有打算支援 SHA-512 或 HMAC？**（[▶ 26:46](https://youtu.be/MZ0PpzKPM5Q?t=1606)）

- 講者自己不知道，把麥克風交給 TF-A 的技術負責人 Dan。
- Dan 的回答（[▶ 27:23](https://youtu.be/MZ0PpzKPM5Q?t=1643)）：
  - 參考實作只是照 TBBR 規範做。
  - 規範加入更強的加密，他們就跟進。
  - 沒有理由不能加，或由別人貢獻。
  - 只是規範沒要求，所以沒有動機做。

> ⚠️ 逐字稿缺字：「Shopify 12」推測是 SHA-512。

【Q&A】**Q：為什麼用一堆 X.509 extension，不直接用 X.509 原本的欄位？**（[▶ 27:55](https://youtu.be/MZ0PpzKPM5Q?t=1675)）

- 答：這是規範寫的。規範裡混了很多設計資訊，所以有空間用不同方式做，而且這樣可以運作。
- 講者補充：他們正想重整這份太舊的規範，有需求可以提出來。

【Q&A】**Q：最新的規範好像是 2013 年？**（[▶ 29:08](https://youtu.be/MZ0PpzKPM5Q?t=1748)）

- 答：client 版是 2015 年。
- 伺服器版只是實驗，從來沒有正式定稿，要從頭重寫。

【Q&A】**Q：secure variable 那張圖裡沒有 OP-TEE 或 secure OS，是打算不靠它們做嗎？**（[▶ 29:38](https://youtu.be/MZ0PpzKPM5Q?t=1778)）

- 答：目前的模型**不能讓 trusted OS 和 secure partition 同時跑**。
- 他們在擴充，讓多個 secure partition 可以跑，也能和 OP-TEE 並存。到時要決定誰負責存取 secure variable。
- 目標約 2018 年初。

【Q&A】**Q：為什麼不用更簡單的做法：開機就載入 OP-TEE，讓 secure variable 變成它的一個服務？**（[▶ 31:15](https://youtu.be/MZ0PpzKPM5Q?t=1875)）

- 答：SPM 這套基礎原本就是為 RAS 做的。可以有兩個 secure partition：一個做 RAS 的 firmware-first 錯誤處理，一個做 secure variable。
- Arm 內部也有別的團隊在用 OP-TEE 做同樣的事，兩邊還要整合。
- 【口頭】可能要看市場：伺服器和行動裝置的答案不一定一樣。

> ⚠️ 逐字稿缺字：「Opti」「OPT」＝OP-TEE。

---

## 10. 一頁速查表

**TBB 信任鏈（照講者 2017 年的描述）**

```
硬體: ROTPK（hash） + BL1（ROM）          ← 天生可信
BL1 (EL3):  ROTPK → BL2 content cert → BL2 hash ✓
BL2 (S-EL1): ROTPK → trusted key cert → { TW 公鑰, NW 公鑰 }
   對 BL31/BL32: TW 公鑰 → BL3x key cert → BL3x 公鑰 → BL3x content cert → hash ✓
   對 BL33:      NW 公鑰 → BL33 key cert → BL33 公鑰 → BL33 content cert → hash ✓
BL33 (UEFI): PK → KEK → db/dbx → OS image ✓/✗
```

| 問題 | 答案 |
|---|---|
| 為什麼每段兩張憑證？ | key cert 帶這段的公鑰，content cert 帶這段的雜湊。分開後，簽章權可以交給不同廠商 |
| 為什麼憑證自簽、不用 CA？ | 信任來自上一段給的公鑰和雜湊，不是來自發證者 |
| 防 rollback 靠什麼？ | 非揮發計數器（TF-A 有實作） |
| UEFI 的根是誰？ | PK（platform owner 持有） |
| OS 怎麼安全地改 UEFI 變數？ | `SetVariable()` → BL31 的 SPM → S-EL0 secure partition → 硬體保護的儲存 |

---

## 11. 延伸連結

- MT8189 上實際開 TF-A TBB：[`../verified-boot-notes/fit-sign.md`](../verified-boot-notes/fit-sign.md)、[`../verified-boot-notes/vb-intro.md`](../verified-boot-notes/vb-intro.md)
- TF-A secure boot 與 crypto：[`../tf-a-and-op-tee-note/secure-boot-intro.md`](../tf-a-and-op-tee-note/secure-boot-intro.md)、[`../tf-a-and-op-tee-note/crypto-in-secure-boot.md`](../tf-a-and-op-tee-note/crypto-in-secure-boot.md)

---

## 附：一句話總結

> **TBB 用「ROTPK → 每段一張 key cert＋一張 content cert」把 BL1 一路驗到 BL33，UEFI Secure Boot 再用 PK／KEK／db 從 BL33 驗到 OS。兩段接起來就是完整信任鏈；剩下的難題是怎麼讓 normal world 安全地更新放在 secure world 的金鑰和變數。**

---

## ⚠️ 待確認清單

1. [▶ 20:51](https://youtu.be/MZ0PpzKPM5Q?t=1251) 「RMM interface」：推測是 MM（Management Mode）介面，聽不清楚。
2. 投影片只有 SlideShare 逐頁摘要，沒有原文。投影片 9–14 的圖、15 的 build flag 細節都沒有逐字核對。

---

*筆記依據 Matteo Carlini〈Secure Boot on ARM systems〉（Linaro Connect SFO17-201）錄影（Whisper `turbo` 轉錄，33:03）與 Linaro SlideShare 投影片逐頁摘要整理。*
