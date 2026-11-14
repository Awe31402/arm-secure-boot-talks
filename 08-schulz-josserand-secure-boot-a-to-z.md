---
talk: Secure Boot from A to Z
speaker: Quentin Schulz、Mylène Josserand（Bootlin）
conference: Embedded Linux Conference North America 2018（Portland）
year: 2018（投影片封面：2018-03-13）
video: https://youtu.be/jtLQ8SzfrDU
slides: https://bootlin.com/pub/conferences/2018/elc/josserand-schulz-secure-boot/josserand-schulz-secure-boot.pdf
---

# Secure Boot from A to Z [▶ 影片](https://youtu.be/jtLQ8SzfrDU)

> **演講**：Quentin Schulz、Mylène Josserand（Bootlin，前身 Free Electrons），ELC 2018（2018-03-13）
> **來源**：YouTube 錄影（49:04）用 Whisper `turbo` 轉成逐字稿，再加上 Bootlin 官方投影片（45 頁）。
> **分工**：Quentin 講 ROM → kernel，Mylène 講 rootfs。
> **標記說明**：`【口頭】` 是投影片沒有的。`【投影片補充】` 是投影片有、講者沒講的。`【Q&A】` 是現場提問。`⚠️ 逐字稿缺字` 是 Whisper 聽錯。`⚠️ 待確認` 是查不清楚的地方。
> **年代提醒**：2018 年，例子用 SHA-1（Q&A 有人指出不該用）、i.MX6 HAB、U-Boot 當時的做法。

---

## 目錄

