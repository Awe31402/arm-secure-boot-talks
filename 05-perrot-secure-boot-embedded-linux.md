---
talk: Secure boot in embedded Linux systems
speaker: Thomas Perrot（Bootlin）
conference: Live Embedded Event（LEE）
year: 2021（投影片封面：2021-06-03）
video: https://youtu.be/fBDNqvNLxMk
slides: https://bootlin.com/pub/conferences/2021/lee/perrot-secure-boot/perrot-secure-boot.pdf
---

# Secure boot in embedded Linux systems [▶ 影片](https://youtu.be/fBDNqvNLxMk)

> **演講**：Thomas Perrot（Bootlin），Live Embedded Event 2021（投影片封面寫 2021-06-03；Bootlin 頻道 2021-06-18 上傳）
> **來源**：YouTube 錄影（21:47）用 Whisper `turbo` 轉成逐字稿，再加上 Bootlin 官方投影片（26 頁）。
> **標記說明**：`【口頭】` 是講者口頭講、投影片沒有的。`【投影片補充】` 是投影片有、講者沒唸出來的。`⚠️ 逐字稿缺字` 是 Whisper 聽錯，靠投影片修正。`⚠️ 待確認` 是查不清楚的地方。`[▶ mm:ss]` 是影片時間點。

---

## 目錄

