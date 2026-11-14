---
talk: "The Bugs in Your Bootloaders: Embedded Device Secure Boot Fails and How to Fix Them"
speaker: Henrik Ferdinand Nölscher（Google，Security Engineer）
conference: Black Hat Europe 2024
year: 2024
video: https://youtu.be/eZczwNFzxus
slides: 待補（影片說明欄指向 https://www.blackhat.com/eu-24/briefings/schedule/#the-bugs-in-your-bootloaders-embedded-device-secure-boot-fails-and-how-to-fix-them-42309 ，該站擋自動抓取）
---

# The Bugs in Your Bootloaders: Embedded Device Secure Boot Fails and How to Fix Them [▶ 影片](https://youtu.be/eZczwNFzxus)

> **演講**：Henrik Ferdinand Nölscher（自稱 Ferdi；Google Cloud 一個做硬體／韌體底層攻擊的團隊），Black Hat Europe 2024。Black Hat 頻道 2025-05-19 上傳。講者和會議都來自影片說明欄。
> **來源**：YouTube 錄影（38:12）用 Whisper `turbo` 轉成逐字稿，再加上影片說明欄（官方摘要）。**沒有投影片**：講者指著程式碼、PCB 照片、攻擊面圖、bootloader 比較表說的地方都看不到。
> **標記說明**：`【口頭】` 這場沒有投影片，正文幾乎全是口頭，只標意見和實務經驗。`【說明欄補充】` 是影片說明欄有的。`【Q&A】` 是現場提問。`⚠️ 逐字稿缺字` 是 Whisper 聽錯。`⚠️ 待確認` 是查不清楚的地方。
> **攻防內容的寫法**：只寫漏洞成因、攻擊的「階段」、修補與防禦教訓，不寫可以照做的利用細節。

---

## 目錄

