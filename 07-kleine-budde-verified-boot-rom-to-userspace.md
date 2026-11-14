---
talk: Verified Boot: From ROM to Userspace
speaker: Marc Kleine-Budde（Pengutronix）
conference: Embedded Linux Conference Europe 2016（柏林）——依投影片與口頭線索推定，見下方說明
year: 2016
video: https://youtu.be/lkFKtCh2SaU
slides: https://elinux.org/images/f/f8/Verified_Boot.pdf（ELCE 2016 版，2016-10-12）
---

# Verified Boot: From ROM to Userspace [▶ 影片](https://youtu.be/lkFKtCh2SaU)

> **演講**：Marc Kleine-Budde（Pengutronix），Linux Foundation 頻道 2017-04-04 上傳。
> **場次**：找到的官方投影片是 ELCE 2016（2016-10-12）版。錄影裡講者說「幾週前有用監視器做的大 DDoS」，又說用的 barebox「已經是 2016.10 了」，比較像 ELCE 2016 的錄影，但沒有直接證據。⚠️ 待確認
> **來源**：YouTube 錄影（54:42）用 Whisper `turbo` 轉成逐字稿，再加上 elinux.org 上的 ELCE 2016 投影片（20 頁）。
> **標記說明**：`【口頭】` 是投影片沒有的。`【投影片補充】` 是投影片有、講者沒講的。`【Q&A】` 是現場提問（這場講到一半就開始有人問）。`⚠️ 逐字稿缺字` 是 Whisper 聽錯。`⚠️ 待確認` 是查不清楚的地方。
> **年代提醒**：2016 年的做法（Linux 4.0、barebox 2016.09、IMA/EVM 保護 rootfs），照講者當時講的寫。

---

## 目錄

