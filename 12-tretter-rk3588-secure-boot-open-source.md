---
talk: Open Source Tools for Secure Boot on Rockchip RK3588
speaker: Michael Tretter（Pengutronix）
conference: Embedded Recipes 2026（Nice）
year: 2026
video: https://youtu.be/PSEJD4Bfnyw
slides: https://cfp.embedded-recipes.org/media/er2026/submissions/ULWYUJ/resources/rockchip-secure-boo_F19lBQL.pdf
---

# Open Source Tools for Secure Boot on Rockchip RK3588 [▶ 影片](https://youtu.be/PSEJD4Bfnyw)

> **演講**：Michael Tretter（Pengutronix），Embedded Recipes 2026（Nice），BayLibre 頻道 2026-06-25 上傳。
> **來源**：YouTube 錄影（13:59）用 Whisper `turbo` 轉成逐字稿，再加上 Embedded Recipes pretalx 上的官方投影片（18 頁）和影片說明欄。
> **標記說明**：`【口頭】` 是投影片沒有的。`【投影片補充】` 是投影片有、講者沒講的。`【說明欄補充】` 是影片說明欄有的。`⚠️ 逐字稿缺字` 是 Whisper 聽錯。
> 這是一場**短講**（約 14 分鐘），沒有 Q&A（講者請大家晚上再找他）。範圍只到「ROM 驗 bootloader」，之後的鏈講者刻意不談。

---

## 目錄

