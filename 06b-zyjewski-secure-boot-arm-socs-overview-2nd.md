---
talk: Overview of Secure Boot state in the ARM-based SoCs — 2nd edition
speaker: Tomasz Żyjewski（3mdeb）
conference: FOSDEM 2023，Open Source Firmware, BMC and Bootloader devroom
year: 2023
video: https://youtu.be/jdDZst29VLo
slides: https://archive.fosdem.org/2023/schedule/event/arm_secure_boot_2/attachments/slides/5852/export/events/attachments/arm_secure_boot_2/slides/5852/Overview_of_Secure_Boot_in_Arm_based_SoCs_2nd_Edition.pdf
---

# Overview of Secure Boot state in the ARM-based SoCs — 2nd edition [▶ 影片](https://youtu.be/jdDZst29VLo)

> **演講**：Tomasz Żyjewski（3mdeb 嵌入式系統團隊主管），FOSDEM 2023 Open Source Firmware, BMC and Bootloader devroom
> **來源**：YouTube（3mdeb 頻道）錄影（31:29）用 Whisper `turbo` 轉成逐字稿，再加上 FOSDEM 官方附件投影片（25 頁）。開頭約 1 分半是麥克風問題。
> **標記說明**：`【口頭】` 是投影片沒有的。`【投影片補充】` 是投影片有、講者沒講的。`【Q&A】` 是現場提問。`⚠️ 逐字稿缺字` 是 Whisper 聽錯。`⚠️ 待確認` 是查不清楚的地方。
> **跟第一版的關係**：第一版是 [06a](06a-pijanowski-secure-boot-arm-socs-overview.md)（FOSDEM 2021）。這一版前面的定義、流程幾乎一樣，筆記只簡單帶過；重點是兩年來的變化，以及新加的 **MediaTek**、**Rockchip** 兩個實例。

---

## 目錄

