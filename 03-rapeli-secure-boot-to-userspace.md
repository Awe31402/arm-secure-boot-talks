---
talk: Secure boot all the way to userspace and upstream
speaker: Mikko Rapeli（Linaro）
conference: Yocto Project Summit 2024.12（線上）
year: 2024（2024-12-04）
video: https://youtu.be/mNC5suIlWAQ
slides: https://pretalx.com/media/yocto-project-summit-2024-12/submissions/WBCBYW/resources/_nHYKnkf.pdf
---

# Secure boot all the way to userspace and upstream [▶ 影片](https://youtu.be/mNC5suIlWAQ)

> **演講**：Mikko Rapeli（Linaro），Yocto Project Summit 2024.12（2024-12-04，線上，30 分鐘）
> **來源**：YouTube 錄影（31:22）用 Whisper `turbo` 轉成逐字稿，再加上 pretalx 上的官方投影片（29 頁）。
> **標記說明**：`【口頭】` 是投影片沒有的。`【投影片補充】` 是投影片有、講者沒講的。`⚠️ 逐字稿缺字` 是 Whisper 聽錯。`⚠️ 待確認` 是查不清楚的地方。
> 講者後半段時間不夠，跳過了好幾頁（第 9 節）。沒有 Q&A。

---

## 目錄