- [0. 這場演講要做什麼](#0-這場演講要做什麼)
- [1. 為什麼要 verified boot](#1-為什麼要-verified-boot)
- [2. 四段開機，每段一把錨](#2-四段開機每段一把錨)
- [3. ROM 驗 bootloader（i.MX6 HABv4）](#3-rom-驗-bootloaderimx6-habv4)
- [4. Bootloader 驗 FIT image](#4-bootloader-驗-fit-image)
- [5. Kernel 驗 rootfs：IMA＋EVM 簽章（唯讀時）](#5-kernel-驗-rootfsimaevm-簽章唯讀時)
- [6. 可寫 rootfs：EVM 改用 HMAC，祕密放在 blob](#6-可寫-rootfsevm-改用-hmac祕密放在-blob)
- [7. 加密：eCryptfs](#7-加密ecryptfs)
- [8. 開機時間](#8-開機時間)
- [9. Demo](#9-demo)
- [10. 用到的元件、還缺什麼](#10-用到的元件還缺什麼)
- [11. 實務經驗](#11-實務經驗)
- [12. 結尾 Q&A](#12-結尾-qa)
- [13. 一頁速查表](#13-一頁速查表)
- [14. 延伸連結](#14-延伸連結)

---

## 0. 這場演講要做什麼

[▶ 00:00](https://youtu.be/lkFKtCh2SaU?t=0)

- 從 ROM code 一路開到 user space，**每一段都被驗證**。開完機就能確定系統沒被動過。
- 目標還包括：**rootfs 可以讀寫，但仍然受保護**。

【口頭】講者現場調查（[▶ 02:49](https://youtu.be/lkFKtCh2SaU?t=169)）：
- 開過嵌入式系統的人：很多。
- 驗 bootloader 的：少一些。
- 驗 kernel 的：更少。
- 驗檔案系統的：很少。
- **可寫、又被驗證的檔案系統**：幾乎沒有。這就是這場要講的。

---

## 1. 為什麼要 verified boot

[▶ 00:33](https://youtu.be/lkFKtCh2SaU?t=33)（p.2–3）

- **很誘人的攻擊目標**：Linux 系統控制工業、醫療、車用等關鍵設備。
  - 【口頭】例子：幾週前有一場大型 DDoS，用的就是跑 Linux 的監視器（[▶ 01:04](https://youtu.be/lkFKtCh2SaU?t=64)）。
- **嵌入式系統的維護比伺服器差。**【口頭】不過這次會議很多場在談更新，希望情況會變好。
- **軟體很複雜**：每個 Linux 系統一定有還沒被發現的漏洞，上面可能還有閉源的商用程式。所以要做 **defense in depth**（縱深防禦，一層層防護），verified boot 是其中一層（[▶ 02:15](https://youtu.be/lkFKtCh2SaU?t=135)）。
- **可以自己做**：到處都有帶硬體支援的 SoC，【口頭】至少有些文件是公開的；需要的軟體都是自由軟體。

**要保護什麼**（p.3；[▶ 03:50](https://youtu.be/lkFKtCh2SaU?t=230)）：
- bootloader、kernel、檔案系統（程式、設定檔、應用資料）。
- 威脅模型：**攻擊者可以改所有存放的資料** → 要能**偵測任何竄改**。

---

## 2. 四段開機，每段一把錨

[▶ 03:50](https://youtu.be/lkFKtCh2SaU?t=230)（p.4）

| 段 | 這個例子用什麼 | 演算法 | 下一把錨放哪 |
|---|---|---|---|
| ROM code | 廠商專屬：Freescale/NXP i.MX6 **HABv4** | SHA＋RSA | SoC fuse 裡（憑證雜湊） |
| Bootloader | **barebox** | — | bootloader 裡的公鑰 |
| Kernel／DT／initramfs | **FIT image** | SHA＋RSA | kernel 裡的公鑰 |
| Root file system | **IMA＋EVM** | HMAC＋RSA | — |

- 【口頭】ROM code 燒在矽晶片上。上電後先跑它，決定從哪裡開機：eMMC、網路、USB……（[▶ 04:25](https://youtu.be/lkFKtCh2SaU?t=265)）
- 【口頭】從上往下看：第一把錨在 SoC，第二把在 bootloader，第三把在 kernel／initramfs。全部開完，就能確定系統沒被改過（[▶ 06:02](https://youtu.be/lkFKtCh2SaU?t=362)）。

---

## 3. ROM 驗 bootloader（i.MX6 HABv4）

[▶ 06:02](https://youtu.be/lkFKtCh2SaU?t=362)（p.5–6）

**為什麼 bootloader 一定要驗**：
- **換掉 bootloader 就能完全控制系統。**
- 【口頭】手機 root 的第一步就是換上自己的 bootloader。
- bootloader 通常放在**沒有保護**的儲存：NAND、eMMC、SD、USB。
- 現代 Arm 系統上第一個跑的是 ROM code，所以要由 ROM 在啟動 bootloader 前先驗它（[▶ 06:36](https://youtu.be/lkFKtCh2SaU?t=396)）。

**i.MX6 的做法**（p.6；[▶ 07:16](https://youtu.be/lkFKtCh2SaU?t=436)）：

1. 用 Freescale 的**專屬工具**簽 bootloader。
2. 對應**憑證的雜湊**燒進 i.MX 晶片的 fuse。
3. 開機時：
   1. ROM 先用 fuse 裡的雜湊，確認 bootloader 附帶的**公鑰／憑證**是對的。
   2. 再用這把公鑰驗**簽章**。簽章涵蓋整個 bootloader。
4. bootloader 裡放著**下一段**的公鑰。

> ⚠️ 逐字稿缺字：「Hub」＝HAB；「Spangotronics」＝Pengutronix。

（燒 fuse 的細節在中場 Q&A，見 6.3。）

---

## 4. Bootloader 驗 FIT image

[▶ 08:27](https://youtu.be/lkFKtCh2SaU?t=507)（p.7–8）

**為什麼用 FIT**：
- 【口頭】要在早期 user space 做一些設定，所以需要 initramfs。
- FIT 原本來自 U-Boot：一個 image 裡有 kernel、一個或多個 device tree、initramfs。
- 可以有多個 **configuration**。【口頭】例如一個 kernel 配多個 DT，一個 FIT 就能用在多種板子，由 bootloader 挑對的 configuration（[▶ 09:04](https://youtu.be/lkFKtCh2SaU?t=544)）。
- FIT **可以放在不可信的媒體**：獨立分區，或甚至放在 rootfs 裡（bootloader 讀得到的話）。

**驗證順序**（[▶ 09:35](https://youtu.be/lkFKtCh2SaU?t=575)）：

1. bootloader 先**挑一個 configuration**。
2. 用 bootloader 裡的公鑰驗這個 configuration 的**簽章**。
3. 簽章通過後，驗 configuration 裡三個 image（kernel、DT、initramfs）的**雜湊**。
4. 都對了才開 kernel、載 initramfs。
5. kernel 裡放著**下一把**公鑰，用來驗 rootfs。

**防 mix-and-match**（p.7；[▶ 10:39](https://youtu.be/lkFKtCh2SaU?t=639)）：
- **永遠簽整個 configuration**（kernel＋DT＋initramfs）。
- 【口頭】這樣攻擊者就不能從多個 configuration 裡挑「這個 kernel、第二個 DT、拿掉 initramfs」，因為 configuration 被簽了，改不了。

---

## 5. Kernel 驗 rootfs：IMA＋EVM 簽章（唯讀時）

[▶ 11:10](https://youtu.be/lkFKtCh2SaU?t=670)（p.9–10）

**目標**：保護 rootfs 裡的**每一個檔案**，之後才能做可寫掛載。

**前提**：檔案系統要支援 **extended attribute**（xattr，擴充屬性）。
- 這個例子用 ext4。
- 【口頭】有客戶用 UBIFS：裸 NAND 配 UBI＋UBIFS；eMMC 這類 block 裝置用 ext4（[▶ 11:43](https://youtu.be/lkFKtCh2SaU?t=703)）。

### 5.1 第一層：IMA

[▶ 12:13](https://youtu.be/lkFKtCh2SaU?t=733)

- **IMA**（Integrity Measurement Architecture）已經進 mainline。
- 每個檔案內容的雜湊（SHA1 或 SHA256）存在 xattr **`security.ima`**。
- kernel **開啟、執行、mmap** 一個檔案時：讀出 xattr，算檔案雜湊，比對（[▶ 12:47](https://youtu.be/lkFKtCh2SaU?t=767)）。

**IMA 自己擋不住什麼**（[▶ 13:21](https://youtu.be/lkFKtCh2SaU?t=801)）：
- 【口頭】攻擊者改了檔案，**重新算一個雜湊寫回去**就好。

### 5.2 第二層：EVM 簽章

[▶ 13:21](https://youtu.be/lkFKtCh2SaU?t=801)

- **EVM**（Extended Verification Module），也已經進 mainline。
- 對所有 **security 類 xattr**（包括 `security.ima`）做簽章，存在 **`security.evm`**。
- 在**開發電腦**上做 image 時，用私鑰簽每個檔案。
- 簽章用 RSA，對應 **kernel 裡的公鑰**。

**驗證鏈**（p.10；[▶ 14:25](https://youtu.be/lkFKtCh2SaU?t=865)）：

```
kernel 公鑰 ─驗→ EVM 簽章 ─保護→ IMA 雜湊 ─驗→ 檔案內容
```

> ⚠️ 逐字稿缺字：「CVM」＝EVM；「Attica／Etika」＝attacker。

---

## 6. 可寫 rootfs：EVM 改用 HMAC，祕密放在 blob

### 6.1 為什麼不能再用 RSA

[▶ 15:03](https://youtu.be/lkFKtCh2SaU?t=903)（p.11）

- 檔案改了就要重算簽章。但**私鑰不在裝置上**（也不能在）。
- 【口頭】如果私鑰在裝置上，攻擊者拿走它、重算一切，沒人會發現。
- p.11 另一個理由：RSA 很慢。

### 6.2 改用 HMAC

[▶ 15:38](https://youtu.be/lkFKtCh2SaU?t=938)（p.11–12）

- EVM 改用 **SHA-HMAC**：同時保證完整性和來源（authentication）。
- **每台裝置要用不同的共享祕密（shared secret）**（[▶ 16:11](https://youtu.be/lkFKtCh2SaU?t=971)）。
  - 【口頭】否則攻擊者攻破一台、改了檔案，就能把改過的檔案搬到另一台。
- **第一次存取檔案時，RSA 簽章就被換成 HMAC**（p.11）。
  - 【口頭】HMAC 只是一堆雜湊，**驗起來比 RSA 快**，想開機快就該用它（[▶ 16:41](https://youtu.be/lkFKtCh2SaU?t=1001)）。
- 結果：每個檔案有 IMA 雜湊＋EVM HMAC。
  - **只有正確開機的系統才拿得到 EVM 祕密。**
  - 攻擊者改了檔案，**算不出對應的 HMAC**（[▶ 17:13](https://youtu.be/lkFKtCh2SaU?t=1033)）。

### 6.3 【Q&A】中場：fuse 是怎麼燒的

講者講到一半，有人發問（[▶ 18:17](https://youtu.be/lkFKtCh2SaU?t=1097)）。

**Q：fuse 裡放的是什麼？生產時怎麼燒？只能燒一次嗎？**
- fuse 放的是**簽 bootloader 那把金鑰的憑證（公鑰）的雜湊**（[▶ 18:47](https://youtu.be/lkFKtCh2SaU?t=1127)）。
- 燒了之後公鑰就不能換，系統只開得了用那把公鑰驗得過的 bootloader。
- **只能燒一次**（[▶ 19:49](https://youtu.be/lkFKtCh2SaU?t=1189)）。
  - fuse 只能從一個值改成另一個值，不能改回來。
  - **還有另一個 fuse 可以禁止再燒其他 fuse**，連剩下還能翻轉的位元都鎖住。
- 什麼時候燒：生產時最初的測試階段，**也可以在 bootloader 裡自動做**。

**Q：Freescale 的工具什麼時候用？**（[▶ 20:21](https://youtu.be/lkFKtCh2SaU?t=1221)）
- build BSP 時用它簽 bootloader，需要工具和私鑰。
- fuse 隨時可以燒：產生金鑰對後，算公鑰的摘要燒進 SoC。
- 【口頭】**燒進 fuse 的東西不需要保密**，只有私鑰要保密（[▶ 20:52](https://youtu.be/lkFKtCh2SaU?t=1252)）。

### 6.4 EVM 祕密從哪來：unique key＋blob

[▶ 17:43](https://youtu.be/lkFKtCh2SaU?t=1063)、[▶ 20:52](https://youtu.be/lkFKtCh2SaU?t=1252)（p.12）

1. i.MX6 上，**用正確簽章的 bootloader 開機之後**，才能使用一把**每顆 i.MX6 都不同的 unique key**。
   - 【口頭】所以用它加密的資料不能搬到別台。
   - 【口頭】**沒有用安全、驗證過的 bootloader 開機，就用不了這把金鑰**。
2. 用 unique key 加密 EVM 的共享祕密，做成一個 **blob**，存在媒體上某處（[▶ 21:30](https://youtu.be/lkFKtCh2SaU?t=1290)）。
3. 開機：initramfs 解開 blob，拿到 EVM 祕密。
4. **EVM 祕密只留在 kernel 裡**（[▶ 22:06](https://youtu.be/lkFKtCh2SaU?t=1326)）。
5. 可寫的 rootfs：EVM 祕密驗 HMAC → HMAC 保護 IMA 雜湊 → IMA 雜湊驗檔案。

- 【口頭】blob 在**工廠**產生，用硬體亂數產生器（[▶ 31:22](https://youtu.be/lkFKtCh2SaU?t=1882)）。

### 6.5 【Q&A】中場：blob 安全嗎？

一段很長的來回（[▶ 22:06](https://youtu.be/lkFKtCh2SaU?t=1326)～[▶ 30:22](https://youtu.be/lkFKtCh2SaU?t=1822)）。整理如下：

**Q：blob 怎麼保護？**
- 用 unique key 加密。unique key 每顆 i.MX 不同，**只有用簽過的 bootloader 開機才能用**。

**Q：第一次開機時 RSA 簽章被換成 HMAC。如果攻擊者把檔案系統還原到還是 RSA 的狀態，再換掉 blob 呢？**（[▶ 22:44](https://youtu.be/lkFKtCh2SaU?t=1364)）
- 答：blob 只能在**安全開機的系統上**產生。
- 【口頭】要重做 blob，得先在 bootloader 或別處找到 bug。從 USB 開機寫不出 blob，因為拿不到 unique key（[▶ 24:27](https://youtu.be/lkFKtCh2SaU?t=1467)）。

**Q：如果 blob 只有加密、沒有驗證，攻擊者可以做密文攻擊（改密文讓解出來的祕密變成他想要的）。**（[▶ 25:00](https://youtu.be/lkFKtCh2SaU?t=1500)）
- 這段來回很亂，講者一開始答不出 blob 有沒有被驗證（[▶ 27:33](https://youtu.be/lkFKtCh2SaU?t=1653)）。
- 最後的答案：blob 由 **crypto engine** 處理（[▶ 28:03](https://youtu.be/lkFKtCh2SaU?t=1683)）：
  - **改 blob 的任何一個位元，crypto engine 都會說「這個 blob 被動過了」**。
  - 現場有人補充：是 **AES-CCM**，**解密時同時驗證**（[▶ 28:36](https://youtu.be/lkFKtCh2SaU?t=1716)）。
  - 【口頭】而且就算用同一把金鑰加密同一份祕密，每次做出的 blob 都不一樣（[▶ 29:15](https://youtu.be/lkFKtCh2SaU?t=1755)）。
  - 軟體拿得到 blob，但**拿不到 unique key**，只能叫 crypto engine「用 unique key 幫我加密／解密」（[▶ 29:48](https://youtu.be/lkFKtCh2SaU?t=1788)）。

**Q：為什麼要加密 blob，簽章不夠嗎？**（[▶ 29:48](https://youtu.be/lkFKtCh2SaU?t=1788)）
- 答：因為裡面是**祕密**（HMAC 的共享祕密），不是公鑰（[▶ 30:22](https://youtu.be/lkFKtCh2SaU?t=1822)）。

**Q：如果我的應用程式被攻破，它寫進檔案系統的東西，下次開機不就都被接受了？**（[▶ 30:52](https://youtu.be/lkFKtCh2SaU?t=1852)）
- 答：對。**這主要防的是離線修改**（拔下儲存直接改）。
- 應用程式寫好、user space 強化，是縱深防禦的**另一層**。
- 【口頭】有實體接觸的攻擊者通常會直接換 bootloader；這套機制擋的就是那種（[▶ 31:22](https://youtu.be/lkFKtCh2SaU?t=1882)）。

> ⚠️ 逐字稿缺字：「ISCCN」「ASC in CCM」推測是 AES-CCM。

---

## 7. 加密：eCryptfs

[▶ 31:55](https://youtu.be/lkFKtCh2SaU?t=1915)（p.13–14）

同樣的「blob＋unique key」概念，可以用在 **eCryptfs**：
- **檔案層級加密**。
- 因為在檔案這一層運作，**NAND（UBI/UBIFS）和 block 裝置都能用**（[▶ 32:30](https://youtu.be/lkFKtCh2SaU?t=1950)）。
- 加密檔案系統裡的每個檔案，對應下層檔案系統的一個檔案：
  - **檔名、內容加密**。
  - **目錄結構和權限是明文**（[▶ 33:01](https://youtu.be/lkFKtCh2SaU?t=1981)）。
- 一樣要**每台不同的共享祕密**（理由同 HMAC：不能把加密資料搬到別台）。
- **不需要 IMA/EVM**：eCryptfs 用 **AES-GCM**，加密和完整性一次搞定（[▶ 33:33](https://youtu.be/lkFKtCh2SaU?t=2013)）。
- 流程：fuse → unique key → blob → eCryptfs 祕密 → 加密檔案。
- 【口頭】適合放：專屬應用程式、設定、資料庫，**甚至不想放在系統裡的祕密金鑰**（[▶ 34:06](https://youtu.be/lkFKtCh2SaU?t=2046)）。

【Q&A】**Q：能不能用 eCryptfs 加密整個 rootfs，再 switch root 過去？**（[▶ 34:06](https://youtu.be/lkFKtCh2SaU?t=2046)）
- 可以：在 initramfs 裡做，再切換到解鎖後的檔案系統。
- 【口頭】「GPL 的問題你得去問律師」（[▶ 34:36](https://youtu.be/lkFKtCh2SaU?t=2076)）。

---

## 8. 開機時間

【Q&A】**Q：對開機時間有什麼影響？**（[▶ 35:06](https://youtu.be/lkFKtCh2SaU?t=2106)）

- 有額外負擔。**系統越慢，負擔越大。**
- i.MX6 用 crypto engine，【口頭】整體開機時間大概多 10%，但用硬體會省下不少 CPU。
- i.MX25 分析過：【口頭】講者說「30 秒裡大概多 10 秒」（[▶ 35:38](https://youtu.be/lkFKtCh2SaU?t=2138)）。⚠️ 待確認：這句聽起來是在回想數字。
- RSA 換成 HMAC 之後更快。
- 負擔的來源：
  - 要先開 initramfs 再切到 rootfs，比直接開 rootfs 慢（[▶ 36:08](https://youtu.be/lkFKtCh2SaU?t=2168)）。
  - **I/O 變多**：例如 systemd 啟動時會 mmap 一堆 library。平常 kernel 只會碰一下；開了 IMA，**每個被碰到的檔案都要整個讀進 RAM 檢查**（[▶ 36:42](https://youtu.be/lkFKtCh2SaU?t=2202)）。
- i.MX6 上沒有正式量過。

---

## 9. Demo

[▶ 36:42](https://youtu.be/lkFKtCh2SaU?t=2202)（p.15；RIoTboard）

1. 為了方便，demo 把 blob 放在 bootloader 環境變數裡。
2. 開機：initramfs 讀 blob，交給 kernel 解（[▶ 37:52](https://youtu.be/lkFKtCh2SaU?t=2272)）。
3. 設定 IMA/EVM policy：
   - kernel 匯出的檔案系統（debugfs 等）**不量測**。
   - 最後設「**appraise and measure**」：檢查所有東西，**簽章不符就拒絕存取**（[▶ 38:25](https://youtu.be/lkFKtCh2SaU?t=2305)）。
4. **竄改測試**：ext4 rootfs 裡有個 `zip` 程式，**離線**改了它的版權字串（[▶ 38:57](https://youtu.be/lkFKtCh2SaU?t=2337)）。
   - 執行它：debug 訊息顯示「hash is invalid」，帶出執行者、檔案路徑、檔案系統，最後 **permission denied**。
   - 【口頭】**失敗時的動作可以自己設定**。他們幫一個客戶做的是：把系統標成 **compromised**，不再嘗試開這套，重開機改開另一套系統（[▶ 39:28](https://youtu.be/lkFKtCh2SaU?t=2368)）。
5. **eCryptfs**（[▶ 40:15](https://youtu.be/lkFKtCh2SaU?t=2415)）：
   - 掛著時，檔案 `bar` 內容是 `foo`。
   - 卸載後看底層：檔名加密了，內容也加密了，而且檔案變大（有額外 metadata，【口頭】沒辦法從大小推回原始大小）。
   - 底層的加密檔沒辦法直接存取，因為它沒有 IMA 雜湊（[▶ 41:20](https://youtu.be/lkFKtCh2SaU?t=2480)）。

---

## 10. 用到的元件、還缺什麼

### 10.1 自己試

[▶ 41:50](https://youtu.be/lkFKtCh2SaU?t=2510)（p.16）

- 便宜的板子：i.MX28（I2SE Duckbill、MYIR MYD-IMX28X）、i.MX53（USB Armory）、i.MX6（Cubox-i、RIoTboard，demo 用的就是 RIoTboard）。
- 【投影片補充】p.16：**沒有硬體支援的話，可以用唯讀 SPI-NOR 或 eMMC＋TPM。**
- 【口頭】幫客戶做過的是 i.MX25 和 i.MX6。i.MX28 客戶後來決定不做（[▶ 42:21](https://youtu.be/lkFKtCh2SaU?t=2541)）。
  > ⚠️ 逐字稿缺字：「IMX 26」依 p.17 應為 i.MX6。

### 10.2 元件

[▶ 42:21](https://youtu.be/lkFKtCh2SaU?t=2541)（p.17）

| 元件 | 版本／說明 |
|---|---|
| bootloader | barebox 2016.09。【口頭】全部已進 mainline，只要告訴 barebox 要簽，再用 Freescale 的專屬工具簽 |
| kernel | Linux 4.0.9＋patch |
| 離線簽 image | e2fsprogs（ext4，＋patch）、ima-evm-utils（＋patch）。【口頭】UBIFS 用的 mtd-utils patch 已經進 mainline |
| 整合 | ptxdist。【口頭】也可以用 Yocto 之類的工具，元件都是公開的 |

### 10.3 還缺什麼

[▶ 43:31](https://youtu.be/lkFKtCh2SaU?t=2611)（p.18）

1. **目錄保護**：
   - 【口頭】IMA/EVM 現在**不保護目錄**。所以可以**把一個檔案搬到系統的另一個位置**，或刪除、新增檔案（[▶ 44:01](https://youtu.be/lkFKtCh2SaU?t=2641)）。
   - 郵件列表上有「directory integrity protection」patch，但沒進 mainline。
2. **mainline**：ext4 離線建 image（mkfs.ext4、ima-evm-utils）的 patch；i.MX6 crypto engine（**CAAM**）和 i.MX25 crypto engine 的 blob driver。
3. **更多 SoC**：i.MX53（應該可以，大致相容）、其他廠商（p.18：「文件？」）。【口頭】TI 可能可以（[▶ 44:32](https://youtu.be/lkFKtCh2SaU?t=2672)）。

---

## 11. 實務經驗

[▶ 45:05](https://youtu.be/lkFKtCh2SaU?t=2705)（p.19）

【口頭】這個專案做了大約兩年，學到的：

1. **開發用金鑰直接放在 BSP 裡**：讓每個開發者都能 build rootfs 和 bootloader 來玩。
2. **量產金鑰絕不能放 BSP**，用 **PKCS#11** 存取（[▶ 45:39](https://youtu.be/lkFKtCh2SaU?t=2739)）。所有工具都支援這個標準 API。金鑰可以放在智慧卡、網路上的 HSM，或廠商提供的線上 HSM 服務。
3. **有些套件做成開發／量產兩種設定**（[▶ 46:10](https://youtu.be/lkFKtCh2SaU?t=2770)）：
   - **bootloader**：
     - 開發版：可以登入、有 shell、能讀 kernel log、能 NFS root 開機。
     - 量產版：全部鎖死，**沒有互動、沒有狀態、沒有環境變數**，用量產金鑰。
     - 【口頭】分開，開發者才能開心工作，不會被 bootloader 卡住。
   - **kernel／initramfs**：
     - 一個版本一偵測到安全違規就**重開機**。
     - 另一個只說「permission denied，有安全問題」（[▶ 46:44](https://youtu.be/lkFKtCh2SaU?t=2804)）。
4. **整合期間，每個 release 逐步多開一點安全功能**（[▶ 47:22](https://youtu.be/lkFKtCh2SaU?t=2842)）。
5. **一旦啟用，客退品（field return）很難除錯**。【口頭】系統全鎖死、進不去時「一點都不好玩」，要事先想到（[▶ 47:52](https://youtu.be/lkFKtCh2SaU?t=2872)）。
6. **UBIFS＋IMA/EVM 很討厭突然斷電**（[▶ 47:52](https://youtu.be/lkFKtCh2SaU?t=2872)）。
   - 【口頭】客戶的使用者直接拔電源時，可寫的 UBIFS 會出問題。可能是舊 kernel（4.0）的 bug，要更新。

---

## 12. 結尾 Q&A

【Q&A】**Q：這個 fuse 機制聽起來像窮人版 TPM。TPM 據說只要幾分錢，為什麼小系統沒人放？**（[▶ 48:24](https://youtu.be/lkFKtCh2SaU?t=2904)）
- 講者：也許 arm64 伺服器等級的硬體會整合 TPM。板子上還是可以另外放 TPM。
- 他不知道有哪塊 Arm 板子有 TPM（[▶ 49:30](https://youtu.be/lkFKtCh2SaU?t=2970)）。現場有人說他有一塊 TI 的 ARM32 板子有 TPM。
- 補充：**IMA/EVM 一開始就是為 TPM 設計的**，沒有 TPM 時需要的那些東西是後來才加的。

【Q&A】**評論：簽 bootloader 還是要專屬工具，其他部分（blob）某種程度上就是在取代 TPM。**（[▶ 50:00](https://youtu.be/lkFKtCh2SaU?t=3000)）
- 講者：對。Freescale 提供這套專屬方法，工具是專屬的，「也許晶片廠哪天會聽我們的」。

【Q&A】**Q：UBIFS 斷電的問題？**（[▶ 50:30](https://youtu.be/lkFKtCh2SaU?t=3030)）
- 講者：還沒除錯。客戶很在意成本，選了裸 NAND 而不是 eMMC 這種 managed NAND。（後半句是現場有人插話：那斷電壞掉就是別人的錯了。）

【Q&A】**Q：10 秒的負擔應該跟 rootfs 大小有關？**（[▶ 51:01](https://youtu.be/lkFKtCh2SaU?t=3061)）
- 答：**跟 rootfs 大小無關**。只檢查**被用到、被開啟、被碰到**的檔案。
- 「rootfs 有 1 TB，沒碰到的檔案就不會被檢查。」不是開機時從頭到尾一個 block 一個 block 地驗（[▶ 51:33](https://youtu.be/lkFKtCh2SaU?t=3093)）。

【Q&A】**Q：crypto 用哪個框架？**（[▶ 52:05](https://youtu.be/lkFKtCh2SaU?t=3125)）
- IMA/EVM 用 kernel 的 crypto framework。crypto engine driver 已經在 mainline，接到 framework 上，開了就自動用。
- i.MX53 的 SAHARA 只有部分支援；不支援時自動退回軟體 SHA／RSA（[▶ 52:37](https://youtu.be/lkFKtCh2SaU?t=3157)）。

【Q&A】**Q：解開的 EVM 祕密能不能留在 crypto engine 裡，不放在 RAM？**（[▶ 52:37](https://youtu.be/lkFKtCh2SaU?t=3157)）
- 講者：祕密在 **kernel space**，不在 user space（[▶ 53:07](https://youtu.be/lkFKtCh2SaU?t=3187)）。
- 提問者：有些 SoC 解開 blob 時可以直接把金鑰放進硬體，只傳 handle，這樣掃 RAM 也拿不到。
- 講者：應該可行，但要 crypto engine 和硬體先支援。**目前不支援**，「但會很好」（[▶ 53:38](https://youtu.be/lkFKtCh2SaU?t=3218)）。

---

## 13. 一頁速查表

**整條鏈**

```
SoC fuse（憑證雜湊，不需保密；另有 fuse 禁止再燒）
  └ROM(HABv4)驗→ barebox（內含 FIT 公鑰）
      └驗 configuration 簽章＋三個雜湊→ FIT: kernel（內含 EVM 公鑰）＋DT＋initramfs
          └initramfs: 用 unique key 解 blob → EVM 祕密（只留在 kernel）
              └EVM（RSA 簽章；首次存取後改成 HMAC）保護 IMA 雜湊 → 驗檔案內容
```

| 問題 | 答案 |
|---|---|
| 為什麼 IMA 不夠？ | 攻擊者改檔後可以自己重算雜湊；要 EVM 保護雜湊 |
| 可寫時為什麼不能用 RSA？ | 私鑰不能在裝置上 |
| HMAC 祕密為什麼要每台不同？ | 不然改過的檔案可以搬到別台 |
| 誰拿得到 unique key？ | 只有用簽過的 bootloader 開機的系統，而且只能叫 crypto engine 用它 |
| blob 被改會怎樣？ | crypto engine（AES-CCM）解密時就驗出來 |
| 防什麼、不防什麼？ | 防**離線**竄改；不防執行中被攻破的程式寫入（要靠其他層） |
| 還有什麼洞？ | 目錄沒保護：檔案可以被搬移、刪除、新增 |
| 驗證失敗？ | 可設定：permission denied，或標成 compromised 再開另一套 |
| 開機變慢多少？ | i.MX6 約 10%；只檢查被碰到的檔案，跟 rootfs 大小無關 |

---

## 14. 延伸連結

- MT8189 上的 dm-verity（block 層級，跟 IMA/EVM 的檔案層級對照）：[`../verified-boot-notes/verity-boot.md`](../verified-boot-notes/verity-boot.md)
- MT8189 上的資料分區加密：[`../verified-boot-notes/dm-crypt.md`](../verified-boot-notes/dm-crypt.md)
- FIT 簽章：[`../verified-boot-notes/fit-sign.md`](../verified-boot-notes/fit-sign.md)

---

## 附：一句話總結

> **ROM 用 fuse 驗 barebox，barebox 驗整個 FIT configuration，kernel 用 IMA＋EVM 逐檔驗 rootfs。要可寫就把 EVM 改成 HMAC，HMAC 祕密用每顆 i.MX6 的 unique key 封成 blob，只有安全開機的系統解得開。**

---

## ⚠️ 待確認清單

1. 影片是 ELCE 2016 還是 ELC 2017 的錄影：口頭線索（「幾週前的監視器 DDoS」、barebox「已經 2016.10」）偏向 ELCE 2016，沒有直接證據。
2. [▶ 35:38](https://youtu.be/lkFKtCh2SaU?t=2138) i.MX25 的開機負擔「30 秒裡多 10 秒」，講者是在回想數字。

---

*筆記依據 Marc Kleine-Budde〈Verified Boot: From ROM to Userspace〉錄影（Whisper `turbo` 轉錄，54:42）與 elinux.org 上的 ELCE 2016 投影片整理。*
