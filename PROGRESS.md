# 進度

狀態：⬜ 未開始 · 📝 大綱中 · ✅ 完成 · ⚠️ 完成但有待確認項 · ⏭️ 略過 · ⛔ 卡住

階段 0 查證：2026-11-13，依據 YouTube 影片頁（`yt-dlp` 抓標題、頻道、上傳日、長度、說明欄，存 `_work/meta/<id>.json`）。官方投影片 2026-11-13 查過（見下面「投影片」欄與 `_work/slides/`）。

**逐字稿**：17 場都**沒有人工字幕**，只有自動字幕；第一次下載回 HTTP 429。不用 Whisper（使用者指示）。使用者選 (A)：間隔一段時間、一次一支、用一般方式重抓自動字幕，不繞過。

- 2026-11-13 21:3x：`fBDNqvNLxMk`（05，Bootlin 頻道）抓到了，但內容幾乎全是 `[Music]` 和亂字，不能用 → 改抓 LEE 頻道版 `ulHLt3FVE44`，第二次請求就回 429。
- 之後背景每 10 分鐘抓一支，還沒抓到第二支就停掉。
- **2026-11-13 晚使用者同意用 Whisper** → 改成 16 場全部用 openai-whisper `turbo` 轉錄（`_work/whisper/<id>.*`），純文字在 `_work/txt/NN.txt`。