- [0. 這場演講要做什麼](#0-這場演講要做什麼)
- [1. 定義與典型流程（跟第一版相同）](#1-定義與典型流程跟第一版相同)
- [2. 2021 年結果回顧](#2-2021-年結果回顧)
- [3. 兩年來的變化：NXP、Marvell、NVIDIA、Allwinner](#3-兩年來的變化nxpmarvellnvidiaallwinner)
- [4. MediaTek](#4-mediatek)
- [5. Rockchip](#5-rockchip)
- [6. 新總表與結論](#6-新總表與結論)
- [7. Q&A](#7-qa)
- [8. 一頁速查表](#8-一頁速查表)
- [9. 延伸連結](#9-延伸連結)

---

## 0. 這場演講要做什麼

[▶ 02:06](https://youtu.be/jdDZst29VLo?t=126)（p.2）

1. 定義與典型流程（重講一次）。
2. 2021 年第一版的結果。
3. 這次新查的兩家：**MediaTek**、**Rockchip**。
4. 比較兩版差在哪。

---

## 1. 定義與典型流程（跟第一版相同）

[▶ 04:12](https://youtu.be/jdDZst29VLo?t=252)（p.5–8）

跟第一版一樣：
- 這裡說的 secure boot 是 Arm boot ROM 的功能，其實比較像 verified boot。
- 公鑰燒在 eFuse/OTP，boot ROM 是 root of trust。
- 簽過的 binary＝原檔加一個帶簽章的 header。

口頭多講的幾點：
- 【口頭】必須假設 boot ROM 是 root of trust，因為大多數是閉源的。「如果開源會比較好，但現實就是這樣。」（[▶ 05:19](https://youtu.be/jdDZst29VLo?t=319)）
- 【口頭】**驗證失敗會發生什麼，要看廠商**（[▶ 08:01](https://youtu.be/jdDZst29VLo?t=481)）。
- 【口頭】header 格式不只各廠商不同，**同一家廠商用不同簽章工具也可能不同**。實用技巧：簽完之後 **dump 簽好 image 的前幾個 byte**，檢查是不是如預期（[▶ 09:07](https://youtu.be/jdDZst29VLo?t=547)）。

---

## 2. 2021 年結果回顧

[▶ 09:07](https://youtu.be/jdDZst29VLo?t=547)（p.9）

講者口頭的回顧：

| 分類 | 廠商 |
|---|---|
| 沒有 NDA 問題，文件、燒 fuse／簽章工具都拿得到 | NXP（i.MX、Layerscape）、ST、Xilinx、NVIDIA |
| 有 secure boot，但要 NDA | Marvell Armada、TI Sitara、Qualcomm、Microchip |
| 部分文件有、部分沒有，工具找不到或用不起來 | Rockchip、Allwinner |

> 注意：講者這裡說「11 家裡 5 家」完全開放，並把 Marvell 放在 NDA 那組。第一版（06a）的表把 Marvell 算成「靠 GitHub 資訊不簽 NDA 也能做」，所以第一版說的是 6 家。

---

## 3. 兩年來的變化：NXP、Marvell、NVIDIA、Allwinner

### 3.1 NXP：還是最好入門

[▶ 10:43](https://youtu.be/jdDZst29VLo?t=643)（p.10）

- 【口頭】要在 Arm SoC 上開始做 secure boot，**NXP 是最簡單的起點**：文件齊全。
- 機制：
  - **HABv4**：i.MX50、53、6、7、8M。應用筆記 AN4581。
  - **AHAB**（Advanced HAB）：i.MX8、8X。應用筆記 AN12312。
  - **QorIQ Trust Architecture**：Layerscape。
- **變化**：【口頭】應用筆記現在要**免費註冊**才拿得到（[▶ 11:21](https://youtu.be/jdDZst29VLo?t=681)）。i.MX 簽章工具還是免費註冊；Layerscape 還是包在 LSDK 裡。

### 3.2 Marvell Armada：資訊更難找

[▶ 11:55](https://youtu.be/jdDZst29VLo?t=715)（p.11）

- 文件還是要 NDA。38x/39x 的手冊直接寫要 NDA；其他系列（例如 8K）只提到有 secure boot（[▶ 12:26](https://youtu.be/jdDZst29VLo?t=746)）。
- **變化**：第一版說 U-Boot repo 裡有教學，**新版 U-Boot 已經沒有了**，只剩舊的 2018 分支有（[▶ 12:57](https://youtu.be/jdDZst29VLo?t=777)）。
- 那份流程理論上適用 38x、39x、7k/8k，但**只是理論，沒有實際範例**。【口頭】所以很可能出錯。

### 3.3 NVIDIA Tegra：文件互相矛盾

[▶ 13:28](https://youtu.be/jdDZst29VLo?t=808)（p.12）

- 文件「不確定」：
  - 一處說可以做 secure boot，提到 `flash.sh`。
  - 另一處說 secure boot **以後才會有**。【口頭】沒人知道「以後」是什麼時候（[▶ 13:59](https://youtu.be/jdDZst29VLo?t=839)）。
- 燒 fuse 還是 `odmfuse.sh`，但文件看起來過時了。
- **失敗案例**（[▶ 14:30](https://youtu.be/jdDZst29VLo?t=870)）：
  - NVIDIA 論壇有人燒 fuse 後**板子壞了**。
  - 原因：**不是每塊板子都能燒**。
  - 【口頭】燒之前要先查序號，有些支援、有些不支援。

### 3.4 Allwinner：有人做成了，但有一個大洞

[▶ 14:30](https://youtu.be/jdDZst29VLo?t=870)（p.13）

- 還是沒有官方文件。
- **論壇上有人在 NanoPi Neo（Allwinner H3）上做成了**（[▶ 15:03](https://youtu.be/jdDZst29VLo?t=903)）：
  - 列了 10～15 個有用的連結和完整驗證流程。
  - 用 **sunxi-tools** 產生金鑰、燒 fuse、做簽好的 SPL。
- **大漏洞：FEL 模式**（[▶ 15:38](https://youtu.be/jdDZst29VLo?t=938)）：
  - **驗證失敗時，平台一定會進 FEL 模式**（一種除錯模式），可以從 USB 存取。
  - 【口頭】所以驗證失敗後，任何人都能接 USB，**讀出 fuse 內容，甚至抹掉**。
  - **論壇上的解法：把那個 USB 埠的資料線毀掉**。這樣就算進了 FEL，也讀不到東西（[▶ 16:16](https://youtu.be/jdDZst29VLo?t=976)）。

**教訓**（以下**不是逐字稿內容**，是依這個例子整理的）：secure boot 不只要看「驗證成功時」，還要看「**驗證失敗時晶片退到哪裡**」。如果退到一個能從外部存取的除錯模式，整個保護就被繞過了。

> ⚠️ 逐字稿缺字：「cell mode」＝FEL mode；「sanction tools」＝sunxi-tools（依 p.13）。

---

## 4. MediaTek

### 4.1 信任鏈

[▶ 16:46](https://youtu.be/jdDZst29VLo?t=1006)（p.14）

- 文件在 MediaTek 的 GitLab pages（AIoT 開發指南的 Yocto secure boot 頁）。
- 【口頭】文件是照 Yocto 寫的，步驟要在 Yocto build 系統裡做。投影片寫「但也可以拿來用」。
- 信任鏈：

| 段 | 誰驗誰 | 用什麼 |
|---|---|---|
| 1 | **MediaTek BootROM**（root of trust）驗 **TF-A BL2** | eFuse 裡的 ROTPK 雜湊 |
| 2 | BL2 驗 BL3x（BL31、OP-TEE BL32、U-Boot BL33） | TF-A Trusted Board Boot |
| 3 | U-Boot 驗 kernel | U-Boot FIT verified boot |

**MediaTek BootROM 的漏洞**（[▶ 17:18](https://youtu.be/jdDZst29VLo?t=1038)）：
- 【口頭】有好幾份報告指出：**在某種特殊的上電情境下，boot ROM 會跳過 image 驗證，照樣載入韌體**。
- 【口頭】也就是說，就算公鑰燒在 fuse 裡、韌體也簽了，攻擊者給一個**沒簽的** image，再利用這個漏洞，平台還是開得起來（[▶ 17:59](https://youtu.be/jdDZst29VLo?t=1079)）。
- p.14 附了報告連結（短網址）。講者沒有說是哪些晶片、怎麼觸發。

### 4.2 開機時 BL1 怎麼驗 BL2

[▶ 18:30](https://youtu.be/jdDZst29VLo?t=1110)（p.15）

1. BL1（boot ROM）從 eFuse 讀出 **ROTPK 的雜湊**。
2. 算 BL2 image 裡附帶的 ROTPK 的 SHA-256。
3. **比對**：不一樣就停機；一樣才進行簽章驗證。
4. 驗 BL2 的簽章，算 BL2（loader）的 SHA-256，再比對一次。
5. 一樣才繼續，載入 BL3x。

**投影片和口頭說法不完全一樣**：
- p.15 寫「BL1 **解密** loader 的簽章，再算 loader 的 SHA-256」。
- 口頭說「從 BL2 載入簽章，也算它的 SHA，再比對」（[▶ 19:04](https://youtu.be/jdDZst29VLo?t=1144)）。
- 兩邊都記下來。

### 4.3 怎麼開啟（全靠 NDA 工具）

[▶ 19:04](https://youtu.be/jdDZst29VLo?t=1144)（p.16）

**哪些 SoC 能開不清楚**：
- 文件只提到 **MT8365** 和 **MT8395**。
- 【口頭】不同 SoC 的 **eFuse index 可能不同**，燒之前一定要確認，但這些資訊**要 NDA**（[▶ 19:34](https://youtu.be/jdDZst29VLo?t=1174)）。

**步驟**：

1. 產生兩把私鑰，交給 build 系統：
   - **`efuse.pem`**：簽 BL2。
   - **`da.pem`**：簽 **Download Agent**（DA）。
     - DA 只在燒錄時用：專屬的燒錄工具用它把 image 燒進板子（[▶ 20:06](https://youtu.be/jdDZst29VLo?t=1206)）。
   - 簽章工具要 NDA。
2. 用 **eFuse Writer** 工具（也只有 NDA 才拿得到）執行開啟程序（p.16）：
   1. 讀 **SBC**（Secure Boot Check）和 **DAA**（Download Agent Authentication）兩個 eFuse 位元的狀態，應該都是 0。
   2. 確認 **Public Key Hash0** 這個 eFuse 欄位是空的。
   3. 把 SBC 和 DAA 設成 1（**只能做一次**）。
   4. 寫入 `efuse.pem` 的公鑰部分（自己算，或從 build BL2 的 log 裡拿）。
3. 之後用這把公鑰驗簽好的韌體（[▶ 20:42](https://youtu.be/jdDZst29VLo?t=1242)）。

**兩個 eFuse 位元各防什麼**（以下**不是逐字稿內容**，是依名稱和 p.16 推論的）：
- **SBC**：開機時 ROM 要不要驗 BL2。
- **DAA**：燒錄時 ROM 要不要驗 Download Agent。只開 SBC、不開 DAA 的話，燒錄這條路就沒有保護。
- 講者沒有解釋這兩個位元的差別。

**新總表裡 MediaTek 的結論**（p.22）：文件要 NDA、應用筆記有、燒 fuse 工具要 NDA、簽章工具要 NDA，**不簽 NDA 做不了**。

---

## 5. Rockchip

### 5.1 信任鏈

[▶ 21:12](https://youtu.be/jdDZst29VLo?t=1272)（p.17）

- BootROM 用 **eFuse 或 OTP** 裡的公鑰建立 root of trust，看哪一顆 SoC：
  - eFuse：RK3399、RK3288。由 PC 工具燒。
  - OTP：RK3308、RK3326、PX30、RK3328。由 miniloader 寫。
- 驗證通過後，root of trust 延伸成信任鏈：
  - **SPL 驗 U-Boot，U-Boot 驗 kernel，兩段都用 FIT verified boot**（[▶ 21:47](https://youtu.be/jdDZst29VLo?t=1307)）。

**建立信任鏈要做的事**（p.17）：
1. 產生金鑰對。
2. 把公鑰燒進 eFuse（或 OTP）。
3. 簽 **`idbloader.img`**（U-Boot TPL＋SPL 合成一個檔）。
4. 在 SPL 和 U-Boot 設定 verified boot。
5. 燒簽好的韌體。

- 【口頭】Rockchip（和 Allwinner）的文件**很難找**，找到的通常也過時、很短、不太有用（[▶ 22:20](https://youtu.be/jdDZst29VLo?t=1340)）。p.17 寫找到的文件是 2019 年的。

### 5.2 開啟流程（講者因時間跳過，只看投影片）

[▶ 22:54](https://youtu.be/jdDZst29VLo?t=1374)（p.18）

講者說「跟上一頁差不多，時間不夠，跳過」。【投影片補充】p.18 的 host／target 流程：

1. host 產生 RSA 金鑰對，用它簽 Rockchip loader binary。
2. 用 **eFUSE Tool** 把簽好的 binary 送到 target。target 取出公鑰，把**公鑰雜湊**存進 eFuse，並開啟 secure mode。
3. host 準備帶簽好 TPL＋SPL 的韌體 image。
4. 用 **rkdeveloptool** 再送一次簽好的 loader。target 用 eFuse 裡的金鑰驗它；通過後執行 DDR init，解鎖 MaskROM，允許燒錄。
5. 送韌體、燒錄、重開機。
6. 金鑰燒對、韌體簽對的話，裝置就會開燒進去的韌體。

### 5.3 簽章工具

[▶ 23:24](https://youtu.be/jdDZst29VLo?t=1404)（p.19）

| 工具 | 平台 | 現況 |
|---|---|---|
| `rk_sign_tool` | Linux | 在 `rockchip-linux/rkbin` repo 的 `tools/` |
| Secure Boot Tool | Windows | 以前在 `tools` repo，**現在找不到了** |

- 【口頭】Rockchip 的 repo 維護方式是：**東西過一陣子可能就不見了**（[▶ 23:56](https://youtu.be/jdDZst29VLo?t=1436)）。
- `rk_sign_tool` 能產生金鑰，Linux、Windows 工具都能用。
- `rkbin` 也提供每顆 SoC 的 `*.ini`（例如 RK3288 用 `RK3288MINIALL.ini`）。用 `boot_merger` script 依 `.ini` 做出 loader，再用任一工具簽。

### 5.4 燒 eFuse

[▶ 24:27](https://youtu.be/jdDZst29VLo?t=1467)（p.20）

- 用 **eFUSE Tool**，也是 Windows 工具，而且**只接受 Secure Boot Tool 簽的 binary**。
- **燒 eFuse 時要另外供電**（[▶ 24:57](https://youtu.be/jdDZst29VLo?t=1497)）：
  - RK3399 有一根 `VCC18V_EFUSE` 腳。
  - 有些板子有專門的電路。
  - 沒有的話，要自己找到對的腳或測試點供電，p.20 寫「然後祈禱一切順利」。
  - 這是從另一份很難找的文件看到的。

### 5.5 總結：卡在找不到工具

[▶ 25:29](https://youtu.be/jdDZst29VLo?t=1529)（p.21）

1. 用 `boot_merger` 做 loader。
2. 用 `rk_sign_tool` 做金鑰。
3. **用 Secure Boot Tool 簽 loader**。
   - 【口頭】他們試過用 `rk_sign_tool` 簽，**不行**。目前看來**只有 Secure Boot Tool 簽的 binary 才能用**，但**現在下載不到這個工具**（[▶ 26:00](https://youtu.be/jdDZst29VLo?t=1560)）。
4. 用 eFUSE Tool 燒 fuse（同樣要找工具在哪裡下載）。
5. 用 `rkdeveloptool` 載入簽好的 loader，開啟 secure boot。
- 細節在 3mdeb 的部落格文章（2021-12-03）。

---

## 6. 新總表與結論

### 6.1 新總表

[▶ 27:03](https://youtu.be/jdDZst29VLo?t=1623)（p.22；原圖，照抄成表）

| SoC | 文件 | 應用筆記／教學 | 燒 fuse 工具 | 簽章工具 | 不簽 NDA 能用嗎？ |
|---|---|---|---|---|---|
| NXP i.MX 6/7/8 | Yes (1) | Yes (1) | Yes | Yes (1) | Yes |
| NXP Layerscape | Yes (1) | Yes (1) | Yes | Yes (1) | Yes |
| Marvell Armada | NDA | NDA | Yes | Yes | **No** |
| ST STM32MP1 | Yes | Yes | Yes (1) | Yes (1) | Yes |
| Xilinx Zynq | Yes | Yes | Yes | Yes | Yes |
| NVIDIA Tegra | 有些誤導 | 有些誤導 | Yes (1) | Yes (1) | Yes |
| Microchip SAMA5 | NDA | NDA | NDA | NDA | No |
| TI Sitara | NDA | NDA | NDA | NDA | No |
| Qualcomm | NDA | NDA | NDA | NDA | No |
| Rockchip | 有些文件流傳 | 有些教學 | Yes | Yes | **Yes** |
| Allwinner | 論壇上有些討論 | 有些教學 | Yes | Yes | **Yes** |
| **MediaTek**（新） | NDA | Yes | NDA | NDA | **No** |

(1)＝要免費註冊。

**跟第一版比的變化**（口頭，[▶ 27:03](https://youtu.be/jdDZst29VLo?t=1623)）：
- NXP：SoC 參考文件現在要註冊。
- NVIDIA：文件不確定、可能過時。
- Rockchip：**現在知道做得到**，但文件品質差。Allwinner 同樣。
- MediaTek：要 NDA。
- 表上 Marvell 從「Yes (2)」變成「No」。講者沒有特別解釋，推測是因為 U-Boot 文件拿掉了。⚠️ 待確認

### 6.2 結論

[▶ 27:37](https://youtu.be/jdDZst29VLo?t=1657)（p.23）

1. 兩年來知道得更多了，例如現在知道 Rockchip 怎麼開。
2. 原則各家相同：執行前驗 image；私鑰簽、公鑰燒在 SoC 裡驗；**boot ROM 還是被當成 root of trust**。
3. 全部用 **SHA-256**。用的金鑰種類越來越多樣。
4. **文件品質不好**：
   - 【口頭】越來越多情況文件要 NDA，或品質真的不好。
   - p.23：**亂動 fuse 可能讓硬體變磚**。
   - p.23：有些情況有工具，但使用手冊要 NDA。

---

## 7. Q&A

【Q&A】**Q：NXP 可以在 bootloader 裡呼叫 ROM 來驗其他東西（FIT、U-Boot 等），讓 ROM 當所有東西的 root of trust。其他家有類似功能嗎？**（[▶ 28:39](https://youtu.be/jdDZst29VLo?t=1719)）

- 答：據他們所知，**沒有**，只有 NXP 有（[▶ 29:48](https://youtu.be/jdDZst29VLo?t=1788)）。

【Q&A】**Q：各家對不同信任邊界的多把金鑰支援如何？例如發一把委派金鑰給亞洲的生產線，之後用 rollback level 之類的方法撤銷它？**（[▶ 29:48](https://youtu.be/jdDZst29VLo?t=1788)）

- 答：要看 SoC 有沒有機制放**不只一把**公鑰。
- 這些都是一次性燒進 SoC 的。**如果只有一個位置，就只能有一把**驗證用的金鑰（[▶ 30:57](https://youtu.be/jdDZst29VLo?t=1857)）。

---

## 8. 一頁速查表

**MediaTek（跟 MT8189 最相關）**

```
BootROM(BL1) ─eFuse: ROTPK hash─▶ 驗 BL2（SBC 位元開啟時）
BL2 ─TF-A TBB─▶ BL31 / BL32(OP-TEE) / BL33(U-Boot)
U-Boot ─FIT verified boot─▶ kernel
燒錄路徑：ROM ─驗 DA（DAA 位元開啟時）─▶ Download Agent
```

開啟步驟：`efuse.pem` 簽 BL2、`da.pem` 簽 DA → eFuse Writer 確認 SBC=DAA=0、Hash0 空 → 設 SBC=DAA=1（一次性）→ 寫公鑰雜湊。工具和 eFuse index 都要 NDA。已知有 boot ROM 在特殊上電情境下跳過驗證的報告。

**各家「驗證失敗後退到哪裡」要特別看**

| 廠商 | 這場提到的風險 |
|---|---|
| Allwinner | 驗證失敗進 FEL（USB 除錯模式），可讀／抹 fuse；民間解法是毀掉 USB 資料線 |
| MediaTek | boot ROM 漏洞可在特殊情境跳過驗證 |
| NVIDIA | 不是每塊板子都能燒，燒錯會壞 |
| Rockchip | 燒 eFuse 要外部供電；只認 Windows 工具簽的 binary，工具已下架 |

---

## 9. 延伸連結

- MT8189 上的 BL2 eFuse／SBC（`BL2_SIGN_ENABLE`）、TF-A TBB、FIT 簽章：[`../verified-boot-notes/vb-intro.md`](../verified-boot-notes/vb-intro.md)、[`../verified-boot-notes/fit-sign.md`](../verified-boot-notes/fit-sign.md)
- TF-A 端 secure boot：[`../tf-a-and-op-tee-note/secure-boot-intro.md`](../tf-a-and-op-tee-note/secure-boot-intro.md)
- 第一版：[06a](06a-pijanowski-secure-boot-arm-socs-overview.md)

---

## 附：一句話總結

> **兩年後原理沒變，但文件變得更難拿：Rockchip、Allwinner 證實做得到，卻卡在工具下架、驗證失敗退到 FEL 這類坑；MediaTek 的鏈是「ROM 用 eFuse 驗 BL2 → TF-A TBB → U-Boot FIT」，但開 SBC/DAA 的工具和 eFuse 位置都要 NDA。**

---

## ⚠️ 待確認清單

1. p.22 Marvell 從第一版的「Yes (2)」變成「No」，講者沒有解釋。

---

*筆記依據 Tomasz Żyjewski〈Overview of Secure Boot state in the ARM-based SoCs 2nd edition〉（FOSDEM 2023）錄影（Whisper `turbo` 轉錄，31:29）與 FOSDEM 官方附件投影片整理。*