- [0. 這場演講要做什麼](#0-這場演講要做什麼)
- [1. 背景名詞：SystemReady、UEFI、secure boot、TPM、measured boot](#1-背景名詞systemreadyuefisecure-boottpmmeasured-boot)
- [2. Trusted Substrate（TS）：韌體這半邊](#2-trusted-substratets韌體這半邊)
- [3. TS 的缺口（做產品前一定要補）](#3-ts-的缺口做產品前一定要補)
- [4. TS 怎麼實作、上游到哪裡](#4-ts-怎麼實作上游到哪裡)
- [5. Trusted Reference Stack（TRS）：OS 這半邊](#5-trusted-reference-stacktrsos-這半邊)
- [6. 兩條鏈：secure boot 鏈與 TPM 量測鏈](#6-兩條鏈secure-boot-鏈與-tpm-量測鏈)
- [7. 在 Yocto 裡怎麼做：UKI、dm-verity /usr](#7-在-yocto-裡怎麼做ukidm-verity-usr)
- [8. 踩到的坑：fTPM、偵測 TPM、測試](#8-踩到的坑ftpm偵測-tpm測試)
- [9. 沒解決的問題：建置時的金鑰](#9-沒解決的問題建置時的金鑰)
- [10. 一頁速查表](#10-一頁速查表)
- [11. 延伸連結](#11-延伸連結)

---

## 0. 這場演講要做什麼

[▶ 00:36](https://youtu.be/mNC5suIlWAQ?t=36)（p.2–3）

兩個 Linaro 的專案，兩個合起來做出「secure boot 一路到 user space」：

| 專案 | 負責哪半邊 | 內容 |
|---|---|---|
| **Trusted Substrate（TS）** | 韌體 | 符合 Arm SystemReady 的 UEFI 韌體（U-Boot＋TF-A＋OP-TEE） |
| **Trusted Reference Stack（TRS）** | OS | kernel、initramfs、rootfs |

兩邊一起用 **UEFI Secure Boot**，再用 **TPM** 加密 rootfs。

投影片 p.3 列出整條鏈：
1. 硬體驗 UEFI 韌體。
2. UEFI 韌體驗 kernel＋initramfs，兩者合成一個 **UKI**（Unified Kernel Image）。
3. UKI 裡嵌著 **dm-verity 雜湊**，用來驗 rootfs。
4. TPM 量測 UEFI 韌體和所有開機相關軟體。
5. 第一次開機時，systemd 用 TPM 建一個**加密、可寫**的檔案系統，綁在這個安全、量測過的系統上。

講者也會談把這些**上游**到 oe-core/poky、meta-arm、meta-security/meta-tpm、meta-secure-core 的狀況，以及遇到的問題。

---

## 1. 背景名詞：SystemReady、UEFI、secure boot、TPM、measured boot

### 1.1 Arm SystemReady

[▶ 01:08](https://youtu.be/mNC5suIlWAQ?t=68)（p.4）

- 一個**相容性認證計畫**，確保 OS 能在 Arm 硬體上互通。
- 建在 UEFI 韌體標準上。
- 有多個 profile，給不同等級的裝置。**IR** 是給嵌入式的（[▶ 06:34](https://youtu.be/mNC5suIlWAQ?t=394)）。
- 好處：OS 不用改就能裝在新硬體上，不必為每塊板子做軟體、也不必重新產生 Linux 發行版。
- 【口頭】很適合韌體需求不嚴格的產品。對開機時間、安全有更嚴格要求的產品，也是很好的起點。

**伺服器和嵌入式 profile 的差別（影響 TPM 偵測，見 8.2）**：
- 投影片 p.4：**伺服器級硬體要求 ACPI**，嵌入式不用。
- 講者口頭說的是「server class hardware requirements **do not** dictate ACPI support」（[▶ 01:38](https://youtu.be/mNC5suIlWAQ?t=98)），跟投影片相反。
- 兩邊都記下來。⚠️ 待確認：從 8.2「IR 只要求 UEFI＋device tree、不要求 ACPI」來看，投影片的說法前後比較一致，講者可能是口誤。

### 1.2 UEFI

[▶ 02:12](https://youtu.be/mNC5suIlWAQ?t=132)（p.5）

- 韌體實作的標準。
- 提供介面讓使用者和廠商跑 script、跟韌體互動、載入並執行 binary（例如載入 OS 開機）。
- 【口頭】最大的重點之一是**探索那些用別的方法發現不了的硬體**。
- 支援 secure boot、TPM，也有標準方法匯入廠商的 secure boot 金鑰。
- 開源實作：**U-Boot** 和 **EDK2**。

### 1.3 Secure boot

[▶ 03:16](https://youtu.be/mNC5suIlWAQ?t=196)（p.6）

- 裝置的擁有者／維護者用來確保：**只有自己做、自己簽的軟體能在裝置上跑**。
- 軟體被改過一定要被偵測到，而且**跑被改過的軟體一定要失敗**。
- 通常用 secure boot 金鑰簽軟體，其中有些由硬體驗證。
- **secure boot 金鑰通常不是每台裝置一把**，而是整個產品線、甚至整個廠商共用一把。
- 通常有多層簽章，從硬體一路建到應用程式。

### 1.4 TPM（Trusted Platform Module）

[▶ 04:21](https://youtu.be/mNC5suIlWAQ?t=261)（p.7）

- 一個外加的硬體模組。它能安全地算 checksum、把 checksum 組合起來，結果叫 **PCR**（Platform Configuration Register）值，並且持久保存。
- **主 CPU 上的 OS 不能改 TPM 裡的資料，只能「追加」**到 PCR：拿舊值和新資料組合成新值。
  - 投影片和講者都把這個組合叫做 **XOR**。
  - ⚠️ 待確認：投影片原文就是 XOR，筆記照錄，沒有更正。
- 用途：
  - 依開機量測結果加密分區或資料。
  - 開機狀態在密碼學上不對時，擋住某些分區、資料、甚至網路服務。
- **TPM 的資料是每台裝置專屬的**（[▶ 05:32](https://youtu.be/mNC5suIlWAQ?t=332)）：裡面通常有一把裝置專屬的祕密金鑰，是所有操作的基礎。
- 沒有實體 TPM 時，可以用 **OP-TEE 的 fTPM**（firmware TPM，一個 trusted application）代替。

### 1.5 Measured boot

[▶ 06:03](https://youtu.be/mNC5suIlWAQ?t=363)（p.8）

- 每一段開機在執行下一段之前，先用 TPM 算下一段的 checksum，再追加進 PCR。
- 每一段都得到一個代表「目前開機狀態」的數位簽章。
- **必須完全一致**，才能解鎖裝置專屬的資料，例如某個分區。

**跟 secure boot 的差別**（講者在第 6 節說清楚）：
- secure boot 的金鑰是一整批裝置共用。
- measured boot 綁的是**每台裝置自己的 TPM**。

---

## 2. Trusted Substrate（TS）：韌體這半邊

[▶ 06:34](https://youtu.be/mNC5suIlWAQ?t=394)（p.9–11）

**支援的板子**（p.9）：

| 板子 | TPM |
|---|---|
| QEMU armv7、armv8 | swtpm（軟體 TPM） |
| AMD Kria KV260、zcu102 | 沒有 |
| Rock Pi 4B、Synquacer | 韌體裡的 OP-TEE fTPM |
| Raspberry Pi 4 | 沒有 |
| NXP i.MX8MP、Qualcomm RB1/2/3/5、AVA Developer Platform | p.9 沒寫 |

- 是 Linaro **LEDGE**（邊緣運算）小組做的，有贊助者。
- 有好幾塊板子用這套韌體通過了 SystemReady 認證。

**元件**（p.10；[▶ 07:36](https://youtu.be/mNC5suIlWAQ?t=456)）：
- **U-Boot**：用 poky master 最新版，加一些設定。
- **TF-A**：來自 meta-arm master。
- **OP-TEE**：要在韌體裡放 fTPM 時用，也來自 meta-arm。

**額外功能**（p.11；[▶ 08:09](https://youtu.be/mNC5suIlWAQ?t=489)）：
- **簽章過的 capsule 韌體更新**。【口頭】韌體也要能更新，更新沒簽章就是一個安全漏洞。
- U-Boot 的另一套 TCP/IP 堆疊 **lwIP**（已送上游），加上用 **MbedTLS** 的 TLS。所以 U-Boot／UEFI 能用 HTTP/HTTPS 下載，例如直接在開機時下載安裝 image（[▶ 08:44](https://youtu.be/mNC5suIlWAQ?t=524)）。
- Arm Trusted Services：可以代替 TPM，例如用 Parsec。
- **UEFI Secure Boot**：所有 binary 載入前都照 UEFI 標準方法驗證（[▶ 09:20](https://youtu.be/mNC5suIlWAQ?t=560)）。

---

## 3. TS 的缺口（做產品前一定要補）

[▶ 09:20](https://youtu.be/mNC5suIlWAQ?t=560)（p.12）

【口頭】TS 是**概念驗證**（proof of concept），不是在每方面都能直接當產品。缺口有：

1. **硬體沒有驗韌體**（[▶ 09:50](https://youtu.be/mNC5suIlWAQ?t=590)）：
   - 沒做「SoC ROM 驗 U-Boot binary」這一段。
   - 原因：每家 SoC 廠的工具都不一樣，而且會讓 CI 環境很難用。
   - 所以只用開放的硬體，**並讓硬體保持開放狀態**（方便測試）。
2. **私鑰放在公開的 git repo 裡**（[▶ 10:23](https://youtu.be/mNC5suIlWAQ?t=623)）：
   - 這樣當然很糟，但是為了測試。
   - 真正的產品要換成廠商自己的祕密金鑰重新 build。
   - 另一個選擇（p.12；[▶ 10:53](https://youtu.be/mNC5suIlWAQ?t=653)）：生產時加一個「硬體準備」步驟。用 SoC／韌體專屬的方法，或 **UEFI 標準方法**，把廠商金鑰複製進裝置，並設定裝置只接受這些金鑰。這樣金鑰就不必放在 build 裡。
3. **時間**：TLS 要驗憑證到期，所以裝置得大概知道現在幾點。【口頭】沒有電池 RTC 的板子會很麻煩。
4. **U-Boot、UEFI console 預設開著**（[▶ 11:25](https://youtu.be/mNC5suIlWAQ?t=685)）：
   - 為了在 Linaro LAVA CI 裡測試。
   - **它可以用來破壞 secure boot**，他們也真的這樣用。
   - 【口頭】他們故意亂改 TPM PCR 值，確認改了之後就**解不開加密的 rootfs**。
   - 產品設定一定要關掉。

---

## 4. TS 怎麼實作、上游到哪裡

### 4.1 meta-ts

[▶ 11:58](https://youtu.be/mNC5suIlWAQ?t=718)（p.13）

- 每塊板子一個 Yocto machine 設定。
- 用 **machine feature** 開功能：

| machine feature | 做什麼 |
|---|---|
| `secure-boot` | 用 build 環境裡的固定金鑰簽章，公鑰嵌進韌體 binary |
| `tpm2` | TPM measured boot |
| `optee` | OP-TEE |
| `capsule-update` | capsule 韌體更新 |
| `auth-capsule-update` | 簽章過的 capsule 更新 |

- 實作方式：在上游 defconfig（例如 U-Boot）上面**疊 config 片段**（[▶ 12:29](https://youtu.be/mNC5suIlWAQ?t=749)）。
- 【口頭】跟社群合作很密切，patch 一做好就送上游。layer 裡的 patch 至少都已經在 review 中。
- 另外有一些記憶體配置的 patch，跟韌體／硬體綁在一起，比較像設定，很難上游（[▶ 12:59](https://youtu.be/mNC5suIlWAQ?t=779)）。
- 輸出：一個給這塊板子燒錄用的韌體 binary，加一個 `.wic` image，裡面有空的 ESP（EFI System Partition）。

### 4.2 上游狀況

[▶ 14:00](https://youtu.be/mNC5suIlWAQ?t=840)（p.14–15）

- 很多板子找不到合適的上游 layer（Rock Pi 4B、Synquacer、AMD、RPi4）。
- 原因：TS 用的是上游 U-Boot、TF-A，但**廠商 BSP layer 常常 fork 舊版**，有些問題還沒修。poky／meta-arm 的預設值在那上面用不了。
- 反過來，【口頭】**廠商 BSP layer 通常能補上 TS 最大的缺口：硬體驗第一個韌體**（[▶ 14:34](https://youtu.be/mNC5suIlWAQ?t=874)）。
- QEMU 有上游：**meta-arm**（[▶ 15:08](https://youtu.be/mNC5suIlWAQ?t=908)）。
  - 2024 年秋天被接受：machine `qemuarm64-secureboot`。
  - build 時：
    1. 做出 U-Boot 韌體，UEFI 開 secure boot。
    2. 簽 kernel 和 **systemd-boot**（不是 grub）。
    3. 做出帶 ESP 的大 image。
    4. secure boot 金鑰在 build 時產生。
  - Linaro 的 Javier Tia 送的上游。
  - 指令（p.14 原文）：
    ```
    $ git clone https://git.yoctoproject.org/meta-arm
    $ cd meta-arm
    $ kas build ci/qemuarm64-secureboot.ym:ci/uefi-secureboot.yml:ci/testimage.yml
    ```
    （第一個檔名在投影片上就是 `.ym`。）

**`ci/uefi-secureboot.yml` 的重點**（p.15；[▶ 16:17](https://youtu.be/mNC5suIlWAQ?t=977)）：
- `SBSIGN_KEYS_DIR`：簽章金鑰放哪。
- runqemu 不要直接載 kernel（`QB_DEFAULT_KERNEL = "none"`）。要讓韌體自己從 ESP 載入（[▶ 16:51](https://youtu.be/mNC5suIlWAQ?t=1011)）。
- `WKS_FILE = "efi-disk.wks.in"`：決定 ESP 的配置。
- `MACHINE_FEATURES:append = " efi uefi-secureboot uefi-http-boot uefi-capsule-updates"`
- `EFI_PROVIDER = "systemd-boot"`、`INIT_MANAGER = "systemd"`

**為什麼用 systemd-boot、不用 grub**（p.15；[▶ 17:28](https://youtu.be/mNC5suIlWAQ?t=1048)）：
- grub 用 TPM 有問題。
- **grub 預設可以編輯開機項目，這基本上就是 secure boot 的漏洞**：kernel command line 可以決定載哪個 kernel、掛哪個分區、跑哪個 init。
- 【口頭】如果一直搭配 TPM 正確使用，問題也許沒那麼大，因為量測值還是會對。但他們覺得 systemd-boot 比較好處理。

**為什麼只測 systemd init**（p.15；[▶ 18:01](https://youtu.be/mNC5suIlWAQ?t=1081)）：
- systemd 已經支援加密分區和開機時的 PCR 量測。
- 用 sysvinit 或 script 的話，這些都要自己寫。

TODO（p.15）：TPM measured boot 的支援。【口頭】可能上游到 meta-security／meta-tpm。

---

## 5. Trusted Reference Stack（TRS）：OS 這半邊

[▶ 18:35](https://youtu.be/mNC5suIlWAQ?t=1115)（p.16）

- OS 這半邊。用 TS 韌體裡同一組金鑰簽 kernel 和 grub（後來改成 systemd-boot）。

**舊版實作的缺口**（p.16）：
- initrd 裡用 shell script：有開 secure boot 簽章時，把 ext4 轉成 TPM 加密的檔案系統。
- 用 grub 當開機選單，也支援 Xen dom0。
- **secure boot 沒有涵蓋 initrd 和主 rootfs。**
- 第一次開機後，measured boot 加 TPM 會加密整個 rootfs，但 **initrd 還是沒加密，ESP 也沒簽**。

**新版：全部改成 systemd，補上所有缺口**（p.16；[▶ 19:08](https://youtu.be/mNC5suIlWAQ?t=1148)）：
1. **UKI**：把 kernel、initrd、kernel command line、`/etc/os-release` 合成**一個**簽章過的 UEFI binary。
2. **rootfs 改成 dm-verity 的 `/usr` 分區**：build 時算出雜湊，放進 UKI 裡的 kernel command line。這樣 secure boot 就一路綁到 rootfs。
3. **initrd 改用 systemd**：第一次開機用 `systemd-repart` 建一個**可寫、用 TPM 加密**的分區。比重新加密整個 ext4 快很多。
- 【口頭】目的是像現在的 x86 筆電一樣，UEFI＋secure boot＋TPM 讓發行版都能正確運作。很多發行版都用 systemd（[▶ 19:38](https://youtu.be/mNC5suIlWAQ?t=1178)）。

---

## 6. 兩條鏈：secure boot 鏈與 TPM 量測鏈

### 6.1 UEFI Secure Boot 信任鏈

[▶ 19:38](https://youtu.be/mNC5suIlWAQ?t=1178)（p.17）

```
硬體 →(1) 韌體（UEFI） →(2) systemd-boot →(2) UKI（kernel、cmdline、initrd） →(3) dm-verity /usr
```

| 段 | 誰驗誰 | 靠什麼 |
|---|---|---|
| (1) | 硬體驗韌體 | **TS 沒做**：沒用廠商硬體金鑰簽，只用開放硬體 |
| (2) | UEFI 韌體驗 systemd-boot 和 UKI | 韌體裡設定的自訂金鑰，只載入簽過的 binary |
| (3) | UKI 驗 rootfs | dm-verity 雜湊在 build 時放進 UKI 裡的 kernel command line |

- 【口頭】**rootfs 不是用 secure boot 金鑰簽的**，而是用 dm-verity：它的雜湊唯一代表那個分區，放在已簽章的 command line 裡（[▶ 20:11](https://youtu.be/mNC5suIlWAQ?t=1211)）。
- **限制**（p.17）：(1)(2)(3) 都是一大批裝置共用的，甚至整個產品線共用，所以**不能拿來做每台裝置專屬的加密儲存**。這就是需要 TPM 的原因。

### 6.2 TPM PCR 量測鏈

[▶ 20:54](https://youtu.be/mNC5suIlWAQ?t=1254)（p.18）

```
0) TPM 裝置的祕密私鑰（每台不同）
硬體 →1 韌體 →2 systemd-boot →3 UKI →4 kernel UEFI stub →5 systemd initrd … →n TPM 保護的祕密，用來加密可寫 rootfs
```

- 從 0 到 n，**每一步都要照順序、沒有被改過**，才能解鎖 TPM 保護的加密 rootfs。
- 所有 PCR 量測都綁在每台裝置自己的 TPM 金鑰上（第 0 步）。
- 資料分區**只能**用同一顆 TPM、而且量測值完全一樣才能解開。

**PCR policy 可以放寬**（p.18；[▶ 21:27](https://youtu.be/mNC5suIlWAQ?t=1287)）：
- 有多個 PCR，各有指定用途。其中一個代表 UEFI secure boot 用的公鑰。
- 可以只綁「TPM 裝置金鑰＋UEFI 廠商簽章金鑰」。這樣更新韌體、UKI、rootfs 時，**不必換檔案系統加密金鑰**。
- p.18 附了 `systemd-repart`、`systemd-cryptenroll` 的文件連結。

### 6.3 對軟體更新的影響

[▶ 22:05](https://youtu.be/mNC5suIlWAQ?t=1325)（p.19）

- **更新的難處**（p.19）：UKI 和 dm-verity `/usr` 一變，量測值就變，但 rootfs 的 TPM 加密金鑰不應該跟著變。所以要選對 PCR policy。x86 UEFI 也有同樣問題，期待 systemd-boot、kernel、systemd 用對的 PCR 封裝金鑰。
- **A/B 更新變簡單了，也變麻煩了**：
  - **一個 UKI 只對應一個 dm-verity 分區**：它開機時只會掛那個 dm-verity 分區。
  - 換新的 dm-verity rootfs，就一定要有新的 UKI（因為 command line 變了）。
  - 只換 UKI，可以不換 rootfs。
  - systemd-boot 會列出所有找到的 UKI，用 `/etc/os-release` 的版本等資訊排序（p.19）。

---

## 7. 在 Yocto 裡怎麼做：UKI、dm-verity /usr

### 7.1 `uki.bbclass`

[▶ 22:39](https://youtu.be/mNC5suIlWAQ?t=1359)（p.20）

- 2024 年 10 月加進 poky 的 `meta/classes-recipe/uki.bbclass`，誰都能用。
- 範例：把 meta-arm 的 `qemuarm64-secureboot` 改成 UKI。p.20 的設定，在 p.15 的基礎上多了：
  ```
  TEST_SUITES:append = " uefi_secureboot uki"
  IMAGE_CLASSES:append:pn-core-image-base = " uki"
  INITRAMFS_IMAGE = "core-image-minimal-initramfs"
  IMAGE_CLASSES:append:pn-core-image-base = " sbsign"
  UKI_SB_KEY = "${SBSIGN_KEY}"
  UKI_SB_CERT = "${SBSIGN_CERT}"
  IMAGE_BOOT_FILES:remove = "Image"
  ```
- 【口頭】UKI 把 kernel、initramfs、command line 綁成一個 secure boot 簽章的 binary，所以**一定要另外 build 一個 initramfs**。這裡用 `core-image-minimal-initramfs`（[▶ 23:43](https://youtu.be/mNC5suIlWAQ?t=1423)）。
- 【口頭】`sbsign` class 是為了拿到金鑰。實際簽章由 systemd 的 UKI 工具做。

### 7.2 systemd initrd

[▶ 24:17](https://youtu.be/mNC5suIlWAQ?t=1457)（p.21）

- 【口頭】他們認為最好的做法是 **initramfs 裡就跑 systemd**。但 poky 和其他 image recipe 預設都不是這樣，所以要提供範例、送上游。
- 講者說要節省時間，跳過這頁的細節（[▶ 24:51](https://youtu.be/mNC5suIlWAQ?t=1491)）。

【投影片補充】p.21 寫了這些：
- initrd 要有 systemd、dm-verity 支援、TPM 設定。
- 有一個 `systemd-repart` 設定檔：建立 TPM 保護的 rootfs，並把 `/usr/etc` 等目錄複製過去。
- **systemd v256 把很多服務的條件從 `ConditionSecurity=tpm2` 改成 `ConditionSecurity=measured-uki`**。
  - `measured-uki` 要在裝置上用 `ukify.py` 產生帶 TPM 量測的 UKI 才行。
  - 交叉編譯環境可能沒有 TPM，build 時做不了量測。所以很多服務的條件只好降回「有 TPM 裝置就好」（`tpm2`）。
  - TODO：build 機器上也許能用軟體 TPM 產生簽章的 PCR policy，但 swtpm 可能需要整台 QEMU。

### 7.3 dm-verity `/usr`

[▶ 24:51](https://youtu.be/mNC5suIlWAQ?t=1491)（p.22）

- dm-verity 支援來自 **meta-security**，但他們的用法很難跟其他 image（特別是 wic image）合在一起。
- 原因：meta-security 的 dm-verity class **自己也會產生 wic 設定**，跟主 image 衝突（[▶ 25:21](https://youtu.be/mNC5suIlWAQ?t=1521)）。
- 所以拆成兩個 recipe：

| recipe | 做什麼 |
|---|---|
| `trs-verity.bb` | 產生 dm-verity `/usr` 分區（附一個產生的 `.wks`）；同時產生 UKI，把 dm-verity root hash 放進 kernel command line；也產生 initramfs |
| `trs-image.bb` | 把 `trs-verity` 的 `.wks` 包進來，產生最後的 `.wic`；ESP 裡放簽過的 systemd-boot 和 UKI |

- 計畫：以 meta-arm 的 `qemuarm64-secureboot` 為基礎，上游一份範例設定和 oeqa 測試。讓大家在 QEMU 上就能試「UEFI 韌體一路到 OS」的 secure boot。

---

## 8. 踩到的坑：fTPM、偵測 TPM、測試

### 8.1 韌體 TPM、tee-supplicant、RPMB

[▶ 25:55](https://youtu.be/mNC5suIlWAQ?t=1555)（p.23）

**問題**：
- Rock Pi 4B、Synquacer 只有 OP-TEE 的 **fTPM**。
- fTPM 要靠 **tee-supplicant**（OP-TEE 的 user space 元件）。
- tee-supplicant 又要提供 **RPMB**（Replay Protected Memory Block，防重播的安全儲存區）存取，給 fTPM 存資料。
- 結果 initramfs 裡**要在 systemd init 之前就啟動 tee-supplicant**，fTPM 才能用。
- 而且**停掉 tee-supplicant 會弄壞 TPM 型的 rootfs 加密**（p.23）。

**解法**（[▶ 26:26](https://youtu.be/mNC5suIlWAQ?t=1586)）：
- Linaro 的 Jens Wiklander 把 **RPMB 支援直接做進 kernel**，**kernel 6.12** 已合併。
- 從此 fTPM **不需要在 initramfs 跑 tee-supplicant**。
- p.23：meta-arm 的 optee-client 還有一點 udev rule、systemd service 的小修，上游 OP-TEE 已經有了。

### 8.2 怎麼偵測有沒有 TPM

[▶ 27:04](https://youtu.be/mNC5suIlWAQ?t=1624)（p.24）

- 【口頭】這是**最難解**的問題。
- 偵測一定要在 kernel 或 initrd、**掛主 rootfs 之前**做。

**systemd 目前的判斷**（兩種情況，任一成立就等 TPM）：
1. systemd 啟動時 TPM 裝置已經在了。表示 TPM driver 編進 kernel 而且正常（p.24：看得到 `/sys/kernel/security/tpm0/binary_bios_measurements`）。
2. 韌體提供了 **ACPI** 的 TPM 表（`/sys/firmware/acpi/tables/TPM2`）。

**會壞的情況**（[▶ 27:42](https://youtu.be/mNC5suIlWAQ?t=1662)）：
- TPM 驅動編成**模組**，systemd（udev）跑之前還沒載入。
- 裝置**沒有 ACPI**。例如 SystemReady **IR** 只要求 UEFI＋device tree。
- 【投影片補充】fTPM：driver 要等 user space 的 tee-supplicant，而這必須在 systemd init 之前。

**提議的解法**（[▶ 28:16](https://youtu.be/mNC5suIlWAQ?t=1696)；還沒合併）：
- 韌體有 TPM 時，會把 TPM 的事件記錄（event log）交給 kernel 的 UEFI stub。
- 但目前 user space 看不到。
- 如果 kernel 把它匯出到 sysfs，systemd 就能拿它當「有 TPM」的證據，排入 `tpm.target`（v256 新增）。
- 然後讓 udev 載 TPM driver，或先啟動 tee-supplicant 之類的服務。
- p.24 附了 kernel 和 systemd 的 draft patch 連結。

### 8.3 分區自動偵測（講者跳過）

[▶ 28:50](https://youtu.be/mNC5suIlWAQ?t=1730)（p.25）

- 講者說「也許跳過」，只帶過一句：用標準的 **GUID**，systemd 就能自動認出 rootfs、dm-verity rootfs、dm-verity `/usr` 分區。
- 投影片 p.25 還有：Discoverable Partitions Specification、`systemd-gpt-auto-generator`、`systemd-repart` 用標準 GUID 建分區、**dm-verity 分區用 verity 雜湊找，放哪都可以**。這讓帶 systemd initrd 的 UKI 可以跨裝置通用。演講中沒講。

### 8.4 測試

[▶ 29:21](https://youtu.be/mNC5suIlWAQ?t=1761)（p.26）

- x86 和 arm64 host 上測試都不容易。KVM 或某處有 bug，讓 `uki.bbclass` 上游跑了好幾輪。
- 【口頭】Richard 不厭其煩地一直幫忙跑測試，最後才弄好。
- p.26 細節：
  - x86 上的 OVMF（EDK2）沒辦法開 secure boot。
  - arm64 build host 上 QEMU 加 U-Boot 韌體開不了機。
  - 最後在**沒有 KVM** 的情況下測試才成功。
- **怪現象**（[▶ 29:52](https://youtu.be/mNC5suIlWAQ?t=1792)）：有時候 rootfs 突然變空的。
  - 原因：`testimage.bbclass` 裡的 `bb.fatal()` 沒清理就結束，又多 build 了一次 image，用到過時的 rootfs 資料。開了 `rm_work` 時，那個目錄是空的。
  - 修法：改成 `bb.error()`（p.26 附 commit 連結）。
- p.26：meta-security 現在 master 上很多測試都是壞的，加新測試前要先修好。
- 【口頭】上游時常常撞到完全意想不到的問題變成阻礙，開發者會掉進各種兔子洞。

---

## 9. 沒解決的問題：建置時的金鑰

[▶ 30:27](https://youtu.be/mNC5suIlWAQ?t=1827)（p.27）

**問題**：Yocto／bitbake build 時，金鑰和祕密要怎麼處理？

p.27 列的考量：
- 不是每個 build 環境都能信任，金鑰存取要受限。
- 用 **HSM**（Hardware Security Module）？要真的硬體。開發時可以用軟體 HSM API。
- 把簽章做成**完全獨立的步驟**？那公鑰要怎麼嵌進 build 出來的 binary？
- 換金鑰應該觸發重新 build？只有透過 `SRC_URI` 才辦得到。
- 用**環境變數**傳金鑰，可能不會正確觸發重新 build，可能造成奇怪的 **sstate 污染**和詭異的執行期行為。
- 現有範例：meta-secure-core 的 UEFI 金鑰和工具、meta-arm 的 secure boot 金鑰、poky 的 FIT image。
- 相關問題：故意不可重現的 build（例如 build 時隨機產生、嵌進 binary 的金鑰）要怎麼處理？

【口頭】meta-secure-core、meta-arm 現在基本上都是**用環境變數把金鑰硬塞進 build**，這對 build 的可重現性不好。講者希望有人能解決並寫好文件。

**結語**（p.28；[▶ 30:57](https://youtu.be/mNC5suIlWAQ?t=1857)）：希望 2025 年能有一個上游維護的 Yocto layer，端到端做到 secure boot 一路到 user space，加上 TPM 保護的安全儲存。

---

## 10. 一頁速查表

**兩條鏈各管什麼**

| | Secure boot 鏈 | TPM 量測鏈 |
|---|---|---|
| 證明什麼 | 只跑我簽的軟體 | 這台裝置照這個順序開了這些軟體 |
| 金鑰 | 整個產品線共用 | 每台 TPM 專屬 |
| 失敗時 | 不執行 | 解不開加密分區 |
| rootfs 怎麼涵蓋 | dm-verity root hash 放在簽章 UKI 的 cmdline | PCR 量測一路到 initrd，`systemd-repart` 用 TPM 加密可寫分區 |

**TS／TRS 的洞與補法**

| 洞 | 補法 |
|---|---|
| 硬體沒驗韌體（TS） | 要靠廠商 BSP、SoC 專屬工具 |
| 測試用私鑰在公開 repo | 換廠商金鑰重 build，或生產時用 UEFI 標準方法寫入金鑰 |
| U-Boot／UEFI console 開著 | 產品設定要關 |
| grub 可編輯開機項目 | 改用 systemd-boot |
| 舊 TRS：initrd、rootfs 沒涵蓋 | UKI＋dm-verity `/usr`＋systemd initrd |
| fTPM 要 tee-supplicant 先跑 | kernel 6.12 內建 RPMB |
| 沒 ACPI 時偵測不到 TPM | 提議：kernel 匯出 UEFI TPM event log |

---

## 11. 延伸連結

- MT8189 上的 dm-verity、內建 initramfs：[`../verified-boot-notes/verity-boot.md`](../verified-boot-notes/verity-boot.md)
- MT8189 上的 LUKS2 資料分區（跟本場 TPM 加密的對照）：[`../verified-boot-notes/dm-crypt.md`](../verified-boot-notes/dm-crypt.md)
- OP-TEE（fTPM、tee-supplicant 的背景）：[`../tf-a-and-op-tee-note/optee-intro.md`](../tf-a-and-op-tee-note/optee-intro.md)

---

## 附：一句話總結

> **Secure boot 用共用金鑰把「硬體 → UEFI → systemd-boot → UKI → dm-verity /usr」串起來，TPM measured boot 用每台專屬的金鑰把同一條路量起來，拿來加密可寫 rootfs。Linaro 把它做到 meta-arm 的 QEMU 上，但「硬體驗韌體」和「build 時怎麼管金鑰」都還沒解決。**

---

## ⚠️ 待確認清單

1. [▶ 01:38](https://youtu.be/mNC5suIlWAQ?t=98) 伺服器 profile 要不要 ACPI：p.4 說要，講者口頭說不要。
2. [▶ 04:21](https://youtu.be/mNC5suIlWAQ?t=261) PCR 的「組合」：投影片和講者都說是 XOR，照錄沒有更正。

---

*筆記依據 Mikko Rapeli〈Secure boot all the way to userspace and upstream〉（Yocto Project Summit 2024.12）錄影（Whisper `turbo` 轉錄，31:22）與 pretalx 官方投影片整理。*