- [0. 這場演講要做什麼](#0-這場演講要做什麼)
- [1. 威脅情境：實體接觸是常態](#1-威脅情境實體接觸是常態)
- [2. 案例一：Cisco Nexus 9000 的 GRUB legacy](#2-案例一cisco-nexus-9000-的-grub-legacy)
- [3. 案例二：Dell iDRAC9 的 RootBlock](#3-案例二dell-idrac9-的-rootblock)
- [4. 怎麼修：分層的做法](#4-怎麼修分層的做法)
- [5. Q&A](#5-qa)
- [6. 一頁速查表](#6-一頁速查表)
- [7. 延伸連結](#7-延伸連結)

---

## 0. 這場演講要做什麼

[▶ 00:00](https://youtu.be/eZczwNFzxus?t=0)

- 講者的工作：拿各種裝置來**滲透測試**：拆開、研究 PCB、看每顆晶片、逆向韌體，找能實際利用的底層韌體和硬體漏洞，再負責任地回報（[▶ 00:30](https://youtu.be/eZczwNFzxus?t=30)）。
- 從底層一路往上做，**最後一定會碰到 bootloader**。bootloader 在各種裝置上都扮演安全關鍵的角色（[▶ 03:39](https://youtu.be/eZczwNFzxus?t=219)）。
- 內容：兩個他找到的嚴重漏洞，然後講**怎麼全部修好**。

**一些數字**（[▶ 04:14](https://youtu.be/eZczwNFzxus?t=254)）：
- 他們審過**超過 15 種裝置**，都用開源 bootloader。
- **每一種都曾被 bootloader 漏洞影響過。**
- 這裡的「bootloader 漏洞」是指：攻擊者能在 bootloader 這個**權限非常高**的環境執行程式碼，從而攻破之後所有開機階段或 OS（[▶ 04:44](https://youtu.be/eZczwNFzxus?t=284)）。
- 裝置類型：資料中心設備（伺服器）、資安設備，**甚至 HSM**。【口頭】他相信這些 bootloader 也涵蓋更多裝置，例如 IoT 和車（[▶ 05:14](https://youtu.be/eZczwNFzxus?t=314)）。

【說明欄補充】這類漏洞讓攻擊者取得**最高程度的入侵**：無法偵測的任意程式碼執行，而且能撐過各種復原或重置。廠商常常要採取激烈手段才修得了，最壞情況要等新硬體出貨才修掉。

---

## 1. 威脅情境：實體接觸是常態

[▶ 01:01](https://youtu.be/eZczwNFzxus?t=61)

1. **供應鏈**：裝置要製造、組裝、運送，部署前經過很多人的手。攻擊者有**時間有限、但是實體**的接觸機會。【口頭】「時間有限」可能就有好幾天，足夠做很多硬體和韌體攻擊（[▶ 01:31](https://youtu.be/eZczwNFzxus?t=91)）。
2. **部署後**：就算供應鏈完美，也有合法的存取：遠端用帳密登入，或實體維修（[▶ 02:04](https://youtu.be/eZczwNFzxus?t=124)）。
3. **bare metal 雲端**：租戶本身就有高權限，「沒有東西擋在一個已經有權限、想動硬體和韌體的攻擊者前面」。

**所以重點是**（[▶ 02:35](https://youtu.be/eZczwNFzxus?t=155)）：
- 要能**把裝置帶回可信狀態**。租戶離開後也要能。
- 最要避免的是**持久性**：藏在韌體、flash、周邊裝置裡。

---

## 2. 案例一：Cisco Nexus 9000 的 GRUB legacy

### 2.1 裝置

[▶ 05:50](https://youtu.be/eZczwNFzxus?t=350)

- Cisco Nexus N9000 系列交換器。裡面有很多處理網路流量的 ASIC，但都由一塊「管理板」啟動：有 SSD，散熱片下是 Intel 處理器（[▶ 06:20](https://youtu.be/eZczwNFzxus?t=380)）。
- 【口頭】Cisco 有投資：**有 secure boot 鏈、有 root-of-trust 晶片**。他認為算是業界一流。
- 板子背面有一顆 SPI flash，dump 下來用 UEFITool 打開：幾個 firmware volume，EDK2 為基礎的韌體（[▶ 06:50](https://youtu.be/eZczwNFzxus?t=410)）。
- 其中一個叫 **Cisco GRUB**。他猜它就是 bootloader，負責驗 OS image 的簽章（[▶ 07:20](https://youtu.be/eZczwNFzxus?t=440)）。

### 2.2 發現：fork 自 1990 年代的 GRUB legacy

[▶ 07:51](https://youtu.be/eZczwNFzxus?t=471)

- 用 Ghidra 看，以為是 GRUB 2，結果 Google 字串後發現**是 fork 自 GRUB legacy**（【說明欄補充】0.97 版）。
- 【口頭】GRUB legacy 根本不支援 secure boot，那 Cisco 怎麼做的？

**Cisco GRUB 的流程**（[▶ 08:21](https://youtu.be/eZczwNFzxus?t=501)）：
1. 找所有開機裝置：主要是內部 flash，**也可能是插在前面的 USB 隨身碟**。
2. 找 OS image。
3. 載入 OS image，**驗簽章**，對了才執行。

**問題在第 1、2 步**（[▶ 08:55](https://youtu.be/eZczwNFzxus?t=535)）：
- 要讀檔案系統。現代韌體通常用 EDK2 的 LoadImage，由 EFI 韌體提供檔案系統。
- GRUB legacy 沒有這些，所以**自己實作了一堆檔案系統 driver**（當時約 12～13 種，【口頭】「連 ReiserFS 都有」）。
- 有一個大迴圈**逐一嘗試所有檔案系統後端**，第一個掛得起來的就拿來找 OS image（[▶ 09:27](https://youtu.be/eZczwNFzxus?t=567)）。

### 2.3 漏洞：XFS driver 的 stack buffer overflow

[▶ 09:27](https://youtu.be/eZczwNFzxus?t=567)

**成因**：
- XFS driver 列檔案的函式裡，有一個 stack 上的緩衝區，**大小來自 superblock 裡的欄位**。
- **superblock 存在外部**：USB 隨身碟或內部 SSD 上，攻擊者能改（[▶ 09:59](https://youtu.be/eZczwNFzxus?t=599)）。
- 改了 superblock 裡的大小欄位，後面的長度檢查就形同虛設，接著用攻擊者控制的長度做 `memcpy` → **教科書等級的 buffer overflow**（[▶ 10:34](https://youtu.be/eZczwNFzxus?t=634)）。
- **沒有任何緩解措施。**
- 關鍵：這發生在**驗簽章之前**（找 OS image 時就在解析檔案系統）。

**兩種觸發方式**（[▶ 10:34](https://youtu.be/eZczwNFzxus?t=634)）：
1. **實體**：準備好的 USB 隨身碟插到前面，下次重開機就觸發。
2. **遠端**：有管理員帳密（或另一個漏洞）。【口頭】要 shell 是這台設備的正式功能；用 shell 把惡意的 XFS 分區寫到磁碟，重開機（[▶ 11:06](https://youtu.be/eZczwNFzxus?t=666)）。

**效果**（[▶ 11:37](https://youtu.be/eZczwNFzxus?t=697)）：
- 在 Cisco GRUB 環境執行程式碼，**繞過簽章檢查**。
- 【口頭】**很難偵測**（[▶ 12:07](https://youtu.be/eZczwNFzxus?t=727)）：
  - 雖然有 root-of-trust 晶片，就算它收集了韌體的量測值，**也沒有軟體介面能讀出來**。
  - 所有復原功能不是在 GRUB 裡，就是在被攻破的 GRUB 之後才啟動的 Linux 裡（[▶ 12:38](https://youtu.be/eZczwNFzxus?t=758)）。聰明的攻擊者可以連復原功能一起 hook，取得隱密的立足點。
- 【口頭】插 USB 讓它開機，大約三分鐘（[▶ 13:10](https://youtu.be/eZczwNFzxus?t=790)）。

**修補與擴散**（[▶ 13:10](https://youtu.be/eZczwNFzxus?t=790)）：
- Cisco 修了，有 CVE。
- 他 Google 那段有漏洞的程式碼，**出現在很多其他地方**：GRUB legacy 的檔案系統實作小巧、不依賴其他函式庫，很容易被拿去用（[▶ 13:43](https://youtu.be/eZczwNFzxus?t=823)）。
  - Xen hypervisor 的一些工具。
  - coreboot 的 **FILO** payload。
  - 都發了安全公告、拿了 CVE，現在都修了。

---

## 3. 案例二：Dell iDRAC9 的 RootBlock

### 3.1 裝置

[▶ 14:17](https://youtu.be/eZczwNFzxus?t=857)

- Dell 企業產品的遠端管理功能 **iDRAC**：PowerEdge 伺服器開機時第一個啟動的東西，有自己的 SoC、儲存、RAM，是一顆 **BMC**（Baseboard Management Controller）（[▶ 14:51](https://youtu.be/eZczwNFzxus?t=891)）。
- 審的是 **iDRAC9**，用在各種產品（伺服器、儲存設備……），大量重用同一顆 SoC。【口頭】「對攻擊者來說很棒，也凸顯它只執行 Dell 簽章程式碼有多重要。」（[▶ 15:21](https://youtu.be/eZczwNFzxus?t=921)）
- 有 secure boot：每一段驗下一段，最後跑 Linux，檔案系統也有完整性保護。
- SoC 是 **Nuvoton** 的 BMC 專用晶片。第一階段 bootloader 是 Nuvoton 寫的，叫 **BootBlock**。漏洞就在 BootBlock（[▶ 15:53](https://youtu.be/eZczwNFzxus?t=953)）。

### 3.2 漏洞：先複製到 header 指定的位址，才驗簽章

[▶ 16:23](https://youtu.be/eZczwNFzxus?t=983)

**BootBlock 的工作**：把系統帶到能跑下一個更強 bootloader 的狀態。主要邏輯在一個函式（Whisper 聽成「check image copy and jump」）：
1. 在外部 SPI flash 找下一階段 bootloader 的 image。
2. 載入記憶體。
3. 驗簽章。
4. 執行。

**成因**（[▶ 16:54](https://youtu.be/eZczwNFzxus?t=1014)）：
- 下一階段 bootloader 可以放在不同位置：**image header 裡的欄位決定 BootBlock 要把它複製到哪個位址**。
- **header 在外部 SPI flash，攻擊者控制。**
- **整個 image 的簽章要等複製到目的位址之後才驗**（[▶ 17:26](https://youtu.be/eZczwNFzxus?t=1046)）。
- → 攻擊者可以讓 BootBlock 把資料**複製到 BootBlock 自己所在的 SRAM**，用自己的內容蓋掉 BootBlock 還沒執行完的程式碼。複製完一返回，就跳進攻擊者的程式碼（[▶ 17:59](https://youtu.be/eZczwNFzxus?t=1079)）。（細節不收錄。）
- 這就是一種 **TOCTOU**：「用」（複製到指定位址）發生在「驗」之前。

**實驗**（[▶ 18:29](https://youtu.be/eZczwNFzxus?t=1109)）：
- 打開伺服器，找到 iDRAC 的 SPI flash。他把 flash 拆下來放在轉接板上。
- 【口頭】「找漏洞很好玩，但最後我恨死這塊轉接板，因為要寫 flash 無數次。」
- 量產伺服器**沒有 UART console，完全是瞎子**。他用邏輯分析儀除錯，自己發明了把資料送出來的方法（[▶ 19:00](https://youtu.be/eZczwNFzxus?t=1140)）。
- 結果：跑他自己編的 U-Boot，印出一個好笑的字串（[▶ 19:33](https://youtu.be/eZczwNFzxus?t=1173)）。

**效果**（[▶ 20:04](https://youtu.be/eZczwNFzxus?t=1204)）：
- 跟 Cisco 一樣：flash 準備好之後，**不需要任何使用者互動**，開機就跑。
- 【口頭】攻擊者可能會載入 Dell 在 eMMC 上的原版 kernel、稍微修改 → **持久、很難偵測的立足點**。
- BMC 權限很高，可以從那裡再攻擊主機（[▶ 20:34](https://youtu.be/eZczwNFzxus?t=1234)）。
- 寫 flash：有時要拆焊；但在他測過的其他系統上，**一個 20 美元的 chip clip 夾上去就能寫**。因為系統大量重用，準備一個 image 就能通用（[▶ 21:05](https://youtu.be/eZczwNFzxus?t=1265)）。
- Dell 合作修了，雙方都發了公告。

---

## 4. 怎麼修：分層的做法

[▶ 21:40](https://youtu.be/eZczwNFzxus?t=1300)

【口頭】這些問題有共通點，不只這兩個案例，也包括近年其他漏洞。他主張**分層處理**。

### 4.1 第一層：改威脅模型

[▶ 22:14](https://youtu.be/eZczwNFzxus?t=1334)

- 【口頭】他不認為廠商或 bootloader 維護者是故意的，而是做的時候有某些假設。（GRUB legacy 例外：早就沒人維護了，「90 年代有別的問題要煩，像 Y2K」。）
- **「實體安全是謊言」**（[▶ 22:44](https://youtu.be/eZczwNFzxus?t=1364)）：它可以是縱深防禦的一層，但**不能假設裝置不會受到實體攻擊**。設計階段做威脅建模時就要考慮。
- **使用者或工作負載不能被天生信任**：bare metal 雲端；或有更強的漏洞（例如可蠕蟲傳播的）打開裝置外殼，想在上面取得難以清除的持久性（[▶ 23:21](https://youtu.be/eZczwNFzxus?t=1401)）。

**攻擊面**（講者有一張圖，看不到；[▶ 23:21](https://youtu.be/eZczwNFzxus?t=1401)）：
- 分**遠端**和**本地**兩類。大部分是 bootloader 專屬，但也適用其他韌體（loader、韌體裡的函式庫）。
- 這些專案的工作就是「載入 OS」，所以會碰到很多外部資料。

**其他人找到的同類漏洞**（[▶ 24:24](https://youtu.be/eZczwNFzxus?t=1464)）：

| 位置 | 例子 |
|---|---|
| 遠端 | **shim**（很多 Linux 發行版用來載入沒被標準 UEFI CA 簽的東西）**竟然支援 HTTP**，有人找到 HTTP 解析的越界寫入（[▶ 24:57](https://youtu.be/eZczwNFzxus?t=1497)） |
| 本地 | **EDK2** 裡量測分割表進 PCR 的函式（本身就是安全相關功能）有 heap buffer overflow，還有一個 DoS |
| 本地 | 他自己這兩個：檔案系統解析、image 格式解析 |

- 【口頭】**位置**可能是公開研究比較少涵蓋的攻擊面，但**漏洞本質很古典**：解析器 bug 導致記憶體破壞（[▶ 25:32](https://youtu.be/eZczwNFzxus?t=1532)）。

### 4.2 第二層：用硬體安全功能

[▶ 26:04](https://youtu.be/eZczwNFzxus?t=1564)

**防降版**（[▶ 26:04](https://youtu.be/eZczwNFzxus?t=1564)）：
- secure boot 很好，但任何韌體遲早會有 bug，要能**管理機隊裡跑的版本**。
- 防降版：1.1 版有嚴重漏洞，就能擋住有實體接觸的攻擊者把舊的有漏洞版本燒回去（[▶ 26:37](https://youtu.be/eZczwNFzxus?t=1597)）。
- 【口頭】他展示的漏洞都修了，但**沒有防降版的話，要完全排除它在機隊裡被利用的可能，其實很難**。這些裝置一用就好幾年。
- 有時也有合理理由要降版，所以最好**讓使用者可以設定**。【口頭】他們審過的裝置**沒有一台做得到**（[▶ 27:07](https://youtu.be/eZczwNFzxus?t=1627)）。

**遠端證明（remote attestation）**（[▶ 27:41](https://youtu.be/eZczwNFzxus?t=1661)）：
- secure boot 是「一段驗下一段，不對就不執行」，這個性質很強。
- 但最後裝置開起來時，你只能**從「它開起來了」推論它是可信的**。【口頭】「我覺得這有點弱。」
- **measured boot**：每一段把下一段的設定或 binary 的證據（通常是雜湊）放進防竄改的地方（root-of-trust 晶片、安全晶片、SoC 裡某區域），加上密碼學身分，就能產生**證明**。再加上新鮮度挑戰，交給你的基礎設施，就能知道機隊裡跑的是什麼版本、有沒有被降版（[▶ 28:12](https://youtu.be/eZczwNFzxus?t=1692)）。
- 實務障礙：最後你只拿到一堆雜湊，不容易預測證據該長什麼樣（[▶ 28:45](https://youtu.be/eZczwNFzxus?t=1725)）。
- 【口頭】**他們審過的幾乎所有裝置，硬體理論上支援，但實際上不能用**。希望廠商讓它可用，而且不只給已經有憑證基礎設施的大企業用（[▶ 29:15](https://youtu.be/eZczwNFzxus?t=1755)）。
- 對照 Cisco 案例：root-of-trust 晶片有量測也讀不出來。

### 4.3 第三層：直接把 bug 找出來

[▶ 29:46](https://youtu.be/eZczwNFzxus?t=1786)

**緩解措施太少**：
- 【口頭】韌體的 exploit 緩解措施少得驚人。嵌入式要移植 canary、CFI 等經典緩解還有很多工作；就算是運算平台的韌體也很少看到（[▶ 30:16](https://youtu.be/eZczwNFzxus?t=1816)）。「沒什麼要發明的，只是要實際用上、主動要求。」
- **RootBlock 的例子**：如果用硬體的 MMU **把前一階段設成唯讀**，下一階段的資料就蓋不掉它，這個漏洞就能完全避免（[▶ 30:52](https://youtu.be/eZczwNFzxus?t=1852)）。

**bootloader 現況**（講者有一張比較表，看不到；[▶ 30:52](https://youtu.be/eZczwNFzxus?t=1852)）：
- 他列了很多有影響力的開源 bootloader，大多是安全關鍵的（GRUB legacy 除外，只有那一個案例）。
- **幾乎都沒用記憶體安全語言、也沒有緩解措施；只有很少數有在做 fuzzing**，有做的也可能沒涵蓋全部攻擊面（[▶ 31:24](https://youtu.be/eZczwNFzxus?t=1884)）。
- 【口頭】「這是危險地帶」：很多裝置靠 secure boot 保護韌體，而 secure boot 最後都依賴這些專案之一（[▶ 31:54](https://youtu.be/eZczwNFzxus?t=1914)）。

**怎麼找 bug**（[▶ 32:24](https://youtu.be/eZczwNFzxus?t=1944)）：
- 這些專案不大（不像瀏覽器或 JavaScript 引擎），可以多看幾眼。
- 他試了 code scanner 和 LLM：
  - **他的兩個漏洞，code scanner 和 LLM 都 100% 抓得到**，但沒找到更多。
  - 【口頭】它們不擅長判斷哪些程式碼實際會跑、哪些在處理攻擊者控制的資料（[▶ 32:54](https://youtu.be/eZczwNFzxus?t=1974)）。
- **他認為 fuzzing 最有效**：當了就是當了，不是 harness 有問題就是程式有問題。
- **OSS-Fuzz**（[▶ 33:24](https://youtu.be/eZczwNFzxus?t=2004)）：
  - 他跟維護者談過，**熱門 bootloader 被列為 critical**，整合進去可以拿 **15,000 美元**獎勵。
  - 他已經開始把 **U-Boot** 放進 OSS-Fuzz。
  - 整合後，每個 commit（至少關鍵分支）都會被 fuzz，當了會通知開發者（[▶ 33:54](https://youtu.be/eZczwNFzxus?t=2034)）。
  - 【口頭】fork bootloader 做 BSP 的晶片廠也該整合。有需要歡迎找他。

---

## 5. Q&A

【Q&A】**Q：記憶體安全語言是可行的方案之一，為什麼大多沒被採用？效能嗎？**（[▶ 35:26](https://youtu.be/eZczwNFzxus?t=2126)）
- 他認為是**歷史包袱**：專案演進了很多很多年，GRUB 2、U-Boot 都非常熱門（[▶ 35:57](https://youtu.be/eZczwNFzxus?t=2157)）。
- 他不確定全部換掉是好主意：還有很多已知有效的方法可以強化現有專案，例如緩解措施。
- 好例子：**Caliptra** 韌體，跨廠商的開源專案，用記憶體安全語言，也在那個語言裡實作緩解措施（[▶ 36:32](https://youtu.be/eZczwNFzxus?t=2192)）。
- 【口頭】但這些專案有歷史，很多人每天在用；嵌入式工程師就是會用 U-Boot bring up 板子，大家做了好多年。

> ⚠️ 逐字稿缺字：「calypter」推測是 Caliptra。

【Q&A】**Q：你說看了 15 種裝置，只展示兩種，其他是什麼？**（[▶ 36:32](https://youtu.be/eZczwNFzxus?t=2192)）
- 各種資料中心相關設備：網路設備、運算平台等（[▶ 37:05](https://youtu.be/eZczwNFzxus?t=2225)）。
- 【口頭】重點是 bootloader 這個整體主題，不是特定裝置；每次審查都看到同樣的模式。以後會公布更多。

---

## 6. 一頁速查表

| 案例 | 成因 | 為什麼繞得過 secure boot | 修法／教訓 |
|---|---|---|---|
| Cisco Nexus 9000（GRUB legacy fork） | XFS driver 用 superblock 裡的大小做 stack 緩衝區，再 `memcpy` → overflow | 解析檔案系統發生在**驗簽章之前**；USB 或遠端 shell 都能放惡意檔案系統 | 只開需要的檔案系統；不信任儲存裝置上的 metadata；同一段程式碼也在 Xen 工具、coreboot FILO 裡 |
| Dell iDRAC9（Nuvoton BootBlock，「RootBlock」） | 依外部 header 指定的位址複製 image，**複製完才驗簽章** | 可以蓋掉 BootBlock 自己 → 驗證前就被劫持（TOCTOU） | 先驗再用；用 MMU 把前一階段設唯讀；只接受固定、安全的載入位址 |

**分層修法**
1. **威脅模型**：實體接觸是常態（供應鏈、維修、bare metal 雲端）；工作負載不可信。
2. **硬體功能**：可設定的防降版；**真的能用的** measured boot＋remote attestation。
3. **找 bug**：緩解措施（canary、CFI、MMU 唯讀）、OSS-Fuzz（critical bootloader 有 15,000 美元獎勵）、code scanner／LLM 能抓到這類古典 bug。

**通用規律**：bootloader 在驗簽章之前就會解析很多外部資料（檔案系統、image header、網路協定），**那段程式碼就是攻擊面**。

---

## 7. 延伸連結

- MT8189 上 BL2 讀 FIP、U-Boot 讀 fitImage 前要解析什麼（對照「驗證前的解析」）：[`../verified-boot-notes/fit-sign.md`](../verified-boot-notes/fit-sign.md)、[`../tf-a-and-op-tee-note/secure-boot-intro.md`](../tf-a-and-op-tee-note/secure-boot-intro.md)
- MT8189 的防降版現況：TF-A TBB NV counter 固定 0（`../verified-boot-notes/vb-brief.md`），正好是本場「沒有防降版」的情況（延伸建議，不是講者說的）

---

## 附：一句話總結

> **兩個有 secure boot 的資料中心設備，都在「驗簽章之前」就倒下：Cisco 的 GRUB legacy fork 解析攻擊者的 XFS 時 overflow，Dell iDRAC 的 BootBlock 先照外部 header 複製、後驗章，結果被蓋掉自己。修法是把實體攻擊納入威脅模型、提供真正能用的防降版和遠端證明，並用緩解措施和 fuzzing 把 bootloader 的古典解析 bug 清掉。**

---

## ⚠️ 待確認清單

1. 沒有投影片：程式碼片段、攻擊面圖、bootloader 比較表（記憶體安全語言／緩解措施／fuzzing）、公告連結都沒有看到。

---

*筆記依據 Henrik Ferdinand Nölscher〈The Bugs in Your Bootloaders〉（Black Hat Europe 2024）錄影（Whisper `turbo` 轉錄，38:12）與影片說明欄整理。沒有投影片。*