- [0. 這場演講要做什麼](#0-這場演講要做什麼)
- [1. 誰要驗、為什麼、代價](#1-誰要驗為什麼代價)
- [2. 加密 vs 簽章](#2-加密-vs-簽章)
- [3. ROM code：root of trust（i.MX6 HAB）](#3-rom-coderoot-of-trustimx6-hab)
- [4. Bootloader 要鎖死](#4-bootloader-要鎖死)
- [5. U-Boot 驗 kernel 和 DTB：FIT 簽章](#5-u-boot-驗-kernel-和-dtbfit-簽章)
- [6. Rootfs：squashfs＋dm-verity＋內建 initramfs](#6-rootfssquashfsdm-verity內建-initramfs)
- [7. 結論：完整的鏈、Yocto 的坑、可寫分區、ROM 漏洞](#7-結論完整的鏈yocto-的坑可寫分區rom-漏洞)
- [8. Q&A](#8-qa)
- [9. 一頁速查表](#9-一頁速查表)
- [10. 延伸連結](#10-延伸連結)

---

## 0. 這場演講要做什麼

[▶ 00:35](https://youtu.be/jtLQ8SzfrDU?t=35)（p.2–3）

- 他們幫客戶在一塊**客製 i.MX6 板子**上做了完整信任鏈，想分享出來。
- 免責聲明（p.3）：「絕對不是資安專家」；只示範**一種**做法、一個 SoC 系列。大部分可以套到別的板子，i.MX 專屬的地方會提醒。

---

## 1. 誰要驗、為什麼、代價

### 1.1 誰要驗、為什麼

[▶ 01:06](https://youtu.be/jtLQ8SzfrDU?t=66)（p.5）

**產品廠商**：
- 確保裝置照該有的方式使用，不被拿去做別的事。
- 不跑未核准的軟體。【口頭】例如軟體有功能限制、要授權才能用全功能，信任鏈可以確保使用者真的是用有授權的版本（[▶ 01:41](https://youtu.be/jtLQ8SzfrDU?t=101)）。
- 保護消費者，不被裝惡意程式。

**終端使用者**：確定系統沒被竄改。

一句話：確定你要載入、開機、執行的 binary，是**你信任的人** build 的。

### 1.2 怎麼運作

[▶ 02:53](https://youtu.be/jtLQ8SzfrDU?t=173)（p.6–7）

- 全部建立在**數位簽章驗證**上。簽章**不是**加密。
- 第一段驗第二段，第二段驗第三段……所以叫信任鏈。
- **一段被驗證了、但沒有鎖好**（例如 bootloader 有 console、user space 有 root），**裝置就不再算是被驗證過的**，鏈斷了（[▶ 03:24](https://youtu.be/jtLQ8SzfrDU?t=204)）。

**這場的鏈**（p.7；[▶ 03:59](https://youtu.be/jtLQ8SzfrDU?t=239)）：

```
ROM code（公鑰）─簽章驗證→ bootloader（公鑰）─簽章驗證→ kernel（摘要）─雜湊驗證→ rootfs
```

- 前面幾段用簽章＋公鑰驗。
- **rootfs 用雜湊機制驗**。

### 1.3 代價

[▶ 07:47](https://youtu.be/jtLQ8SzfrDU?t=467)（p.10）

1. **後勤與專案複雜度**：要有一整套架構產生金鑰、用金鑰 build……
2. **開發流程變複雜**：平台鎖住後，每次測試都要重新簽 binary、驗證信任鏈。
3. **開機時間**：一路到 Linux prompt 要做一堆驗證。
4. **私鑰一定要非常小心**：【口頭】只要一把被偷或外洩，「你就完蛋了」，任何人都能簽你的 binary（[▶ 08:18](https://youtu.be/jtLQ8SzfrDU?t=498)）。

---

## 2. 加密 vs 簽章

[▶ 05:04](https://youtu.be/jtLQ8SzfrDU?t=304)（p.8–9）

【口頭】兩者不同，但**可以並用**：資料可以同時加密又簽章。

| | 加密 | 簽章 |
|---|---|---|
| 目的 | 只有收件者讀得到 | 證明是誰送的 |
| 寄件者用 | **收件者（Bob）的公鑰** | **自己（Alice）的私鑰** |
| 收件者用 | 自己的私鑰解密 | Alice 的公鑰驗證 |
| 資料別人讀得到嗎 | 不行 | **可以**。【口頭】「這是很重要的觀念：大家都讀得到」 |

Secure boot 用的是**右邊**：binary 是明文，重點是證明它是你簽的。

---

## 3. ROM code：root of trust（i.MX6 HAB）

### 3.1 跟 SoC 綁在一起

[▶ 08:49](https://youtu.be/jtLQ8SzfrDU?t=529)（p.12）

- root of trust 是信任鏈的根本，**完全看 SoC**。【口頭】不是每顆 SoC 都支援 secure boot。
- 要有地方安全地存公鑰，讓 ROM 讀得到、而且**防竄改**。每家廠商自己決定存在哪。
- 檢查簽章的微碼在 ROM 裡，你碰不到。【口頭】只能相信廠商。
- 廠商例子：Xilinx、Tegra、Atmel、Freescale/NXP、Rockchip、ST、Samsung……

### 3.2 公鑰存哪：OTP fuse 裡只放雜湊

[▶ 09:50](https://youtu.be/jtLQ8SzfrDU?t=590)（p.13）

- 要放在 ROM 讀得到的**非揮發記憶體**。NXP 用 **OTP fuse**。
- 【口頭】fuse 可以想成一條導線：有電流通過是 1；灌很大的電流把它燒斷就變 0。**不可逆**（[▶ 10:22](https://youtu.be/jtLQ8SzfrDU?t=622)）。
- OTP fuse 很佔面積、存的資訊很少，而**公鑰至少 1 KiB**（【口頭】有時到 4 KiB）。
  - p.13 寫「佔**矽**面積」。講者口頭說「佔 **PCB** 面積」，應該是口誤。
- 所以：**OTP 只放公鑰的雜湊**，公鑰本身放在別處（例如要載入的 binary 裡）。驗證時比對雜湊就好（[▶ 10:56](https://youtu.be/jtLQ8SzfrDU?t=656)）。
- **放多把**（【口頭】例如 4 把）的雜湊：一把私鑰被偷、外洩或弄丟時，可以**撤銷**它、改用其他把（[▶ 11:28](https://youtu.be/jtLQ8SzfrDU?t=688)）。這樣：
  1. 裝置不會變成完全不驗證。
  2. 不必讓裝置變磚。

### 3.3 開機流程

[▶ 12:01](https://youtu.be/jtLQ8SzfrDU?t=721)（p.14）

1. **把 bootloader 載入一個安全的空間**，防實體攻擊。
   - 【口頭】為什麼：如果在不安全的地方載入並驗證，從「驗完」到「執行」之間有一段時間，**攻擊者可以在這時換掉 binary**，讓它看起來像驗過了，其實沒有（[▶ 12:01](https://youtu.be/jtLQ8SzfrDU?t=721)）。
   - 這就是 **TOCTOU**（Time-Of-Check to Time-Of-Use，檢查和使用之間的時間差）問題，講者沒用這個名詞。
2. 讀出 bootloader 裡附的公鑰。
3. 把公鑰的雜湊跟 OTP 裡的雜湊表比對。
4. 用驗過的公鑰驗 bootloader 的簽章。
5. 執行 bootloader。

這個 SoC 系列叫它 **HAB**（High Assurance Boot）。

### 3.4 設定板子

[▶ 12:37](https://youtu.be/jtLQ8SzfrDU?t=757)（p.15）

1. 用 NXP 的 **CST**（Code Signing Tool）產生金鑰（私鑰和憑證）。
2. 在一個**能動的、還沒驗證的 U-Boot** 裡，用 NXP 專屬的程式碼和 CST 給的 fuse 表燒 fuse。【口頭】指令好像是 `fuse prog`（[▶ 13:08](https://youtu.be/jtLQ8SzfrDU?t=788)）。
3. 用 CST、以 fuse 表裡其中一把金鑰簽 bootloader。
4. 在簽好的 U-Boot 裡用 `hab_status`（NXP 專屬）檢查狀態。
5. 前面都成功了，才**燒鎖定 fuse**，限制只能載入驗證過的 bootloader。

【口頭】**前面任何一步弄錯，又燒了鎖定 fuse，你就完蛋了。一定要確定自己在做對的事。**（[▶ 13:39](https://youtu.be/jtLQ8SzfrDU?t=819)）

### 3.5 看 `hab_status`

[▶ 14:10](https://youtu.be/jtLQ8SzfrDU?t=850)（p.16）

失敗的例子：

```
=> hab_status
Secure boot disabled
HAB Configuration: 0xf0, HAB State: 0x66
--------- HAB Event 1 -----------------
STS = HAB_FAILURE (0x33)
RSN = HAB_INV_CSF (0x11)
CTX = HAB_CTX_CSF (0xCF)
ENG = HAB_ENG_ANY (0x00)
```

成功的例子：`No HAB Events Found!`

讀法：
- `Secure boot disabled`：**還沒燒鎖定 fuse**。燒了就變 `enabled`。
- **有 HAB event = bootloader 驗證失敗。**
- 沒有 event = 驗證成功。

**什麼情況會被繞過**：
- 以下**不是逐字稿內容**，是依 p.16 推論的：鎖定 fuse 燒之前（`Secure boot disabled`），驗證失敗只會留下 event，bootloader 照樣執行。所以沒燒鎖定 fuse 的板子不受保護。

---

## 4. Bootloader 要鎖死

[▶ 14:40](https://youtu.be/jtLQ8SzfrDU?t=880)（p.18）

標題是「Trust (almost) no one」（幾乎誰都別信）。

1. **bootloader 沒被 ROM 驗，就算它會驗別人也沒用**：換一個沒驗證的 bootloader，之後想開什麼都可以（[▶ 15:14](https://youtu.be/jtLQ8SzfrDU?t=914)）。
2. **bootloader 一定要鎖好，否則驗它也沒意義。**
3. **mainline U-Boot 的具體問題**：
   - 【口頭】U-Boot 有一個環境變數叫 **`verify`**。**設成 `no`，U-Boot 就不再驗 image 的簽章**（[▶ 15:45](https://youtu.be/jtLQ8SzfrDU?t=945)）。
   - 所以絕不能讓任何人進 console 改它，要**完全關掉 console**。
   - p.18 的做法：在 `board_early_init_f()` 裡設 `gd->flags |= GD_FLG_DISABLE_CONSOLE`。
4. **任何不在「被 ROM 驗過的 U-Boot binary」裡的東西，都不要信。**
   - 【口頭】環境變數通常放在別的媒體上，那裡的東西**驗證不了，所以不能信**（[▶ 16:17](https://youtu.be/jtLQ8SzfrDU?t=977)）。
   - 預設情況下，只有放在 U-Boot binary 裡的環境（**`ENV_IS_NOWHERE`**）才能信。
5. **跟 OTA 更新衝突**：
   - 【口頭】Linux 的更新軟體常常要寫 U-Boot 環境，告訴它「下次開這個 image」（[▶ 16:17](https://youtu.be/jtLQ8SzfrDU?t=977)）。
   - Quentin 送了一個 U-Boot patch（當時還在審）：**只從外部環境載入少數幾個你指定的變數**，其他都用 binary 內建的。這樣攻擊面變小（[▶ 16:47](https://youtu.be/jtLQ8SzfrDU?t=1007)）。

---

## 5. U-Boot 驗 kernel 和 DTB：FIT 簽章

### 5.1 公鑰放在 U-Boot 的 DTB

[▶ 16:47](https://youtu.be/jtLQ8SzfrDU?t=1007)（p.19）

- U-Boot 支援 DTB，用法跟 kernel 一樣（照 DT 探測 driver）。DTB 也可以拿來**放公鑰**。
- **DTB 接在 U-Boot binary 後面**，所以也被算進 ROM 驗證用的雜湊裡 → **可以信任**（[▶ 17:20](https://youtu.be/jtLQ8SzfrDU?t=1040)）。
- 用 FIT image：一個檔案裝所有 binary 和簽章，不用載入一堆檔案。
- `mkimage` 本來就支援簽 binary 的雜湊。

### 5.2 產生金鑰

[▶ 18:23](https://youtu.be/jtLQ8SzfrDU?t=1103)（p.20）

```
openssl genrsa -out my_key.key 4096
openssl req -batch -new -x509 -key my_key.key -out my_key.crt
```

- 【口頭】憑證跟公鑰很接近。`mkimage` 規定要用憑證，不是公鑰。
- **憑證和私鑰檔名一定要一樣**，否則 `mkimage` 完全不能用（[▶ 18:56](https://youtu.be/jtLQ8SzfrDU?t=1136)）。

### 5.3 放公鑰的 DTS

[▶ 18:56](https://youtu.be/jtLQ8SzfrDU?t=1136)（p.21）

```
/dts-v1/;
/ {
    model = "Keys";
    compatible = "vendor,board";
    signature {
        key-my_key {
            required = "image";
            algo = "sha1,rsa4096";
            key-name-hint = "my_key";
        };
    };
};
```

- `key-name-hint` 和節點名 `key-` 後面的字，**都要跟金鑰名一樣**。
- 【口頭】板子本來就有 DT 的話，加一個 `signature` 節點就好（[▶ 19:28](https://youtu.be/jtLQ8SzfrDU?t=1168)）。
- `required` 是 `image` 或 `conf`：決定在哪一層驗簽章。細節看 U-Boot 的 `doc/uImage.FIT/signature.txt`。

### 5.4 FIT 是什麼

[▶ 20:00](https://youtu.be/jtLQ8SzfrDU?t=1200)（p.22–23）

- 基本上是一個容器：多個 kernel、DTB、script 等，加上雜湊和簽章。
- **configuration**：強迫某幾個 binary 一起載入。例如 `conf@1` 強迫用第一個 kernel 加第三個 DTB（[▶ 20:31](https://youtu.be/jtLQ8SzfrDU?t=1231)）。
- 支援的架構、OS、image 類型在 U-Boot 的 `common/image.c`。
- p.23 的 `.its` 範例：
  - 一個 kernel、兩個 DTB（revA、revB），**每個 image 都有一個 `signature@1`**（`sha1,rsa4096`、`my_key`）。
  - 兩個 configuration，`default = "conf@1"`。

### 5.5 Build

[▶ 21:38](https://youtu.be/jtLQ8SzfrDU?t=1298)（p.24，原文）

```
# DTB 要在 U-Boot 樹外先編，因為要用 mkimage 把公鑰加進去
dtc u-boot_pubkey.dts -O dtb -o u-boot_pubkey.dtb
make CROSS_COMPILE=arm-linux-gnueabihf- foo_defconfig
make CROSS_COMPILE=arm-linux-gnueabihf- tools
tools/mkimage -f fitImage.its -K u-boot_pubkey.dtb -k /path/to/keys -r fitImage
make CROSS_COMPILE=arm-linux-gnueabihf- EXT_DTB=u-boot_pubkey.dtb
```

步驟：
1. `dtc` 先編出公鑰用的 DTB。
2. 編 U-Boot 的工具。
3. `mkimage` 做 FIT，**同時把公鑰寫進那個 DTB**。
4. 用外部 DTB 編 U-Boot。

**U-Boot 要開的選項**（p.25）：
- `CONFIG_SECURE_BOOT=y`（NXP 專屬），並在板子 DCD 檔開頭加 `CSF CONFIG_CSF_SIZE`（NXP 專屬）。
- `CONFIG_OF_CONTROL=y`、`CONFIG_DM=y`、`CONFIG_FIT=y`、`CONFIG_FIT_SIGNATURE=y`。

### 5.6 開機與失敗的樣子

[▶ 23:16](https://youtu.be/jtLQ8SzfrDU?t=1396)（p.26–27）

```
=> bootm 0x15000000      # 或 bootm 0x15000000#conf@1；conf@1 是 default 所以可省略
```

成功時，每個 subimage 都會印：
```
Verifying Hash Integrity ... sha1,rsa4096:my_key+ sha1+ OK
```

**DTB 被改過時**（p.27）：
```
Verifying Hash Integrity ... sha1,rsa4096:my_key- Failed to verify required signature 'key-my_key'
Unable to verify required signature for '' hash node in 'fdt@1' image node
Bad Data Hash
...
ERROR: image is not a fdt - must RESET the board to recover.
FDT creation failed! hanging...### ERROR ### Please RESET the board ###
```

- 【口頭】有人動了 DTB，U-Boot 驗不過，**停止開機**（[▶ 24:22](https://youtu.be/jtLQ8SzfrDU?t=1462)）。

---

## 6. Rootfs：squashfs＋dm-verity＋內建 initramfs

### 6.1 選擇

[▶ 24:55](https://youtu.be/jtLQ8SzfrDU?t=1495)（p.29）

1. **檔案系統改不了**：唯讀的 **squashfs**。
   - 【口頭】這不算 secure boot 流程的一部分，但對他們和客戶很重要。
2. **驗證 rootfs**：**dm-verity**，確認 rootfs（squashfs image）就是預期的那個。
3. dm-verity 需要 user space 工具（`veritysetup`），所以要一個 **initramfs** 當第一個檔案系統，裡面放工具。
4. **initramfs 內建在 kernel 裡**：kernel 已經在信任鏈裡（被 FIT 驗過），所以**信任鏈不會斷**（[▶ 26:38](https://youtu.be/jtLQ8SzfrDU?t=1598)）。

### 6.2 dm-verity 原理

[▶ 26:38](https://youtu.be/jtLQ8SzfrDU?t=1598)（p.30）

- **device mapper**：kernel 裡在 block 裝置上建虛擬層的框架。
- **dm-verity**：用 kernel crypto API 檢查 block 裝置的完整性。
- 可以把整個裝置做雜湊再比對，**但不這樣做**。【口頭】那樣開機會非常久（[▶ 27:14](https://youtu.be/jtLQ8SzfrDU?t=1634)）。
- 改用**雜湊樹**（Merkle tree）：
  - 裝置切成小 block，每個 block 有雜湊。
  - 每個非葉節點是子節點的雜湊，一直到最上面的 **root hash**。
  - **讀到 block 時才算、才驗**。【口頭】開機不變長，只是每次存取稍慢一點（[▶ 27:44](https://youtu.be/jtLQ8SzfrDU?t=1664)）。
- user space 工具：`cryptsetup` 套件的 `veritysetup`，能建雜湊樹、也能驗裝置。

### 6.3 他們的流程

[▶ 28:49](https://youtu.be/jtLQ8SzfrDU?t=1729)（p.31）

1. kernel 開 dm-verity 的 config，帶著 initramfs 開機。
2. initramfs 的 init script 對 block 裝置（他們用 **`ubiblk0`**，UBI block）跑 `veritysetup`。
3. **成功**：拿到驗證過的 squashfs。
4. **失敗**：掛不上 squashfs，**init 停在這裡**（[▶ 29:21](https://youtu.be/jtLQ8SzfrDU?t=1761)）。

### 6.4 建雜湊樹

[▶ 29:53](https://youtu.be/jtLQ8SzfrDU?t=1793)（p.32–33）

- `veritysetup format <data> <hash>`：產生雜湊樹（`hash.img`），**並印出 root hash**。【口頭】root hash 一定要留著，之後驗證要用（[▶ 30:24](https://youtu.be/jtLQ8SzfrDU?t=1824)）。
- 預設：資料和雜湊樹在兩個不同的裝置／image。
- **他們只要一個裝置**：把雜湊 image **接在 squashfs image 後面**，用 `--hash-offset` 指出雜湊區在哪。【口頭】雜湊樹在 squashfs 尾巴，所以 offset 就是 squashfs image 的大小（[▶ 32:05](https://youtu.be/jtLQ8SzfrDU?t=1925)）。

### 6.5 在板子上驗證

[▶ 32:39](https://youtu.be/jtLQ8SzfrDU?t=1959)（p.34–36）

- `veritysetup create <名稱> --hash-offset=<offset> <data 裝置> <hash 裝置> <root hash>`
  - 他們的例子：data 和 hash 都是 `ubiblk0`，所以寫兩次（[▶ 34:21](https://youtu.be/jtLQ8SzfrDU?t=2061)）。
  - 分開放的話（例如 data 在 `ubiblk0`、雜湊在 `ubiblk1`），就不用 `--hash-offset`。
- 雜湊對得上 → 得到 `/dev/mapper/<名稱>` → 可以 mount（或 switch root）。

> p.34–36 是同一張圖的動畫，文字一樣。

### 6.6 offset 和 root hash 怎麼交給 kernel

[▶ 34:53](https://youtu.be/jtLQ8SzfrDU?t=2093)（p.37–39）

**問題**：`veritysetup` 需要 offset 和 root hash，怎麼交給 kernel？

**做法**：
1. 寫一個 **U-Boot 環境 script**，設好 `bootargs`（帶 offset 和 root hash）。
2. **但這個 script 也可能被攻擊** → **把它放進 FIT image**，它就有雜湊和簽章（[▶ 35:25](https://youtu.be/jtLQ8SzfrDU?t=2125)）。
3. U-Boot 驗 script 的簽章：
   - 不對：**source 失敗**。
   - 對：source 它，`bootargs` 就有 offset 和 root hash（[▶ 36:27](https://youtu.be/jtLQ8SzfrDU?t=2187)）。
4. kernel 開機，initramfs 的 init script 從 `bootargs` 讀出值，跑 `veritysetup`。
5. 成功後用 **`switch_root`** 把 rootfs 從 initramfs 換到驗證過的 squashfs。
   - 【口頭】用 switch root 不用 mount，因為不想一直待在 initramfs（[▶ 36:59](https://youtu.be/jtLQ8SzfrDU?t=2219)）。

【口頭】**原則**：只要加了一個新元件（這裡是 U-Boot script），就要把它放進被簽的 FIT，鏈才不會斷（[▶ 37:29](https://youtu.be/jtLQ8SzfrDU?t=2249)）。

---

## 7. 結論：完整的鏈、Yocto 的坑、可寫分區、ROM 漏洞

### 7.1 完整的鏈

[▶ 37:29](https://youtu.be/jtLQ8SzfrDU?t=2249)（p.41）

1. ROM 裡有**最多 4 個公鑰雜湊**，用來驗 bootloader 裡附的公鑰，再用公鑰驗 bootloader 簽章。
2. U-Boot binary 裡有另一把公鑰，驗**整個 FIT**（kernel、DTB、U-Boot script）（[▶ 38:03](https://youtu.be/jtLQ8SzfrDU?t=2283)）。
3. FIT 裡（script 設的 bootargs）帶著摘要，用來驗 rootfs。

### 7.2 Yocto 的依賴循環

[▶ 38:35](https://youtu.be/jtLQ8SzfrDU?t=2315)（p.42）

- Yocto 要做 FIT，kernel recipe 得 inherit `kernel-fitimage` class。
- 這發生在 **rootfs 建好之前**（【口頭】因為大家通常想把 kernel 放進 rootfs 的 `/boot`）。
- 但 U-Boot script 必須放在 FIT 裡，而 script 又要等 **squashfs rootfs 建好**才拿得到 root hash。
- → **依賴循環**。【口頭】「很難除錯」（[▶ 39:39](https://youtu.be/jtLQ8SzfrDU?t=2379)）。
- 解法：丟掉 `kernel-fitimage` class，自己寫新的 image 和 class。【口頭】還在草稿／概念驗證階段，但能動（[▶ 40:10](https://youtu.be/jtLQ8SzfrDU?t=2410)）。

### 7.3 要可寫的檔案系統怎麼辦

[▶ 40:10](https://youtu.be/jtLQ8SzfrDU?t=2410)（p.43）

- 他們的案子很特殊：rootfs 唯讀。
- **不重要的資料**（log、使用者資料……）：另外掛一個可寫分區，放在唯讀 rootfs 旁邊就好。
- **重要的資料**：看 **IMA/EVM**。【口頭】他們沒研究過，只給了連結（[▶ 40:44](https://youtu.be/jtLQ8SzfrDU?t=2444)）。

### 7.4 連 SoC 廠商都不能信

[▶ 41:14](https://youtu.be/jtLQ8SzfrDU?t=2474)（p.44）

- **2017-07-17**，NXP 公開了 i.MX6、i.MX50、i.MX53、i.MX7、i.MX28、Vybrid 的 **ROM code secure boot 漏洞**。
- 【口頭】現在應該修好了。產品要用的話，去問 NXP（[▶ 41:44](https://youtu.be/jtLQ8SzfrDU?t=2504)）。
- **要知道自己的威脅模型，沒有東西是 100% 安全的。**
- 【口頭】推薦同場 Mike Anderson 的逆向工程入門教學，看看別人能怎麼破解你的東西。

---

## 8. Q&A

【Q&A】**Q：做這些花了多久？**（[▶ 42:15](https://youtu.be/jtLQ8SzfrDU?t=2535)）
- 從頭研究所有軟體到完成，兩個人大約 **6 個月**，不是全職。講者說「以月計算，絕對是」。

【Q&A】**Q：你們用 SHA-1，它已經完全被破解了，不該再用。還有，解決依賴循環的程式碼在哪？**（[▶ 42:45](https://youtu.be/jtLQ8SzfrDU?t=2565)）
- SHA-1：講者沒有回應。
- 依賴循環只發生在 Yocto build 時，跟最後的 rootfs 無關。新 recipe **還沒送進 Yocto**，在他們自己的 layer 裡，想繼續做（[▶ 43:46](https://youtu.be/jtLQ8SzfrDU?t=2626)）。

【Q&A】**Q：弄壞了幾塊板子？能用 QEMU 模擬嗎？**（[▶ 43:46](https://youtu.be/jtLQ8SzfrDU?t=2626)）
- **一塊都沒壞**。網路上教學很多，運氣好（[▶ 44:18](https://youtu.be/jtLQ8SzfrDU?t=2658)）。
- QEMU：不知道。

【Q&A】**Q：有量開機時間的影響嗎？**（[▶ 44:18](https://youtu.be/jtLQ8SzfrDU?t=2658)）
- 【口頭】他們覺得沒什麼量的必要：需要安全裝置的話，延遲不是重點（[▶ 45:06](https://youtu.be/jtLQ8SzfrDU?t=2706)）。
- rootfs 這段：據說 I/O 時間比雜湊計算多太多，雜湊的時間可以忽略。

【Q&A】**Q：為什麼 rootfs 不在 U-Boot 裡驗？**（[▶ 45:38](https://youtu.be/jtLQ8SzfrDU?t=2738)）
1. U-Boot 不支援 squashfs。
2. 他們客戶的 kernel 和 rootfs 放在兩個不同的媒體（[▶ 46:08](https://youtu.be/jtLQ8SzfrDU?t=2768)）。
3. 【口頭】而且 dm-verity 是**讀資料時才驗**，讀資料的是 kernel，所以 bootloader 本來就做不了（[▶ 46:42](https://youtu.be/jtLQ8SzfrDU?t=2802)）。

【Q&A】**Q：存了 4 把公鑰，一把壞了怎麼撤銷？**（[▶ 46:42](https://youtu.be/jtLQ8SzfrDU?t=2802)）
- 跟燒公鑰一樣：**燒一個 fuse，表示這把已撤銷**。
- 在 U-Boot 裡做，例如用更新 script 叫它燒（[▶ 47:14](https://youtu.be/jtLQ8SzfrDU?t=2834)）。
- 【口頭】「但如果已經太遲了，那就完蛋了。」

【Q&A】**觀眾分享：只驗一次 squashfs 是不夠的。**（[▶ 47:46](https://youtu.be/jtLQ8SzfrDU?t=2866)）
- squashfs 雖然唯讀，但**不會把所有資料都 cache 住**。有心人可以去改底層 squashfs 裡的資料。
- 他們發現這點，是因為有客戶不小心對**正在跑的** squashfs 執行了更新程式，kernel 很不高興，系統當掉。

**推論**（以下**不是逐字稿內容**）：這正是 dm-verity「每次讀都驗」比「開機時驗一次」安全的原因。只在開機時驗一次，之後從底層裝置重新讀進來的資料就沒人檢查了。

【Q&A】**Q：投影片網址打不開？**（[▶ 48:17](https://youtu.be/jtLQ8SzfrDU?t=2897)）
- 還沒上傳，會放在 sched.org，最慢下週。

---

## 9. 一頁速查表

**整條鏈**

```
OTP: 最多 4 個 SRK 公鑰雜湊（可撤銷）＋鎖定 fuse
 └ROM(HAB，先把 bootloader 載入安全空間再驗)→ U-Boot（console 關閉、ENV_IS_NOWHERE、DTB 內含公鑰）
     └FIT（kernel、DTB、U-Boot script，各自簽）
         └script 設 bootargs（root hash、hash offset）
             └kernel 內建 initramfs → veritysetup create → /dev/mapper → switch_root 到 squashfs
```

| 環節 | 在解什麼 | 怎麼會失敗或被繞過 |
|---|---|---|
| OTP 放雜湊 | fuse 空間太小放不下公鑰 | 燒錯又燒鎖定 fuse → 板子廢了 |
| 多把 SRK | 一把外洩時還能撤銷 | 已經被拿來簽了才撤銷就太遲 |
| ROM 載入安全空間 | 驗完到執行之間被換掉（TOCTOU） | — |
| 鎖定 fuse | 只能開驗過的 bootloader | 沒燒時驗證失敗只留 event，照樣開機 |
| 關 U-Boot console | `verify=no` 就不驗簽章 | console 開著 = 鏈斷 |
| 環境變數 | 外部環境驗證不了 | 用外部環境 → 可被改；只放行少數變數 |
| FIT 裡放 script | root hash 不能被竄改 | script 在 FIT 外 → 被改掉 |
| dm-verity | rootfs 太大，讀到才驗 | 只驗一次的話，底層被改就看不出來 |

---

## 10. 延伸連結

- MT8189 上的 FIT 簽章、U-Boot `setenv verify n` 能跑被改的 kernel（正好是第 4 節講的洞）：[`../verified-boot-notes/fit-sign.md`](../verified-boot-notes/fit-sign.md)
- MT8189 上的 dm-verity（verity data block 大小、內建 initramfs 的坑）：[`../verified-boot-notes/verity-boot.md`](../verified-boot-notes/verity-boot.md)、[`../verified-boot-notes/verity-manual.md`](../verified-boot-notes/verity-manual.md)

---

## 附：一句話總結

> **ROM 用 OTP 裡的公鑰雜湊驗 U-Boot，U-Boot（console 關掉、環境內建）用 DTB 裡的公鑰驗 FIT，FIT 裡的 script 把 root hash 交給內建 initramfs 開 dm-verity。每加一個元件都要放進被簽的東西裡，而且連 SoC 的 ROM 都可能有洞。**

---

*筆記依據 Quentin Schulz、Mylène Josserand〈Secure Boot from A to Z〉（ELC 2018）錄影（Whisper `turbo` 轉錄，49:04）與 Bootlin 官方投影片整理。*