- [0. 這場演講要做什麼](#0-這場演講要做什麼)
- [1. Secure boot 在防什麼](#1-secure-boot-在防什麼)
- [2. 信任鏈與非對稱簽章](#2-信任鏈與非對稱簽章)
- [3. 開 secure boot 對工作流程的影響](#3-開-secure-boot-對工作流程的影響)
- [4. i.MX8 實作全貌：每段誰驗誰](#4-imx8-實作全貌每段誰驗誰)
- [5. ROM 驗 bootloader：NXP AHAB](#5-rom-驗-bootloadernxp-ahab)
  - [5.1 AHAB 和舊的 HAB 差在哪](#51-ahab-和舊的-hab-差在哪)
  - [5.2 產生 PKI tree、SRK table、SRK hash](#52-產生-pki-treesrk-tablesrk-hash)
  - [5.3 寫 CST 設定檔、簽 flash.bin](#53-寫-cst-設定檔簽-flashbin)
  - [5.4 燒 OTP、看狀態、鎖板](#54-燒-otp看狀態鎖板)
- [6. U-Boot 驗 kernel：FIT verified boot](#6-u-boot-驗-kernelfit-verified-boot)
  - [6.1 FIT 是容器](#61-fit-是容器)
  - [6.2 簽 image 還是簽 configuration](#62-簽-image-還是簽-configuration)
  - [6.3 產生金鑰、建置、把公鑰放進 U-Boot](#63-產生金鑰建置把公鑰放進-u-boot)
- [7. Kernel 驗 rootfs：dm-verity](#7-kernel-驗-rootfsdm-verity)
- [8. 不用 initramfs：dm-init＋FIT 裡的 boot script](#8-不用-initramfsdm-initfit-裡的-boot-script)
- [9. 一頁速查表](#9-一頁速查表)
- [10. 延伸連結](#10-延伸連結)

---

## 0. 這場演講要做什麼

[▶ 00:34](https://youtu.be/fBDNqvNLxMk?t=34) 講者把演講分成兩部分：

| 部分 | 內容 | 投影片 |
|---|---|---|
| 一、觀念 | secure boot 是什麼、簽章流程、對工作流程的影響 | p.4–8 |
| 二、實例 | 一塊 **i.MX8** 板子的完整 secure boot，**不需要 initramfs** | p.9–25 |

實例的信任鏈分四段（第 4 節）：ROM → bootloader → kernel → rootfs。

> ⚠️ 逐字稿缺字：[▶ 01:07](https://youtu.be/fBDNqvNLxMk?t=67) 的「initial MFS」應為「initramfs」。對照：[▶ 19:36](https://youtu.be/fBDNqvNLxMk?t=1176) 講者說「we don't need to use an initramfs」。

---

## 1. Secure boot 在防什麼

[▶ 01:07](https://youtu.be/fBDNqvNLxMk?t=67)（p.5）

Secure boot 在開機時檢查用到的每一段（硬體加軟體）。目的有三個：

- **保護系統**：防劫持（hijacking）。
- **保護使用者**：防篡改（tampering）、防硬體故障、防惡意程式執行。
- 【口頭】**廠商自己的需求**：讓廠商達成法規和商業目標。

投影片 p.5 的列法稍有不同：開機時檢查系統完整性；防 hijack、tampering、未授權軟體、惡意程式執行。

---

## 2. 信任鏈與非對稱簽章

### 信任鏈（Chain of Trust）

[▶ 01:42](https://youtu.be/fBDNqvNLxMk?t=102)（p.6）

Secure boot 的另一個名字就是**信任鏈**。核心規則：

- **建置時**：
  1. 每一段都被簽章。
  2. 每一段裡面放著「**下一段**的公鑰」。
- **開機時**：每一段先驗下一段的簽章，再執行它。
- **驗證失敗**：下一段**不會被載入**（p.6「Next stage isn't loaded when the authentication fails」）。

> ⚠️ 逐字稿缺字：[▶ 02:19](https://youtu.be/fBDNqvNLxMk?t=139) 「the main functionality of this feature is Hat Boot」意思不通。原字查不出來。從上下文看，講的是「每一段驗下一段」這個主要功能。

### 非對稱簽章（asymmetric signature）

[▶ 02:49](https://youtu.be/fBDNqvNLxMk?t=169)（p.7）

| 金鑰 | 誰拿 | 用途 | 規則 |
|---|---|---|---|
| 私鑰（private key） | 發布者（建置端） | 建置時簽章 | 一定要保密、不能公開 |
| 公鑰（public key） | 接收者（裝置） | 開機時驗章 | 可以公開 |

流程：

1. 發布者把資料做雜湊，得到摘要（digest）。
2. 用私鑰對摘要簽章。
3. 資料、簽章、公鑰一起給接收者。
4. 接收者自己算一次摘要，再用公鑰確認簽章對得上。

---

## 3. 開 secure boot 對工作流程的影響

[▶ 04:05](https://youtu.be/fBDNqvNLxMk?t=245)（p.8）

投影片只列了四個詞：Keys management、Manufactory、Upgrade、boot time。講者口頭逐項解釋：

- 【口頭】**金鑰管理**：特別是要能保護私鑰。
- 【口頭】**生產**：要在生產線上把裝置鎖起來。
- 【口頭】**升級**：升級用的 image 要帶簽章和公鑰。
- 【口頭】**開機變慢**：多了加密運算，要接受開機時間變長。

---

## 4. i.MX8 實作全貌：每段誰驗誰

[▶ 04:43](https://youtu.be/fBDNqvNLxMk?t=283)（p.10）

【口頭】Secure boot 有很多種做法，要看需求。這個案子照開機流程分四段：

| 段 | 誰驗 | 驗誰 | 用什麼 | 公鑰／雜湊放哪 |
|---|---|---|---|---|
| 1 | ROM code | bootloader（SPL、ATF、U-Boot…） | NXP **AHAB** | SRK hash 燒在 OTP fuse |
| 2 | U-Boot | kernel、DTB、boot script | U-Boot **verified boot**（FIT 簽章） | 公鑰編進 U-Boot 的 DTB |
| 3 | kernel | rootfs | **dm-verity** | root hash 放在 boot script（在已簽章的 FIT 裡） |
| 4 | — | 不用 initramfs | **dm-init**＋boot script | — |

為什麼這樣選：

- 【口頭】**bootloader 那段只有一個選擇**：要看晶片廠有提供什麼。NXP 提供的是 AHAB。
- 【口頭】**rootfs 選 dm-verity**：因為它簡單，而且可以用硬體加速（hardware offloading）。

---

## 5. ROM 驗 bootloader：NXP AHAB

### 5.1 AHAB 和舊的 HAB 差在哪

[▶ 05:53](https://youtu.be/fBDNqvNLxMk?t=353)（p.11–12）

**名詞**：
- **AHAB**（Advanced High Assurance Boot）是 i.MX8 系列 ROM 的 secure boot。
- 舊款 i.MX（例如 i.MX6）用的是 **HAB**（High Assurance Boot）。
- 【口頭】AHAB 比舊的 HAB 複雜。

**跟 HAB 一樣的地方**（p.11）：

- 用非對稱金鑰（PKI tree）。
- 用 OTP（One-Time Programmable）fuse 存公鑰的雜湊（**SRK**，Super Root Key）。
- Bootloader 各段用 NXP 的 **CST**（Code Signing Tool）在建置時打包成一個簽好的 image。
- 可以在 U-Boot 查 secure boot 狀態。

**跟 HAB 不一樣的地方**：

1. 多了一顆**安全控制器**來做驗證。投影片叫 SECO（Security Controller），經由 SCU（System Controller Unit）的 ROM 操作。
2. 也能啟動給另一顆處理器跑的程式。投影片 p.12 列出 **M4** image。
   > ⚠️ 逐字稿缺字：[▶ 07:07](https://youtu.be/fBDNqvNLxMk?t=427) 「a binary for a SP processor」。依 p.12 應該是 M4 核心，但不能確定講者原話。⚠️ 待確認
3. Image 分成**兩個 container**（[▶ 07:40](https://youtu.be/fBDNqvNLxMk?t=460)）：

| Container | 內容 | 用誰的金鑰簽 |
|---|---|---|
| 第一個 | SECO firmware | **NXP** 的金鑰 |
| 第二個 | SPL、ATF、U-Boot（加上相關簽章） | **OEM**（產品廠商）的金鑰 |

> ⚠️ 逐字稿缺字：「harm tested firmware」＝Arm Trusted Firmware；「hohohem keys」＝OEM keys。

**投影片和口頭不完全一樣**：
- p.12 寫第二個 container 是「SCFW、SPL、M4 image」用 OEM 簽，「U-Boot 和 ATF 由 SPL 載入」。
- 講者口頭說的是「SPL、ATF、U-Boot」。
- 兩邊都記下來。⚠️ 待確認

**開機時的驗證流程**（[▶ 08:19](https://youtu.be/fBDNqvNLxMk?t=499)）：

1. SCU 先載入安全控制器的 firmware（SECO FW）。
2. 再一段一段載入其他 bootloader 段。
3. **每載入一段，安全控制器就驗一次。**
4. 全部載入、全部驗過之後，才**輪流執行**。

> ⚠️ 逐字稿缺字：「signature controller firmware」應為 security controller firmware（SECO FW）。

### 5.2 產生 PKI tree、SRK table、SRK hash

[▶ 09:05](https://youtu.be/fBDNqvNLxMk?t=545)（p.13–14）

**在解什麼**：
- ROM 需要一組「根公鑰」，才知道要信任誰。
- 公鑰太大，OTP 放不下。
- 所以：把 4 把 SRK 公鑰做成一張表（SRK table），再算表的雜湊（SRK hash）。**燒進 OTP 的是 hash。**

**步驟**（指令照投影片原文）：

1. 設定憑證 ID、私鑰的密碼（p.13）：
   ```
   echo 00000001 > serial
   echo -e "mypassphrase\nmypassphrase" > key_pass.txt
   ```
2. 跑 NXP 腳本產生 PKI tree（p.13）。互動問答裡選：ECC、`p384`、`sha384`、有效期 10 年、SRK 憑證不設 CA flag。
   ```
   ./ahab_pki_tree.sh
   ```
   - 【口頭】選橢圓曲線（ECC），是因為 **i.MX8 的 B0 版晶片有限制**。
3. 產生 SRK table 和要燒進 fuse 的 hash（p.14）：
   ```
   ../linux64/bin/srktool -a -s sha384 -t SRK_1_2_3_4_table.bin \
     -e SRK_1_2_3_4_fuse.bin -f 1 -c \
     SRK1_sha384_secp384r1_v3_usr_crt.pem,SRK2_...,SRK3_...,SRK4_...
   ```
4. **燒之前先自己核對**（p.14）。【口頭】目的是確定等一下燒進去的值是對的：
   ```
   od -t x4 --endian=big SRK_1_2_3_4_fuse.bin
   sha512sum SRK_1_2_3_4_table.bin
   ```
   > ⚠️ 逐字稿缺字：[▶ 09:42](https://youtu.be/fBDNqvNLxMk?t=582) 「the hodi command」＝`od` 指令（依 p.14）。

**什麼情況會失敗**：
- 講者只說「先核對，確定燒進去的值是對的」。
- 以下**不是逐字稿內容**，是依「OTP 只能寫一次」推論的：如果燒錯，這塊板子的 SRK hash 就永遠對不上任何簽章。之後只要鎖板（5.4），就開不了機。

### 5.3 寫 CST 設定檔、簽 flash.bin

[▶ 10:14](https://youtu.be/fBDNqvNLxMk?t=614)（p.15）

**在解什麼**：把 bootloader image（`mkimage` 做出的 `flash.bin`）用 OEM 私鑰簽好，簽章放進 container 的 signature block。

**步驟**：有了金鑰、SRK table、bootloader image 之後，寫一個給 CST 的小設定檔，再用 CST 產生簽好的 image。p.15 的設定檔：

```
[Header]
Target = AHAB
Version = 1.0
[Install SRK]
File = "crts/SRK_1_2_3_4_table.bin"
Source = "crts/SRK1_sha384_secp384r1_v3_usr_crt.pem"
Source index = 0
Source set = OEM
Revocations = 0x0
[Authenticate Data]
File = "flash.bin.nosigned"
Offsets = 0x400  0x590
```

設定檔指定了四樣東西：

| 欄位 | 意思 |
|---|---|
| `File`（Install SRK） | SRK table |
| `Source` / `Source index` | 這次用表裡第幾把 SRK（0～3）簽 |
| `Revocations` | 撤銷哪幾把 SRK 的 bitmask。p.15 是 `0x0`，沒撤銷 |
| `File`（Authenticate Data） | 要簽的 image |
| `Offsets` | container header 和 signature block 的位置 |

- 【口頭】`Offsets` 要看目標晶片，可以在 datasheet 查到。p.15 的註解寫的是「`mkimage` 會印出來」。

**什麼情況會失敗或被繞過**：
- 【口頭】**簽好的 bootloader 在 fuse 燒好之前不會被驗**（[▶ 10:57](https://youtu.be/fBDNqvNLxMk?t=657)）。
- 也就是說，沒燒 SRK hash 的板子，簽了也等於沒保護。

### 5.4 燒 OTP、看狀態、鎖板

[▶ 11:34](https://youtu.be/fBDNqvNLxMk?t=694)（p.16–17）

**步驟**：

1. **在 U-Boot 燒 SRK hash，再讀回來核對**（p.16）。共 16 個 32-bit word，fuse bank 0 的 word 730～745：
   ```
   => fuse prog 0 730 0xbef4d897
   ...（到 745）
   => fuse read 0 730
   ```
2. **燒之前、燒之後都看一次 secure boot 狀態**（p.17）：
   ```
   => ahab_status
   Lifecycle: 0x0020, NXP closed
   No SECO Events Found!
   ```
3. **驗證有問題時**，安全控制器會留下 event（p.17）：
   ```
   SECO Event[0] = 0x0087EE00
   CMD = AHAB_AUTH_CONTAINER_REQ (0x87)
   IND = AHAB_NO_AUTHENTICATION_IND (0xEE)
   ```
   - 【口頭】event code 對應一種錯誤類型。
   - 【口頭】event 是以 container 為單位產生的。
4. **沒有任何 event，才鎖板**（p.17）：
   ```
   => ahab_close
   => reset
   => ahab_status
   Lifecycle: 0x0080, OEM closed
   ```
   【口頭】`ahab_close` 會**再燒一個 fuse**，從此不能執行沒簽章的 bootloader。

**什麼情況會失敗或被繞過**：
- **鎖板前**（lifecycle 是 `NXP closed`）：驗證失敗只會留 event，**板子照樣開機**。這正是用來除錯的狀態。
- **鎖板後**（`OEM closed`）：只能跑簽過的 bootloader。
- 所以順序一定是：簽好 → 燒 hash → 確認沒 event → 才 `ahab_close`。
- 以下**不是逐字稿內容**，是依投影片推論的：「鎖板前會照樣開機」這點，是從「有 event 還能進 U-Boot 下 `ahab_status`」推出來的。

> 投影片和口頭的指令名稱不一樣：
> - 講者口頭說「hab status」「HAB close」。
> - 投影片 p.17 寫的是 `ahab_status`、`ahab_close`；p.11 又寫「可以用 `hab_status` 查」。
> - 原文照列。⚠️ 待確認：i.MX8 的 U-Boot 指令實際是哪一個。

---

## 6. U-Boot 驗 kernel：FIT verified boot

### 6.1 FIT 是容器

[▶ 12:56](https://youtu.be/fBDNqvNLxMk?t=776)（p.18–19）

**FIT** image 是一個容器。內容寫在 image source file（`.its`）裡，基本上就是一串節點（node），每個節點描述一個元素。

裡面有兩種節點：

- **images**：kernel、DTB、DT overlay、boot script、FPGA bitstream……
- **configurations**：images 的組合。

講者的例子（p.19）：
- 1 個 kernel、1 個 DTB、1 個 boot script。
- 1 個 configuration `conf@1` 把三個組在一起。
- 每個 image 都有 `hash@1`（sha256）。

### 6.2 簽 image 還是簽 configuration

[▶ 15:21](https://youtu.be/fBDNqvNLxMk?t=921)（p.20）

**在解什麼**：U-Boot 要確定 kernel、DTB、script 都是你簽過的，而且是你**原本想要的那個組合**。

重點：

- p.20：**FIT 不是整個檔案一起簽的**（「Isn't globally signed」）。
- 有兩種簽法：
  1. 每個 image 各簽一個：每個 image 節點加一個 `signature` 節點。
  2. **簽 configuration**：在 configuration 節點加 `signature` 節點。
- 講者的例子用第 2 種（p.20）：
  ```
  signature@1 {
      algo = "sha256,rsa4096";
      key-name-hint = "kernel-dev";
      sign-images = "kernel", "fdt", "bootscr";
  };
  ```

**什麼情況會被繞過**：

- **簽 configuration 可以防 mix-and-match 攻擊**（p.20；[▶ 15:59](https://youtu.be/fBDNqvNLxMk?t=959)）。
- **mix-and-match 攻擊**：每個 image 單獨看都是合法簽過的，但攻擊者把它們重新組合。例如舊 kernel 配新 DTB，組出一個你從沒打算出貨的組合。
- 講者只說到「簽 configuration 可以防它」，沒有展開攻擊細節。

> ⚠️ 逐字稿缺字：「send a fit image」「mix and max attack」＝sign a FIT image、mix-and-match attack（依 p.20）。

### 6.3 產生金鑰、建置、把公鑰放進 U-Boot

[▶ 13:36](https://youtu.be/fBDNqvNLxMk?t=816)、[▶ 16:39](https://youtu.be/fBDNqvNLxMk?t=999)（p.21–22）

**金鑰放哪**：
- 私鑰：建置時拿來簽 kernel image。
- 公鑰：存進 **U-Boot binary**。

**產生金鑰和憑證**（p.21）：
```
openssl genpkey -algorithm RSA -out kernel-dev.key -pkeyopt rsa_keygen_bits:4096
openssl req -new -x509 -key kernel-dev.key -out kernel-dev.crt
openssl rsa -pubout -in kernel-dev.key -out kernel-dev.pem
```

**建置**（p.22）：
```
dtc u-boot_pubkey.dts -O dtb -o u-boot_pubkey.dtb
make CROSS_COMPILE=arm-linux-gnueabihf- foo_defconfig
make CROSS_COMPILE=arm-linux-gnueabihf- tools
tools/mkimage -f fitImage.its -K u-boot_pubkey.dtb -k /path/to/keys -r fitImage
make CROSS_COMPILE=arm-linux-gnueabihf- EXT_DTB=u-boot_pubkey.dtb
```

【口頭】講者說「透過 `dtc` 和 `mkimage`，分三步」（[▶ 14:06](https://youtu.be/fBDNqvNLxMk?t=846)）：

1. 建出還沒簽的 kernel image。
2. 建出簽好的 kernel image。
3. 把公鑰放進 U-Boot。

投影片 p.22 的指令順序是另一種切法：
1. 用 `dtc` 做一個放公鑰的 DTB。
2. `mkimage -K … -k … -r` 簽 FIT，同時把公鑰寫進那個 DTB。
3. 用 `EXT_DTB=` 重編 U-Boot。

兩邊都記下來。p.22 沒有一條獨立的「建未簽 image」指令。

---

## 7. Kernel 驗 rootfs：dm-verity

[▶ 17:10](https://youtu.be/fBDNqvNLxMk?t=1030)（p.23–24）

**在解什麼**：rootfs 太大，不可能開機時整個驗一遍。要改成「讀到哪一塊，驗哪一塊」。

**機制**（p.23；[▶ 17:51](https://youtu.be/fBDNqvNLxMk?t=1071)）：

- dm-verity 是 device mapper 上的一層虛擬層。
- 它用**雜湊樹**（hash tree，又叫 Merkle tree）：每個葉節點是 rootfs 一個 block 的雜湊，往上一層層再做雜湊，最上面是 **root hash**。
- **只在讀到那個 block 時才算雜湊、才比對。**
- 限制：
  - 只能用在 block device 上（【口頭】例如 squashfs）。
  - **只能唯讀。**
- 雜湊樹放哪：
  - 預設放在另一個 block device（hash device）。
  - 也可以接在資料 device 的後面，同一個 device。
- Kernel 5.4 起，root hash 可以簽章（p.23）。【口頭】簽的公鑰放在 kernel keyring。

**步驟**（p.24，指令照原文）：

1. 建雜湊樹。例子把雜湊樹接在 image 尾巴，所以要用 `--hash-offset` 指出資料在哪裡結束：
   ```
   veritysetup format verify --hash-offset=${OFFSET} image.squashfs image.squashfs
   ```
   輸出的 `Root hash`、`Salt`、`Data blocks` 之後都要用到。
2. 驗證：
   ```
   veritysetup verify --hash-offset=${OFFSET} image.squashfs image.squashfs ${HASH_ALG}
   ```
3. 打開：
   ```
   veritysetup open --hash-offset=${OFFSET} image.squashfs foo image.squashfs ${KEY} ${SALT}
   ```

> ⚠️ 待確認：
> - p.24 的 `verify`、`open` 最後的參數寫成 `${HASH_ALG}`、`${KEY} ${SALT}`。照 `veritysetup` 的用法，這裡應該放 root hash。投影片原文照列，沒有更正。
> - [▶ 19:00](https://youtu.be/fBDNqvNLxMk?t=1140) 講者說「the integrity can be checked with you knowing the root hash, but it is necessary to want it」，聽不清楚。比較可能是「驗證要知道 root hash」。

**什麼情況會被繞過**：
- 講者說，這個例子**沒有簽 root hash**。
- Root hash 的保護來自下一節：它寫在 boot script 裡，boot script 又在**簽過的 FIT** 裡。
- 以下**不是逐字稿內容**，是推論：所以 rootfs 的安全，完全靠 FIT 簽章那一段（第 6 節）。

---

## 8. 不用 initramfs：dm-init＋FIT 裡的 boot script

[▶ 19:36](https://youtu.be/fBDNqvNLxMk?t=1176)（p.25）

**在解什麼**：
- 案子的需求是**不用 initramfs** 來準備 rootfs。
- 平常要在 initramfs 裡跑 `veritysetup`，才能把 dm-verity device 開起來。

**做法**：

1. **dm-init**：kernel 直接從 kernel command line 的 `dm-mod.create=` 參數，在早期建好 dm-verity device，再掛成 root（p.25）：
   ```
   dm-mod.create="rootfs,,0,ro,0 905880 verity 1 /dev/mmcblk0p2 /dev/mmcblk0p2 4096 4096 113235 113236 sha256 <root hash> <salt>"
   ```
2. **Boot script 放在 FIT 裡**：
   - U-Boot 在「載入 kernel」和「啟動 kernel」兩個指令之間執行它（[▶ 20:11](https://youtu.be/fBDNqvNLxMk?t=1211)）。
   - p.25：`source ${fitimage_loadaddr}:bootscr@1`。
3. **Boot script 的工作**：把 dm-init 需要的參數（sectors、data blocks、hash 起點、block size、雜湊演算法、salt、**root hash**）設成變數，再接到 `bootargs`（p.25）：
   ```
   setenv root_hash bf67ab59...
   setenv bootargs ${bootargs} rootfstype=squashfs root=/dev/dm-0 dm-mod.create="rootfs,,0,ro,0 ${sectors} verity 1 /dev/mmcblk0p2 /dev/mmcblk0p2 ${data_block_sz} ${hash_block_sz} ${data_blocks} ${hash_start} ${hash_alg} ${root_hash} ${salt}"
   ```

**為什麼安全**：
- 【口頭】boot script 是 FIT 的一部分，所以**它也被簽了**（[▶ 20:48](https://youtu.be/fBDNqvNLxMk?t=1248)）。
- 投影片 p.25 也寫了：「Without initramfs and veritysetup」「Only with a boot script that extend the kernel cmdline」。

**什麼情況會失敗或被繞過**：
- 講者沒有談。
- 以下**不是逐字稿內容**，是推論：`bootargs` 是「接在原本的 `${bootargs}` 後面」。如果 U-Boot 環境變數可以被改，原本的 `bootargs` 就可能被塞進別的參數。講者沒有提到要怎麼處理這點。⚠️ 待確認

演講到這裡結束（[▶ 21:29](https://youtu.be/fBDNqvNLxMk?t=1289)），影片沒有 Q&A。

---

## 9. 一頁速查表

**信任鏈（本例）**

```
ROM (AHAB, SRK hash 在 OTP)
  └驗→ SECO FW（NXP 簽）、SPL / ATF / U-Boot（OEM 簽）
        └U-Boot 驗→ FIT configuration 簽章（公鑰在 U-Boot DTB）
              ├ kernel、DTB
              └ boot script ── 帶 root hash ──┐
                                               ↓
                      kernel 用 dm-init 建 dm-verity → 讀到哪驗到哪
```

**每段一句話**

| 段 | 在解什麼 | 關鍵一步 | 失敗／被繞過的條件 |
|---|---|---|---|
| AHAB | ROM 要有信任的根 | SRK table 做 hash 燒進 OTP，`ahab_close` 鎖板 | 沒燒 fuse 就不驗；沒 `ahab_close` 前，失敗只留 event |
| CST | 把 bootloader 簽好 | 設定檔指定 SRK、要簽的檔、header／signature offset | offset 要照晶片 datasheet |
| FIT 簽章 | U-Boot 驗 kernel 組合 | 簽 **configuration**（`sign-images`） | 只簽個別 image → mix-and-match |
| dm-verity | rootfs 太大沒辦法整個驗 | 雜湊樹，讀到才驗；只能唯讀 | root hash 沒簽時，要靠上一段保護 |
| dm-init | 不用 initramfs | `dm-mod.create=` 放在 FIT 裡的 boot script | 參數接在 `${bootargs}` 後面 |

---

## 10. 延伸連結

- MT8189 上實際開 FIT 簽章：[`../verified-boot-notes/fit-sign.md`](../verified-boot-notes/fit-sign.md)
- dm-verity 手動操作與開機掛載：[`../verified-boot-notes/verity-manual.md`](../verified-boot-notes/verity-manual.md)、[`../verified-boot-notes/verity-boot.md`](../verified-boot-notes/verity-boot.md)
- 整體：[`../verified-boot-notes/vb-intro.md`](../verified-boot-notes/vb-intro.md)
- TF-A／OP-TEE 端的 secure boot：[`../tf-a-and-op-tee-note/secure-boot-intro.md`](../tf-a-and-op-tee-note/secure-boot-intro.md)

---

## 附：一句話總結

> **ROM 用燒在 OTP 的 SRK hash 驗 bootloader，U-Boot 用簽在 FIT configuration 上的簽章驗 kernel＋boot script，boot script 帶著 root hash 用 dm-init 直接開 dm-verity。三段串起來，不需要 initramfs。**

---

## ⚠️ 待確認清單

1. [▶ 07:07](https://youtu.be/fBDNqvNLxMk?t=427) 「a binary for a SP processor」：p.12 是 M4 image，講者原話是什麼聽不出來。
2. [▶ 07:40](https://youtu.be/fBDNqvNLxMk?t=460) 第二個 container 的內容：口頭說「SPL、ATF、U-Boot」，p.12 寫「SCFW、SPL、M4，U-Boot 和 ATF 由 SPL 載入」。
3. [▶ 12:19](https://youtu.be/fBDNqvNLxMk?t=739) U-Boot 指令名稱：口頭說 hab status／HAB close，p.17 是 `ahab_status`／`ahab_close`，p.11 寫 `hab_status`。
4. [▶ 19:00](https://youtu.be/fBDNqvNLxMk?t=1140) p.24 `veritysetup verify`／`open` 最後的參數（`${HASH_ALG}`、`${KEY} ${SALT}`），跟口頭「要知道 root hash」對不起來。
5. [▶ 20:11](https://youtu.be/fBDNqvNLxMk?t=1211) boot script 把參數接在原本的 `${bootargs}` 後面，講者沒談環境變數被改的情況（推論，不是講者說的）。

---

*筆記依據 Thomas Perrot〈Secure boot in embedded Linux systems〉（Live Embedded Event 2021）錄影（Whisper `turbo` 轉錄，21:47）與 Bootlin 官方投影片整理。*
