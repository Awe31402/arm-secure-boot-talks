---
talk: Arm Trusted Firmware for coreboot developers
speaker: Julius Werner（Google，Chrome OS firmware；coreboot ARM 維護者）
conference: Open Source Firmware Conference（OSFC）2018
year: 2018
video: https://youtu.be/UC35q4OJg3k
slides: 待補（osfc.io、pretalx 都沒附投影片）
---

# Arm Trusted Firmware for coreboot developers [▶ 影片](https://youtu.be/UC35q4OJg3k)

> **演講**：Julius Werner（Google Chrome OS 韌體、coreboot ARM 架構維護者），OSFC 2018（2018 年 9 月）
> **來源**：YouTube 錄影（39:22）用 Whisper `turbo` 轉成逐字稿。**找不到官方投影片**，所以講者說「這張投影片」的圖、linker script、程式碼，筆記裡都沒有。
> **標記說明**：`【口頭】` 這場沒有投影片，正文幾乎全是口頭，所以只標實務經驗和取捨。`【Q&A】` 是現場提問。`⚠️ 逐字稿缺字` 是 Whisper 聽錯。`⚠️ 待確認` 是查不清楚的地方。
> **範圍提醒**：這場的主題是「為什麼 coreboot 在 arm64 要用 TF-A 的 BL31」，不是 secure boot。信任鏈只在 Q&A 出現一次（第 8 節）。

---

## 目錄