| # | 演講 | 影片 ID | 長度 | 上傳日 | 標題 | 講者 | 投影片 | 狀態 | 備註 |
|---|---|---|---|---|---|---|---|---|---|
| 01 | Secure Boot on ARM systems – Building a complete Chain of Trust | MZ0PpzKPM5Q | 33:03 | 2017-09-29 | ✓ | ✓ Matteo Carlini（說明欄） | ⚠️ 只有 SlideShare（Linaro 帳號），抓不到 PDF | ⚠️ 待確認 2 | LinaroOrg，SFO17-201 |
| 02 | Arm Trusted Firmware for coreboot developers | UC35q4OJg3k | 39:22 | 2018-10-02 | ✓ | ✓ Julius Werner（標題） | ✗ osfc.io／pretalx 沒附 | ⚠️ 待確認 2 | OSFC 2018 |
| 03 | Secure boot all the way to userspace and upstream | mNC5suIlWAQ | 31:22 | 2025-01-31 | ✓ | ✓ Mikko Rapeli（標題） | ✓ `03-rapeli.pdf`（pretalx 附件） | ⚠️ 待確認 2 | Yocto Project Summit 2024.12（README 寫 Linaro／Yocto Virtual Summit） |
| 04 | Secure Boot on Arm systems | 3g-WURfbhKI | 25:26 | 2024-07-04 | ✓ | ✓ Alexandre Vicenzi（media.ccc.de/v/4521） | ✓ `04-vicenzi.pdf`（講者 Speaker Deck，檔名 oSC24） | ⚠️ 待確認 1 | openSUSE Conference 2024；media.ccc.de/v/4521 可查講者 |
| 05 | Secure boot in embedded Linux systems | fBDNqvNLxMk | 21:47 | 2021-06-18 | ✓ | ✓ Thomas Perrot（標題） | ✓ `05-perrot.pdf`（Bootlin） | ⚠️ 待確認 5 | Bootlin 頻道；同場另有 LEE 頻道 ulHLt3FVE44；**樣品** |
| 06a | Overview of Secure Boot state in the ARM-based SoCs | QtYO1vbyoN0 | 14:31 | 2024-07-04 | ✓ | ✓ Maciej Pijanowski（FOSDEM 2021 議程頁＋投影片封面） | ✓ `06a-fosdem21.pdf`（FOSDEM 2021 附件） | ✅ | 3mdeb 頻道；實為 FOSDEM 2021 Hardware-Aided Trusted Computing devroom（README 寫 ELC，不符） |
| 06b | 同上 2nd edition | jdDZst29VLo | 31:29 | 2024-07-04 | ✓ | ✓ Tomasz Żyjewski（FOSDEM 2023 議程頁＋逐字稿自我介紹） | ✓ `06b-fosdem23.pdf`（FOSDEM 2023 附件） | ⚠️ 待確認 1 | FOSDEM 2023 Open Source Firmware devroom；README 沒列；回顧第一版並加 Rockchip／MediaTek 例子，暫列入 |
| 07 | Verified Boot: From ROM to Userspace | lkFKtCh2SaU | 54:42 | 2017-04-04 | ✓ | ✓ Marc Kleine-Budde（說明欄） | ✓ `07-kleine-budde-elce2016.pdf`（elinux.org，ELCE 2016 版） | ⚠️ 待確認 2 | Linux Foundation；找到的投影片是 ELCE 2016（2016-10-12）；影片 2017-04 上傳，是 ELCE 2016 還是 ELC 2017 的錄影 → ⚠️ |
| 08 | Secure Boot from A to Z | jtLQ8SzfrDU | 49:04 | 2018-03-14 | ✓ | ✓ Quentin Schulz & Mylène Josserand | ✓ `08-schulz-josserand.pdf`（Bootlin，ELC 2018-03-13） | ✅ | Linux Foundation |
| 09 | Implementing UEFI-based Secure Boot + OTA Update for Embedded ARM Devices | H_dBnwkTAbw | 41:52 | 2022-10-08 | ✓ | ✓ Jan Kiszka & Christian Storm | ✗ sched 擋 curl，查不到 | ⚠️ 待確認 1 | Linux Foundation |
| 10 | FIT Happens: How Secure Boot Wasn't | mMlSsVGGAsI | 38:12 | 2026-11-03 | ✓ | ✓ Ahmad Fatoum | ✗ sched 擋 curl，查不到 | ⚠️ 待確認 1 | OSS＋ELC Europe 2026（sched osselceu2026；README 寫 ELC／FOSDEM） |
| 11 | Practical Application of Verified Boot | 6rGKI5KblZ4 | 42:02 | 2024-10-04 | ✓ | ✓ Rouven Czerwinski | ✗ sched 擋 curl，查不到 | ⚠️ 待確認 2 | Linux Foundation |
| 12 | Open Source Tools for Secure Boot on Rockchip RK3588 | PSEJD4Bfnyw | 13:59 | 2026-06-25 | ✓ | ✓ Michael Tretter（標題） | ✓ `12-tretter.pdf`（Embedded Recipes pretalx 附件，說明欄指路） | ✅ | BayLibre 頻道，Embedded Recipes 2026；只有 14 分鐘，README 摘要（TZC-400、PTA 等）可能言過其實 |
| 13 | Getting the RK3588 SoC supported upstream | pnIVaig-LoA | 35:01 | — | ✓ | ⚠️ 影片頁抓不到 | — | ⏭️ | **影片 not available**；搜尋只找到這支。另外主題是上游支援，不是 secure boot |
| 14 | Breaking Samsung's Root of Trust: Exploiting Samsung S10 Secure Boot | BwFtOrkKlbo | 36:36 | 2021-02-26 | ✓ | ✓ Jeff Chao（BH 投影片檔名 us-20-Chao；README 寫 G. Beniamini，錯） | ✓ `14-chao.pdf`（BH USA 2020） | ⚠️ 待確認 2 | Black Hat |
| 15 | Attacking Samsung Galaxy A* Boot Chain, and Beyond | qU9SzAo1G-s | 38:32 | 2025-03-21 | ✓ | ✓ Maxime Rossi Bellom & Raphaël Neveu（說明欄；README 寫 D. Komaromy，錯） | ✓ `15-rossi.pdf`（BH USA 2024） | ✅ | Black Hat |
| 16 | Reflections on Trusting TrustZone | 7w40mS5yLjc | 39:25 | 2015-03-19 | ✓ | ✓ Dan Rosenberg（說明欄；README 寫 Black Hat Speakers） | ✓ `16-rosenberg.pdf`＋白皮書 `16-rosenberg-wp.pdf`（BH USA 2014） | ⚠️ 待確認 1 | Black Hat USA 2014 |
| 17 | The Bugs in Your Bootloaders: Embedded Device Secure Boot Fails and How to Fix Them | eZczwNFzxus | 38:12 | 2025-05-19 | ✓ | ✓ Henrik Ferdinand Nölscher（說明欄） | ✗ BH 官網擋自動抓取（說明欄給了議程連結） | ⚠️ 待確認 1 | Black Hat |

## 範圍判斷（Claude 依 BRIEF 規則，待使用者複核）

- 列入：01–12、14–17（含 06b）。講者 ⚠️ 的幾場標題完全對上，講者等逐字稿開頭自我介紹再確認。
- 略過：13（影片無法播放）。

## 給 README 的修正建議（README 這次不改）

- 所有「YouTube 觀看」連結換成上表影片 ID。
- 03 會議、06 會議（3mdeb 而非 ELC）、07 年份／場次、16 講者 Dan Rosenberg、12 摘要過度推論、13 影片失效。
- 講者錯誤：14 是 Jeff Chao（不是 G. Beniamini）、15 是 Maxime Rossi Bellom & Raphaël Neveu（不是 D. Komaromy）、17 是 Henrik Ferdinand Nölscher；06a 是 FOSDEM 2021、06b 是 FOSDEM 2023（Tomasz Żyjewski）。
- 會議：09 推定 ELCE 2022、10 是 OSS＋ELC Europe 2026、11 是 OSS Europe 2024、14 BH USA 2020、15 BH USA 2024、17 BH Europe 2024。
- 12 的 README 摘要（TZC-400、Linux 呼叫 PTA 等）演講都沒講；演講只講到 ROM 驗 bootloader。