- [0. 這場演講要做什麼](#0-這場演講要做什麼)
- [1. RK3588 的驗證流程](#1-rk3588-的驗證流程)
- [2. 簽 image：Rockchip 原廠 vs barebox](#2-簽-imagerockchip-原廠-vs-barebox)
- [3. 鎖板（燒 OTP）：Rockchip 原廠 vs barebox](#3-鎖板燒-otprockchip-原廠-vs-barebox)
- [4. barebox 的完整步驟](#4-barebox-的完整步驟)
- [5. 建議與參考資料](#5-建議與參考資料)
- [6. 一頁速查表](#6-一頁速查表)
- [7. 延伸連結](#7-延伸連結)

---

## 0. 這場演講要做什麼

[▶ 00:35](https://youtu.be/PSEJD4Bfnyw?t=35)（p.2–4）

【口頭】開場先「一句話講完」（p.2）：產生金鑰、簽 image、把金鑰雜湊燒進硬體，secure boot 就開了，謝謝大家。「看來還有時間，那就仔細看看。」

接下來講（p.4）：
1. RK3588 的 secure boot 怎麼運作。
2. 怎麼簽韌體 image。
3. 怎麼開啟 secure boot。
4. 建議和參考資料。

【說明欄補充】RK3588 硬體支援 secure boot，但文件少，又依賴 Rockchip 的**閉源 OP-TEE binary 和開發工具**，在安全性和可維護性上令人擔心。**OP-TEE 4.9.0 和 barebox v2026.02.0** 起，不需要任何 Rockchip 專屬工具就能在 RK3588 上開 secure boot。說明欄也提到會講「怎麼套用到其他 Rockchip SoC」和「從 Linux 或 U-Boot 使用 OP-TEE PTA」，演講中沒講到。

定義（p.6）：secure boot／verified boot 是一組驗證程序，確保裝置上跑的韌體的完整性與合法性。【口頭】定義「偷」自 Rockchip 的 Secure Boot Developer Guide（[▶ 01:10](https://youtu.be/PSEJD4Bfnyw?t=70)）。

---

## 1. RK3588 的驗證流程

[▶ 01:10](https://youtu.be/PSEJD4Bfnyw?t=70)（p.7–8）

**image 的組成**（p.7 是圖）：Rockchip image 裡有一把**公鑰**、一個**簽章**、一個 **bootloader**。

**開機時 boot ROM 做的事**（p.8）：
1. 從 **secure OTP** 讀出**金鑰雜湊**。
   - OTP 就是只能燒一次、燒了不能改的 eFuse。
   - 【口頭】**RK3588 的 OTP 只有 secure world（EL3）讀寫得到**。「細節不重要，但等一下很重要。」（[▶ 01:43](https://youtu.be/PSEJD4Bfnyw?t=103)）
2. 算 image 裡公鑰的雜湊，跟 OTP 裡的比對。
3. 用這把公鑰驗 image 的簽章。
4. 用 header 裡的雜湊驗 bootloader 那段（sector）。
5. 執行 bootloader。

**我們能改什麼、不能改什麼**（[▶ 02:43](https://youtu.be/PSEJD4Bfnyw?t=163)）：
- 上面全部在 Rockchip 的 boot ROM 裡，**改不了**。只能相信 boot ROM，也只能相信 OTP 真的只能寫一次、開機時不會被改。
- **能改的**：怎麼把公鑰、簽章、雜湊放進去（p.9）：
  - 工廠或 build server 有一組金鑰對。
  - 公鑰放進 image，私鑰簽 image。
  - **要保密的只有私鑰**。
  - 公鑰雜湊要寫進裝置，**這一步也要在安全的環境做**（[▶ 03:17](https://youtu.be/PSEJD4Bfnyw?t=197)）。
  - 【口頭】一定要在你的工廠、完全由你控制。否則有人可以寫入別的雜湊，**secure boot 就破了**（[▶ 03:47](https://youtu.be/PSEJD4Bfnyw?t=227)）。

---

## 2. 簽 image：Rockchip 原廠 vs barebox

[▶ 03:47](https://youtu.be/PSEJD4Bfnyw?t=227)（p.10–11）

| | Rockchip 原廠（downstream） | barebox（upstream） |
|---|---|---|
| 產生金鑰對 | `rk_sign_tool` | **OpenSSL**。【口頭】「OpenSSL 產生的金鑰應該還算可信」（[▶ 05:21](https://youtu.be/PSEJD4Bfnyw?t=321)） |
| 做 image | `mkimage` | barebox 的開源工具 **`rkimage`**，做 image 的同一步就簽好。build 一個開了 secure boot 設定的 barebox，出來的 image 就已經簽好了 |
| 簽 image | `rk_sign_tool` | 同上 |
| 優點 | Rockchip 支援 | **全部開源**：能看原始碼、能改、能自己 build；**支援 PKCS#11**，私鑰可以放 HSM、移出 build 環境（[▶ 05:53](https://youtu.be/PSEJD4Bfnyw?t=353)） |
| 缺點 | **`rk_sign_tool` 只有 binary**，不知道裡面做什麼，「也許可以信，不確定」（[▶ 04:17](https://youtu.be/PSEJD4Bfnyw?t=257)）；**有狀態**：要跑好幾次，背景產生設定檔，很難整合進 build 流程（[▶ 04:48](https://youtu.be/PSEJD4Bfnyw?t=288)）；**HSM 支援不確定**：看過一些線索，但從沒成功接過 HSM | **Rockchip 不支援**。【口頭】「這是缺點還是優點，你自己決定。」可能**缺 Rockchip 有的功能**：他只做了自己需要的（[▶ 06:23](https://youtu.be/PSEJD4Bfnyw?t=383)） |

> ⚠️ 逐字稿缺字：「ROGchip／Robchip」＝Rockchip；「Bearbox」＝barebox；「RK sign tool」＝`rk_sign_tool`。

---

## 3. 鎖板（燒 OTP）：Rockchip 原廠 vs barebox

[▶ 06:23](https://youtu.be/PSEJD4Bfnyw?t=383)（p.12–13）

**前提**：OTP 只有 secure world／EL3 碰得到。

### 3.1 Rockchip 原廠：U-Boot 開機早期寫

p.12；[▶ 06:55](https://youtu.be/PSEJD4Bfnyw?t=415)

1. 把**公鑰放進 U-Boot 的 device tree**。
2. 開機時 U-Boot 算公鑰的雜湊，在**早期開機**（還在 EL3 時）寫進 OTP。

問題：
- **要另外一個 image 專門用來初始化裝置**（帶著 DT 裡的公鑰），工廠要多管理一個 image（[▶ 07:27](https://youtu.be/PSEJD4Bfnyw?t=447)）。
- **執行時無法檢查 secure boot 狀態**：OTP 在 normal world 讀不到，所以**不知道 secure boot 到底開了沒、OTP 裡寫的是哪個雜湊**（[▶ 07:57](https://youtu.be/PSEJD4Bfnyw?t=477)）。

### 3.2 barebox：經 OP-TEE PTA 寫

p.13；[▶ 07:57](https://youtu.be/PSEJD4Bfnyw?t=477)

1. 在 **build 機器上**算公鑰雜湊（`rk-otp.sh`）。
   - 【口頭】公鑰雜湊**可以公開**，可以帶著走。但要確保它的**完整性**（沒被換掉），那是另一個問題（[▶ 08:28](https://youtu.be/PSEJD4Bfnyw?t=508)）。
2. 在裝置上的 barebox 執行 **`rksecure`** 指令，給它這個雜湊，就會開啟 secure boot。
3. 因為 OTP 在 normal world 碰不到，**實際寫 OTP 的是 OP-TEE**（[▶ 08:58](https://youtu.be/PSEJD4Bfnyw?t=538)）：
   - barebox 端：跟 OP-TEE 溝通的使用者介面。
   - OP-TEE 端：一個 **PTA**（Pseudo Trusted Application，OP-TEE 內建的 TA）**RK secure PTA**，真正去開 secure boot。

特點：
- **生產時要跑 script**（[▶ 09:28](https://youtu.be/PSEJD4Bfnyw?t=568)）：開系統 → 確認 secure boot 還沒開 → 帶雜湊執行指令 → 從此只能跑簽過的東西。
- 優點：**可以精確決定在生產的哪一步開**，之前、之後做什麼都行。「這是你的責任。」
- **需要上游 OP-TEE**（有 RK secure PTA）。**Rockchip 提供的 OP-TEE 不行**（[▶ 10:01](https://youtu.be/PSEJD4Bfnyw?t=601)）。

**什麼情況會失敗或被繞過**（講者提到的）：
- 寫進 OTP 的雜湊被換掉 → secure boot 破了。所以寫入一定要在可控的環境。
- 雜湊算錯就燒 → 板子變磚（第 5 節）。

---

## 4. barebox 的完整步驟

[▶ 10:01](https://youtu.be/PSEJD4Bfnyw?t=601)（p.14，原文）

```
$ openssl genrsa -f 4 -out <key.pem> 4096          # 產生金鑰對（RSA）
$ make menuconfig                                  # 設定 build
    CONFIG_ARCH_ROCKCHIP_IMAGE_SIGN_KEY=<key.pem>
    CONFIG_CMD_RKSECURE=y
$ make <image>                                     # build image（同時簽好）
$ scripts/rk-otp.sh <image>                        # 算金鑰雜湊
> rksecure -x <hash> -b 4096 -l                    # 在裝置上寫入金鑰雜湊
```

- `rk-otp.sh` 可以給金鑰，也可以直接給 image，它會從 image 抽出公鑰再算雜湊（[▶ 10:32](https://youtu.be/PSEJD4Bfnyw?t=632)）。
- `rksecure` 在 barebox 裡跑，經 OP-TEE 寫入。
- `rksecure` 的參數 `-b 4096`、`-l` 講者沒解釋。

---

## 5. 建議與參考資料

### 5.1 建議

[▶ 10:32](https://youtu.be/PSEJD4Bfnyw?t=632)（p.15）

1. **簽章私鑰放 HSM。**「沒什麼好爭的。」
2. **燒之前檢查公鑰雜湊**，不然會變磚（[▶ 11:05](https://youtu.be/PSEJD4Bfnyw?t=665)）。
3. 所以**先在可以犧牲的硬體上測**。【口頭】桌上只有一台的話，他不會在那台上開 secure boot。
4. **開了之後，測試沒簽的 image、或用別把金鑰簽的 image 真的會被拒絕**，才能確定 secure boot 真的開了（[▶ 11:37](https://youtu.be/PSEJD4Bfnyw?t=697)）。

### 5.2 參考資料

[▶ 11:37](https://youtu.be/PSEJD4Bfnyw?t=697)（p.16）

| 資料 | 講者的說明 |
|---|---|
| `github.com/DualTachyon/rk3588-secure-boot` | 【口頭】做了大量逆向工程。「我對 RK3588 secure boot 的了解全部來自這個 repo」，他做的是把它整合進上游專案 |
| Rockchip Developer Guide Linux Secure Boot | 部分記錄早期 secure boot；也講 Rockchip 建議怎麼簽 Linux、rootfs，讓 secure boot 延續到 bootloader 之後（[▶ 12:08](https://youtu.be/PSEJD4Bfnyw?t=728)） |
| barebox 文件（`boards/rk35xx`） | 這場講的流程，有更細的步驟 |
| 上游 OP-TEE 的 `core/pta/rockchip` | RK secure PTA。最新的 OP-TEE 版本已經有 |

- 【口頭】**bootloader 之後的鏈（kernel、rootfs）他沒講**：一旦有了可信的 bootloader，之後怎麼延續可以自己決定（[▶ 12:38](https://youtu.be/PSEJD4Bfnyw?t=758)）。
- 【口頭】他只做了 barebox 版，沒有 U-Boot 版。想在 U-Boot 實作的人歡迎找他（[▶ 13:38](https://youtu.be/PSEJD4Bfnyw?t=818)）。

---

## 6. 一頁速查表

**RK3588 boot ROM 驗證**：讀 OTP 金鑰雜湊 → 比對 image 裡公鑰的雜湊 → 用公鑰驗簽章 → 用 header 雜湊驗 bootloader → 執行。OTP **只有 secure world（EL3）能存取**。

| | 原廠 | barebox |
|---|---|---|
| 金鑰 | `rk_sign_tool`（binary、有狀態、HSM 不確定） | OpenSSL＋PKCS#11 |
| 簽 image | `mkimage`＋`rk_sign_tool` | `rkimage`（build 時就簽） |
| 誰寫 OTP | U-Boot 早期開機（EL3），公鑰放 DT | barebox `rksecure` → 上游 OP-TEE 的 RK secure PTA |
| 生產 | 要另一個專用 image | 要 script；可選擇在哪一步開 |
| 執行時看得到狀態嗎 | 不行 | —（講者沒說） |
| 需要 | Rockchip 工具 | OP-TEE ≥ 4.9.0、barebox ≥ v2026.02.0（說明欄） |

**四條建議**：私鑰放 HSM｜燒前檢查雜湊｜先在可犧牲的板子上試｜開了之後測試沒簽的 image 會被拒絕。

---

## 7. 延伸連結

- MT8189 上的 BL2 eFuse（同樣是「ROM 用 OTP 裡的雜湊驗第一段」）：[`../verified-boot-notes/vb-intro.md`](../verified-boot-notes/vb-intro.md)
- OP-TEE PTA、secure world 才能碰的硬體：[`../tf-a-and-op-tee-note/optee-intro.md`](../tf-a-and-op-tee-note/optee-intro.md)、[`../tf-a-and-op-tee-note/secure-memory.md`](../tf-a-and-op-tee-note/secure-memory.md)

---

## 附：一句話總結

> **RK3588 的 boot ROM 用 OTP 裡的公鑰雜湊驗 bootloader，而 OTP 只有 secure world 碰得到。barebox 的做法是用 OpenSSL／`rkimage` 開源地簽 image，再用 `rksecure` 經上游 OP-TEE 的 PTA 寫入雜湊，完全不需要 Rockchip 的閉源工具。**

---

*筆記依據 Michael Tretter〈Open Source Tools for Secure Boot on Rockchip RK3588〉（Embedded Recipes 2026）錄影（Whisper `turbo` 轉錄，13:59）、Embedded Recipes 官方投影片與影片說明欄整理。*