- [0. 這場演講要做什麼](#0-這場演講要做什麼)
- [1. 為什麼 arm64 一定要有 secure monitor：PSCI](#1-為什麼-arm64-一定要有-secure-monitorpsci)
- [2. TrustZone 在講者眼中是什麼](#2-trustzone-在講者眼中是什麼)
- [3. coreboot 只拿 BL31](#3-coreboot-只拿-bl31)
- [4. 移植新 SoC：TF-A 原始碼怎麼看](#4-移植新-soctf-a-原始碼怎麼看)
- [5. PSCI 的平台回呼：power level、power state](#5-psci-的平台回呼power-levelpower-state)
- [6. 自訂 SMC、coreboot 傳參數給 BL31](#6-自訂-smccoreboot-傳參數給-bl31)
- [7. 實戰故事：RK3399 把 suspend 塞進 8 KiB](#7-實戰故事rk3399-把-suspend-塞進-8-kib)
- [8. Q&A](#8-qa)
- [9. 一頁速查表](#9-一頁速查表)
- [10. 延伸連結](#10-延伸連結)

---

## 0. 這場演講要做什麼

[▶ 00:31](https://youtu.be/UC35q4OJg3k?t=31)

- **對象**：懂 coreboot、但不懂 TF-A 的人。
- **要回答的問題**：為什麼 coreboot 在 arm64 上要用 TF-A。
- 【口頭】講者原本想講「coreboot on arm64」，接續他 2016 年講的 arm32 版。但他發現：
  - 在 coreboot 這邊，32 位元和 64 位元幾乎沒差別。
  - **真正的差別只有 TF-A 這一塊**（[▶ 01:41](https://youtu.be/UC35q4OJg3k?t=101)）。
  - 所以就專講這一塊。
- 【口頭】Arm 自己在前一場也講了 TF-A，所以內容可能有點重複。

---

## 1. 為什麼 arm64 一定要有 secure monitor：PSCI

[▶ 01:41](https://youtu.be/UC35q4OJg3k?t=101)

**起點是 Linux 對韌體的要求**：
- Linux 的 device tree 文件說，CPU 執行期電源管理（把 CPU 關掉、打開）要靠 **PSCI**（Power State Coordination Interface）。
- arm32 上這是選配。
- **arm64 上是必要的。**

### 1.1 arm32 時代怎麼做

[▶ 05:55](https://youtu.be/UC35q4OJg3k?t=355)

CPU idle 完全由 Linux 自己處理：
1. Linux 關掉 CPU 的電源軌，執行 `WFI`。
2. CPU 醒來時，直接回到 Linux。
3. Linux 自己重新初始化。

### 1.2 有 TrustZone 之後為什麼不行

[▶ 06:26](https://youtu.be/UC35q4OJg3k?t=386)

兩個問題：

1. **secure world 也要用這顆 CPU。**
   - Linux 說「我不要這顆 CPU 了」，還得先問 secure world 要不要。
   - 也許 secure world 還需要它，CPU 就得留著。
2. **CPU 完全斷電後，狀態全沒了，有些狀態 kernel 不能碰。**
   - 例子：page table base 暫存器。kernel 有一個，secure monitor 也有自己的一個。
   - kernel 不能寫 secure monitor 的那個，否則破壞安全模型。
   - 所以 secure monitor 的部分，只能由 secure monitor 自己重新初始化。

**結論**：每一次 CPU 關、開都要經過 secure monitor，再回到 kernel。Arm 為此定了標準介面 **PSCI**。它建在 **SMC**（Secure Monitor Call）上：SMC 就像 system call，只是對象是 secure monitor 那一層（[▶ 07:32](https://youtu.be/UC35q4OJg3k?t=452)）。

### 1.3 為什麼 arm32 可以不管、arm64 不行

[▶ 08:07](https://youtu.be/UC35q4OJg3k?t=487)

- TrustZone 在 arm32 後期就有，同樣的問題那時就存在。
- 但 Linux 一直支援「不用 TrustZone」的系統。coreboot 從來不需要 secure 應用，就直接忽略它。
- arm64 上 Linux **一刀切**：既然所有系統都有 TrustZone，那就靠它，自己不再實作 CPU 電源管理。
- 【口頭】講者的說法：arm64 要提供 PSCI，「其實只是因為 **Linux 變懶了**」。所以就算不用 secure 部分，要跑完整的 Linux，韌體也得提供 PSCI（[▶ 08:37](https://youtu.be/UC35q4OJg3k?t=517)）。

---

## 2. TrustZone 在講者眼中是什麼

[▶ 02:44](https://youtu.be/UC35q4OJg3k?t=164)

【口頭】很多人以為 TrustZone 是「跑邪惡程式、監視你、跑 DRM」的可怕東西。講者想打破這個印象：
- **跑開源韌體的話，TrustZone 也可以是開源的。**
- 它只是一個架構功能：讓程式在 kernel 之外跑。

**跟 x86 SMM 比**（[▶ 03:17](https://youtu.be/UC35q4OJg3k?t=197)）：
- 概念類似 x86 的 System Management Mode。
- 差別：SMM 是醜陋的歷史包袱；TrustZone 是乾淨地擴充現有架構。

**架構**（[▶ 03:47](https://youtu.be/UC35q4OJg3k?t=227)）：
- 把「kernel／user space」的概念往上加一層。
- user space 對 kernel 做 system call；kernel 對 secure monitor 做 SMC。
- TrustZone 不只是 secure monitor，而是右邊整套：獨立的 OS 加 user space，跑 trusted application。

**兩個安全上的性質**（[▶ 04:18](https://youtu.be/UC35q4OJg3k?t=258)）：

1. **單行道**：secure 可以存取 non-secure，反過來不行。
2. **secure 這一側沒有真正的記憶體隔離**：secure OS 可以存取 secure monitor 的記憶體，所以**能攻擊 secure monitor**。除非用前一場講到的新架構功能。

**Exception level**（[▶ 04:48](https://youtu.be/UC35q4OJg3k?t=288)）：
- EL0 user space、EL1 kernel、EL2 hypervisor、**EL3 secure monitor**（最高權限）。
- secure monitor 的工作是在 trusted application 和主 OS 之間仲裁。

**哪些記憶體是 secure，完全由 SoC 決定**（[▶ 04:48](https://youtu.be/UC35q4OJg3k?t=288)）：
- Arm 架構**沒有**統一的方法規定哪段記憶體是 secure。
- 每家 SoC 自己做，通常是 range register：「從這個 offset 開始、這麼大，屬於 secure」。
- 不只 DRAM，是**整個實體位址空間**，包括 MMIO 周邊。例如可以讓某個 I2C 控制器只歸 secure world，non-secure 存取不到（[▶ 05:22](https://youtu.be/UC35q4OJg3k?t=322)）。

---

## 3. coreboot 只拿 BL31

### 3.1 TF-A 對 coreboot 有什麼好處

[▶ 09:08](https://youtu.be/UC35q4OJg3k?t=548)

- TF-A 是 Arm 的參考韌體，包含開機韌體和執行期韌體兩部分。
- coreboot 本身就是開機韌體，所以只要**執行期**那部分，也就是 **BL31**。BL31 就是常駐的 secure monitor，PSCI 在這裡。

BL31 有、但 coreboot 傳統上沒有的東西：

| 功能 | 為什麼重要 |
|---|---|
| **多處理器** | coreboot 在 ARM 上只用開機那一顆核心。要提供開關 CPU 的服務，就得處理 coherency、mutex 等等 |
| **CPU 核心支援與 errata** | 每顆 Arm 核心（A53、A57、A7x…）都有自己的怪癖和 errata（勘誤）。由 CPU 廠自己寫好，不用自己追 |

【口頭】講者不只一次遇到：在既有的 ARM 系統上換新版 TF-A，開機 log 就提醒「發現你的 CPU 有一個新的 errata」（[▶ 10:43](https://youtu.be/UC35q4OJg3k?t=643)）。

> ⚠️ 逐字稿缺字：「b031」＝BL31；「Iwata」＝errata；「core wood／Corvoo」＝coreboot。

### 3.2 TF-A 各段對應 coreboot 哪裡

[▶ 10:43](https://youtu.be/UC35q4OJg3k?t=643)

| TF-A | coreboot |
|---|---|
| BL1、BL2（純開機韌體） | coreboot 的三個 stage（bootblock、romstage、ramstage） |
| BL31（secure monitor） | **coreboot 沒有，整段拿過來用** |
| BL32、BL33（不是 TF-A 的一部分，只是它給「之後載入的東西」取的名字） | coreboot payload（也不是 coreboot 的一部分） |

### 3.3 怎麼整合

[▶ 11:52](https://youtu.be/UC35q4OJg3k?t=712)

1. TF-A 是 coreboot 的 **git submodule**。checkout coreboot 就有 TF-A 原始碼。
2. build coreboot 時順便 build TF-A，挑出 BL31，放到 coreboot 裡正確的位置。
3. **唯一動到的地方**：ramstage 最後「跳到 payload」那一步。這是架構相關的回呼（[▶ 12:26](https://youtu.be/UC35q4OJg3k?t=746)）。有 TF-A 時改成：
   - 先別跳 payload，先載入並執行 BL31。
   - 告訴 BL31「做完之後怎麼跳到 payload」。payload 這時已經載好了。
4. 好處：**BL31 不需要知道怎麼讀 flash**。下一段已經在記憶體裡了。

---

## 4. 移植新 SoC：TF-A 原始碼怎麼看

[▶ 12:59](https://youtu.be/UC35q4OJg3k?t=779)（講者用一張目錄結構投影片，筆記看不到）

- **只用 BL31 的話**，`bl1/`、`bl2/` 可以不管。
- **文件很好**。【口頭】講者特別推薦 **porting guide**：要定義的 macro、要實作的函式都列在裡面，移植新平台看這份就夠了（[▶ 13:34](https://youtu.be/UC35q4OJg3k?t=814)）。
- **driver 依廠商分目錄**（[▶ 14:07](https://youtu.be/UC35q4OJg3k?t=847)）：
  - GIC（大部分 SoC 用）在 `arm/` 下面。
  - 標準 16550 UART 在 `ti/` 下面。
  - 不能共用的 driver 都放在平台目錄。
- 【口頭】框架本身很精簡，大部分東西由平台自己實作，**每個平台想怎麼做就怎麼做**。
- **CPU 支援是少數通用的部分**（[▶ 14:38](https://youtu.be/UC35q4OJg3k?t=878)）：
  - 在 makefile 加上 SoC 有的 CPU。
  - 開核心時讀識別暫存器（ID register），自動挑對應的 CPU 程式碼。
- **平台目錄**（[▶ 15:08](https://youtu.be/UC35q4OJg3k?t=908)）：
  - `common/`：大多數平台用得上的預設回呼，直接連結進來。
  - 每個平台通常有：
    - `plat_setup`：開機時第一個跑，做開機初始化。
    - `pm`：實作 PSCI 回呼。
  - 很多廠商會把共用的部分和每顆 SoC 的部分分開放。
- **設定**：沒有 Kconfig 之類的框架，全部是 makefile 裡的選項，加上 makefile 連結哪些 driver（[▶ 15:40](https://youtu.be/UC35q4OJg3k?t=940)）。

**要支援 coreboot，真正要實作的只有 PSCI。**

---

## 5. PSCI 的平台回呼：power level、power state

[▶ 16:11](https://youtu.be/UC35q4OJg3k?t=971)

重點：**非常彈性，照你的 SoC 怎麼做最好就怎麼做。**

**Power level**（電源層級，描述拓撲）：
- 最底層一定是 CPU（有多執行緒的話是 thread）。
- 上面可以疊任意多層，也可以不疊。大多數 SoC 至少有 cluster。
- cluster 裡的 CPU 全關了，就可以再關掉 cluster 的東西（[▶ 16:43](https://youtu.be/UC35q4OJg3k?t=1003)）。
- 告訴框架最高到哪一層，框架就會對每一層呼叫對的函式。

**Power state**（電源狀態，跟 level 正交）：
- 不只開和關，中間可以有任意多種狀態，在「醒來延遲」和「耗電」之間取捨（[▶ 17:15](https://youtu.be/UC35q4OJg3k?t=1035)）。
- 對框架只要說明是哪一種：

| 種類 | 狀態保留嗎 | 誰負責恢復 |
|---|---|---|
| off | 全部消失 | 框架回來時幫你重新初始化 |
| retention | 要保留 | 不用重建 |

**要實作的東西**（[▶ 17:46](https://youtu.be/UC35q4OJg3k?t=1066)）：
- 一個**裝滿函式指標的 struct**。
- 內容是各種回呼：怎麼關掉某個節點（不只 CPU）、怎麼打開、打開之後做什麼（`finish` 回呼）……
- 框架會在對的時候呼叫它們。

【口頭】講者最推薦看 **Rockchip** 平台當範例：這些 SoC 很單純，沒有其他複雜 SoC 那些奇怪的角落（[▶ 18:19](https://youtu.be/UC35q4OJg3k?t=1099)）。

---

## 6. 自訂 SMC、coreboot 傳參數給 BL31

### 6.1 自訂 SMC

[▶ 18:19](https://youtu.be/UC35q4OJg3k?t=1099)

- PSCI 的 SMC 框架都做好了，不用管。
- 也可以加自己的 SMC。
- 【口頭】常見需求：**執行期 DDR 換頻**。記憶體是整個平台共用的，要動它通常得經過最高權限那一層（[▶ 18:49](https://youtu.be/UC35q4OJg3k?t=1129)）。
- 做法：有一個 macro，替某個範圍的 SMC function ID 定義 handler。
- Arm 有一份規範，規定哪些 function ID 範圍給誰用。SoC 移植通常用 **SiP** 範圍（Silicon Provider，SoC 廠商範圍）（[▶ 19:19](https://youtu.be/UC35q4OJg3k?t=1159)）。
  - 【口頭】講者說他老是忘記 SiP 代表什麼。

### 6.2 coreboot 怎麼把參數交給 BL31

[▶ 19:19](https://youtu.be/UC35q4OJg3k?t=1159)

**問題**：當時 coreboot 沒有通用的方法傳參數給 TF-A。TF-A 只給**一個平台自訂的指標**，平台自己決定怎麼解讀。

**coreboot 的做法**（[▶ 19:53](https://youtu.be/UC35q4OJg3k?t=1193)）：
1. 用那個指標傳一個**簡陋的 linked list**。
2. BL31 一開始的平台函式先解析它。
3. 其中一項是 **coreboot table 的位址**。

**傳 coreboot table 換到什麼**（[▶ 20:27](https://youtu.be/UC35q4OJg3k?t=1227)）：
- TF-A 裡有一個 coreboot table 的設定函式，提供通用的 coreboot 支援，當時主要是 console：
  - **UART**：直接用 coreboot 給的 UART 資訊，不用把位址寫死。
  - **沿用 coreboot 的設定**：coreboot Kconfig 關掉 UART，就不傳，TF-A 也不用。不用在每個 repo 各關一次。
  - **CBMEM console**：coreboot 有 CBMEM console，TF-A 就自動註冊對應的 console driver。進到 user space 後 dump CBMEM console，**TF-A 的 log 就接在 coreboot 的 log 後面**（[▶ 20:59](https://youtu.be/UC35q4OJg3k?t=1259)）。

---

## 7. 實戰故事：RK3399 把 suspend 塞進 8 KiB

[▶ 21:32](https://youtu.be/UC35q4OJg3k?t=1292)

主題：在 RK3399 上把所有東西「塞進去」的麻煩。

### 7.1 一開始一切都塞得下

1. **suspend/resume**（[▶ 22:03](https://youtu.be/UC35q4OJg3k?t=1323)）：
   - 整機 suspend 會關掉整個系統，所以也要經過 secure monitor。
   - DDR 控制器在 suspend 時會掉狀態，醒來要重新初始化。
   - 重新初始化的程式**不能放 DRAM**。ARM SoC 通常有不少 SRAM，放那裡就好。
2. **執行期 DDR 換頻**（[▶ 22:35](https://youtu.be/UC35q4OJg3k?t=1355)）：
   - SoC 裡有一顆獨立的 **Cortex-M0**。它可以把主 CPU 原地停住、把 DDR 重新 training 到別的頻率、再放主 CPU 走。主 CPU 完全不知道發生了什麼。
   - M0 的程式也要放 SRAM，因為換頻時 DDR 不能用。
3. **硬體 bug 的繞法**（[▶ 23:08](https://youtu.be/UC35q4OJg3k?t=1388)）：
   - 進 suspend 時，如果喚醒中斷剛好在主 CPU 關掉之後到，有時就醒不來。
   - 要有東西等所有 CPU 都關掉之後檢查這個狀況並清掉。又是 M0 上場。

### 7.2 想多省一點電，麻煩就來了

[▶ 23:40](https://youtu.be/UC35q4OJg3k?t=1420)

- 還有一條電源軌可以關，它供應大半顆晶片，關掉能省很多電。
- 問題：**SRAM 也接在這條軌上**。關掉以後，醒來時沒有東西可以 resume。
- 唯一的救星：一小塊 **PMU SRAM**。它在另一條電源軌上，這條軌關掉也還活著（[▶ 24:12](https://youtu.be/UC35q4OJg3k?t=1452)）。
- 但要把所有東西擠進去，限制是：
  - CPU 醒來的入口位址只能給 SoC 高位元，所以要 **64 KiB 對齊**。PMU SRAM 本身是 64 KiB 對齊的，但程式必須放在最開頭（[▶ 24:42](https://youtu.be/UC35q4OJg3k?t=1482)）。
    > ⚠️ 逐字稿缺字：「top 60 bits」，依「64K aligned」應為 top 16 bits。⚠️ 待確認
  - **M0 的程式要 4 KiB 對齊**。

### 7.3 怎麼塞

[▶ 24:42](https://youtu.be/UC35q4OJg3k?t=1482)

1. 原本的 M0 程式整包放不下。
2. 改成**兩個 M0 image**（一個換頻、一個 suspend）。原本是一個 image 加參數，改成啟動 M0 時直接給要用的那個的 base address（[▶ 25:12](https://youtu.be/UC35q4OJg3k?t=1512)）。
3. 還是會和 DDR 初始化程式重疊。
4. 最後發現：DDR 初始化程式**只有入口要在 64 KiB**，後面都是普通程式。所以把它拆開，**夾在 M0 程式的前後**。
5. 一陣搬位元、數指令之後，**全部塞進 8 KiB**（[▶ 25:51](https://youtu.be/UC35q4OJg3k?t=1551)）。

### 7.4 剩下的問題：換頻程式會掉

- S3 會丟掉主 SRAM，換頻程式就沒了。開機後能換頻，suspend/resume 一次後就不能換。
- 醜但直接的解法：**把它快取在 DRAM，每次 resume 再複製回去**（[▶ 25:51](https://youtu.be/UC35q4OJg3k?t=1551)）。

### 7.5 怎麼把 M0 的 binary 包進 BL31

[▶ 26:52](https://youtu.be/UC35q4OJg3k?t=1612)（linker script 和程式在投影片上，筆記看不到）

1. 先把 M0 程式單獨 build 成 strip 過的 binary。
2. makefile 讓那個 binary 成為某個 C 檔的相依項，並把檔名當 preprocessor macro 傳進去（[▶ 27:22](https://youtu.be/UC35q4OJg3k?t=1642)）。
3. 用組語的 `incbin`：讓組譯器在這個位置整個塞進另一個檔案。
4. 前後加 label，C 程式就能拿到它的位址，交給 M0 當 base address。
- 【口頭】資料段放在 64 KiB 之後「剛好就能動」。講者只希望永遠不要遇到編譯器改版把它弄亂（[▶ 26:52](https://youtu.be/UC35q4OJg3k?t=1612)）。

### 7.6 suspend 時 M0 在做什麼

[▶ 27:52](https://youtu.be/UC35q4OJg3k?t=1672)

- M0 的 suspend 程式非常簡單：一個 suspend 狀態值，suspend 時往上數，resume 時再往上數。
- 測得越多，越多問題要繞。
- 【口頭】所以現在**闔上 Chromebook 的蓋子時，那顆 M0 一直在死迴圈裡問「我 resume 了沒？」**。M0 很省電，又跑在 32 kHz，其實沒聽起來那麼瘋。「你只是不該知道香腸是怎麼做的。」（[▶ 28:22](https://youtu.be/UC35q4OJg3k?t=1702)）

---

## 8. Q&A

【Q&A】**Q：S3 resume 後為什麼 DDR 控制器要重新初始化？DDR 不是在 self-refresh 嗎？**（[▶ 28:52](https://youtu.be/UC35q4OJg3k?t=1732)）

- 板子上的 DDR 顆粒確實在 self-refresh。
- 但 **SoC 上的 DDR 控制器**為了省電被關掉了。
- 醒來後要有人告訴控制器：DDR 有幾個 row、bank、column，再叫 DDR 離開 self-refresh。這些程式要放在某個地方。

【Q&A】**Q：為什麼不像 x86 coreboot 那樣，從 flash 跑正常開機流程來初始化？**（[▶ 29:53](https://youtu.be/UC35q4OJg3k?t=1793)）

- 看 SoC。這顆 SoC 本來就設計成從 SRAM resume，不確定能不能重跑 boot ROM 從 flash 開機。
- 【口頭】**另一個理由跟 Chrome OS 的 verified boot 有關**（[▶ 30:23](https://youtu.be/UC35q4OJg3k?t=1823)）：
  - Chromebook 一定先從 **唯讀分區**開機，做完驗證，才跳到可更新的分區。
  - 他們以前吃過虧：**把 resume 路徑綁在唯讀 flash 上是個很糟的主意**。早期 resume 路徑有 bug 就再也修不了。
  - 從 SRAM resume，就永遠可以更新它。

【Q&A】**Q：你把 TF-A 的前幾段換成 coreboot，root of trust 不是從那幾段來的嗎？懂 TF-A 的人會嚇到吧？**（[▶ 30:56](https://youtu.be/UC35q4OJg3k?t=1856)）

- 看你要拿系統做什麼。
- TF-A 有它自己的 trusted boot：每一段驗下一段。但**不一定要用**（[▶ 32:03](https://youtu.be/UC35q4OJg3k?t=1923)）。
- 這裡的目標只是讓 coreboot 在 arm64 上跑起來，需要的是 secure monitor，所以只拿了 secure monitor。
- **coreboot 有自己的 trusted boot**，從 Chrome OS 的做法來，叫 **vboot**（verified boot）。**BL31 是它的一部分**（[▶ 32:35](https://youtu.be/UC35q4OJg3k?t=1955)）：
  1. 從 flash 的**唯讀分區**開機。
  2. 驗證**讀寫分區**。
  3. 再從讀寫分區開機。
  - TF-A 的 BL31 只是放在讀寫分區裡的其中一個元件。

> ⚠️ 逐字稿缺字：「verified boot reboot」＝verified boot（vboot）。

【Q&A】**Q：如果能叫 SoC 廠重新設計 SRAM，你會要什麼？**（[▶ 33:12](https://youtu.be/UC35q4OJg3k?t=1992)）

- 講者不是電源專家。
- 這裡的問題是設計上把所有東西都綁在一條大電源軌上：想關的是別的元件，SRAM 剛好也掛在上面。比較好的做法是把 SRAM 放在獨立的軌或 always-on 軌。
- 不過他們做的事本來就不是晶片的設計用途，是事後才發現「理論上可以關這個」（[▶ 33:43](https://youtu.be/UC35q4OJg3k?t=2023)）。
- 分兩塊 SRAM 的想法不壞，只是 8 KiB 太少。16 或 32 KiB 會好做很多。

【Q&A】**Q：coreboot 傳了哪些資訊給 TF-A？**（[▶ 34:13](https://youtu.be/UC35q4OJg3k?t=2053)）

- coreboot table 位址，加上一些板子相關資訊。
- 【口頭】設計原則：**不要把板子相關的資訊拉進 TF-A**。TF-A 處理的東西幾乎只跟 SoC 有關。如果 TF-A 有「板子」的概念，每塊板子都要有自己的程式，會變得很複雜（[▶ 34:46](https://youtu.be/UC35q4OJg3k?t=2086)）。
- 例外用參數處理：例如重開機，有的板子用外部 GPIO，有的用 SoC 內部機制，就傳一個參數告訴 TF-A 用哪一種。

【Q&A】**評論（觀眾，聽起來是 Arm 的人）：TF-A 現在支援 dynamic configuration，在 image 之間傳 device tree，以後也許可以用。**（[▶ 35:20](https://youtu.be/UC35q4OJg3k?t=2120)）

- 講者聽過，不確定做完了沒，會去看。
- 觀眾補充：目前用在 BL1 和 BL2 之間，沒有理由不能用在 BL31（[▶ 35:53](https://youtu.be/UC35q4OJg3k?t=2153)）。
- 講者：那就是他們在等的擴充，有了才能換成更好的機制。

【Q&A】**Q：用 TF-A 之後開機慢多少？**（[▶ 36:28](https://youtu.be/UC35q4OJg3k?t=2188)）

- 通常不嚴重。TF-A **不做任何 SoC 初始化**，那些都在 coreboot 做。
- 開機時它只設好自己的東西就交棒，它本來就只是提供執行期服務。
- 通常**不到 15 ms**。

【Q&A】**Q：RK3399 原本有一顆專門做 DRAM 換頻的微控制器（DCF），為什麼換成 M0？**（[▶ 36:59](https://youtu.be/UC35q4OJg3k?t=2219)）

- DCF 是 Rockchip 專為換頻做的小微控制器，只有幾個指令，很怪。
- 他們沒有它的組譯器，得跟 Rockchip 要程式碼（[▶ 37:30](https://youtu.be/UC35q4OJg3k?t=2250)）。
- 後來發現有件換頻時要做的事 DCF 做不到。既然旁邊就有一顆完整、通用的 ARM 核心，就改用它。

【Q&A】**Q：TF-A 的前幾段（BL1、BL2）驗證失敗時怎麼處理？是開機還是變磚？coreboot 是一定開得起來、再告訴你出了問題。**（[▶ 38:09](https://youtu.be/UC35q4OJg3k?t=2289)）

- 講者對那兩段不熟。
- 他認為 BL1、BL2 的通用框架很薄，「失敗了怎麼辦」這類事情留給平台決定（[▶ 38:39](https://youtu.be/UC35q4OJg3k?t=2319)）。

---

## 9. 一頁速查表

| 問題 | 答案 |
|---|---|
| arm64 為什麼一定要 EL3 韌體？ | Linux arm64 規定用 PSCI 開關 CPU。CPU 斷電後，secure monitor 自己的狀態只能由 secure monitor 恢復 |
| coreboot 用 TF-A 的哪一段？ | 只用 BL31。BL1/BL2 由 coreboot 的 stage 取代 |
| 整合點在哪？ | ramstage 跳 payload 前先跑 BL31，並告訴它 payload 的入口 |
| 移植要實作什麼？ | PSCI 平台回呼（一個函式指標 struct）＋power level／state 拓撲 |
| 自訂服務？ | SMC handler，用 SiP function ID 範圍 |
| coreboot → BL31 傳參數？ | 一個指標 → linked list → coreboot table（UART、CBMEM console） |
| 用 coreboot 時信任鏈靠誰？ | coreboot 的 vboot：唯讀分區驗讀寫分區，BL31 放在讀寫分區、被 vboot 驗 |
| resume 程式為什麼放 SRAM 不放唯讀 flash？ | 綁在唯讀 flash 的 resume 路徑有 bug 就修不了 |
| TrustZone 的弱點？ | secure 側沒有記憶體隔離，secure OS 可以攻擊 secure monitor |

---

## 10. 延伸連結

- TF-A BL31 執行期與 SMC 流程：[`../tf-a-and-op-tee-note/tfa-intro.md`](../tf-a-and-op-tee-note/tfa-intro.md)、[`../tf-a-and-op-tee-note/smc-call-flow.md`](../tf-a-and-op-tee-note/smc-call-flow.md)
- secure memory 怎麼劃分：[`../tf-a-and-op-tee-note/secure-memory.md`](../tf-a-and-op-tee-note/secure-memory.md)

---

## 附：一句話總結

> **arm64 Linux 把 CPU 電源管理丟給 EL3 的 PSCI，所以就算不用 secure 功能，韌體也得有 secure monitor。coreboot 的做法是只拿 TF-A 的 BL31、用自己的 vboot 驗它，再把平台相關的東西（PSCI 回呼、SMC、suspend 程式）塞進 BL31。**

---

## ⚠️ 待確認清單

1. [▶ 24:42](https://youtu.be/UC35q4OJg3k?t=1482) 「top 60 bits」：依 64 KiB 對齊推測是 top 16 bits，聽不清楚。
2. 沒有官方投影片：目錄結構、linker script、M0 程式等「如圖」的內容都沒有。

---

*筆記依據 Julius Werner〈Arm Trusted Firmware for coreboot developers〉（OSFC 2018）錄影整理（Whisper `turbo` 轉錄，39:22）。沒有投影片。*