## 完成狀態（2026-11-13）

16 份筆記全部寫完（13 略過）。待確認共 27 項，列在各筆記最後的清單。沒有 commit。

## 階段 1 樣品：05 Perrot

**逐字稿**：Whisper turbo（`_work/txt/05.txt`，21:47）。Bootlin 頻道那支的 YouTube 自動字幕是亂字，不用。

**大綱**（2026-11-13，Claude 依 BRIEF 自行檢查後放行，記錄如下）：

0. 這場演講要做什麼（兩部分；i.MX8 實作、不用 initramfs）
1. Secure boot 在防什麼 [01:07] — p.5
2. 信任鏈與非對稱簽章 [01:42] — p.6–7
3. 開 secure boot 對工作流程的影響 [04:05] — p.8
4. i.MX8 實作全貌：每段誰驗誰 [04:43] — p.10
5. ROM 驗 bootloader：NXP AHAB [05:53] — p.11–17
   5.1 AHAB 和舊的 HAB 差在哪、兩個 container、SECO 驗證流程
   5.2 產生 PKI tree、SRK table 和 SRK hash（在解什麼／步驟／失敗）
   5.3 寫 CST 設定檔、簽 `flash.bin`
   5.4 燒 SRK hash 進 OTP、看狀態、`ahab_close` 鎖板
6. U-Boot 驗 kernel：FIT verified boot [12:56] — p.18–22
   6.1 FIT 是容器（image＋configuration）
   6.2 簽 image 還是簽 configuration：mix-and-match 攻擊
   6.3 產生金鑰、建置、把公鑰塞進 U-Boot
7. Kernel 驗 rootfs：dm-verity [17:10] — p.23–24
8. 不用 initramfs：dm-init＋FIT 裡的 boot script [19:36] — p.25
9. 一頁速查表
10. 延伸連結

檢查：骨架照逐字稿時間順序；每節都有對應投影片頁；三個工具（CST／FIT 簽章／dm-verity）都有「在解什麼／步驟／失敗或被繞過」；沒有 Q&A（講者問了「有沒有問題」，影片到此結束）。

**全文**：`05-perrot-secure-boot-embedded-linux.md`（2026-11-13）。待確認 5 項（筆記最後的清單）。Claude 依 BRIEF 檢查後當作樣品通過，同樣格式用在階段 2。

## 階段 2 批次

大綱由 Claude 依 BRIEF 自行檢查後放行（使用者以 /goal 授權）；每份筆記的目錄就是大綱。
- 01 `01-carlini-secure-boot-arm-chain-of-trust.md`：投影片只有 SlideShare 逐頁摘要（不是原文）。
- 02 `02-werner-tf-a-for-coreboot.md`：沒有投影片；主題偏 BL31/PSCI，secure boot 只在 Q&A。
- 03 `03-rapeli-secure-boot-to-userspace.md`
- 04 `04-vicenzi-secure-boot-arm-systems.md`
- 06a `06a-pijanowski-secure-boot-arm-socs-overview.md`：講者確認是 Maciej Pijanowski（逐字稿自我介紹＋投影片）。待確認 0。
- 06b `06b-zyjewski-secure-boot-arm-socs-overview-2nd.md`：講者已由逐字稿確認。
- 07 `07-kleine-budde-verified-boot-rom-to-userspace.md`：場次口頭線索偏 ELCE 2016。
- 08 `08-schulz-josserand-secure-boot-a-to-z.md`：待確認 0。
- 09 `09-kiszka-storm-uefi-secure-boot-ota-arm.md`：沒有投影片；會議名待查。
- 10 `10-fatoum-fit-happens.md`：會議＝OSS+ELC Europe 2026（sched osselceu2026）；CVE-2026-33243 來自說明欄。
- 11 `11-czerwinski-practical-verified-boot.md`：會議＝OSS Europe 2024（sched osseu2024）；沒有投影片。
- 12 `12-tretter-rk3588-secure-boot-open-source.md`：投影片後來在 pretalx API 找到。README 摘要說的 TZC-400、PTA 給 Linux 呼叫等，演講都沒講。待確認 0。
- 14 `14-chao-breaking-samsung-s10-secure-boot.md`：攻防場，不收位址／heap 利用細節。
- 15 `15-rossi-neveu-attacking-samsung-galaxy-a-boot-chain.md`：會議＝BH USA 2024（投影片檔名）；含 MediaTek 引入的 ATF 漏洞 CVE-2024-20021。待確認 0。
- 16 `16-rosenberg-reflections-on-trusting-trustzone.md`：用了白皮書。
- 17 `17-nolscher-bugs-in-your-bootloaders.md`：講者、會議（BH Europe 2024）由說明欄確認；沒有投影片。
