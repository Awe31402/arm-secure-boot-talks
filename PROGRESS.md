# 進度

狀態：⬜ 未開始 · 📝 大綱中 · ✅ 完成 · ⚠️ 完成但有待確認項 · ⏭️ 略過 · ⛔ 卡住

階段 0 查證：2026-11-13，依據 YouTube 影片頁（`yt-dlp` 抓標題、頻道、上傳日、長度、說明欄，存 `_work/meta/<id>.json`）。研討會議程頁、官方投影片**還沒查**。

**逐字稿**：17 場都**沒有人工字幕**，只有自動字幕；第一次下載回 HTTP 429。不用 Whisper（使用者指示）。使用者選 (A)：間隔一段時間、一次一支、用一般方式重抓自動字幕，不繞過。

| # | 演講 | 影片 ID | 長度 | 上傳日 | 標題 | 講者 | 狀態 | 備註 |
|---|---|---|---|---|---|---|---|---|
| 01 | Secure Boot on ARM systems – Building a complete Chain of Trust | MZ0PpzKPM5Q | 33:03 | 2017-09-29 | ✓ | ✓ Matteo Carlini（說明欄） | ⛔ | LinaroOrg，SFO17-201 |
| 02 | Arm Trusted Firmware for coreboot developers | UC35q4OJg3k | 39:22 | 2018-10-02 | ✓ | ✓ Julius Werner（標題） | ⛔ | OSFC 2018 |
| 03 | Secure boot all the way to userspace and upstream | mNC5suIlWAQ | 31:22 | 2025-01-31 | ✓ | ✓ Mikko Rapeli（標題） | ⛔ | Yocto Project Summit 2024.12（README 寫 Linaro／Yocto Virtual Summit） |
| 04 | Secure Boot on Arm systems | 3g-WURfbhKI | 25:26 | 2024-07-04 | ✓ | ✓ Alexandre Vicenzi（media.ccc.de/v/4521） | ⛔ | openSUSE Conference 2024；media.ccc.de/v/4521 可查講者 |
| 05 | Secure boot in embedded Linux systems | fBDNqvNLxMk | 21:47 | 2021-06-18 | ✓ | ✓ Thomas Perrot（標題） | ⛔ | Bootlin 頻道；同場另有 LEE 頻道 ulHLt3FVE44；**樣品** |
| 06a | Overview of Secure Boot state in the ARM-based SoCs | QtYO1vbyoN0 | 14:31 | 2024-07-04 | ✓ | ⚠️ 影片頁未列講者（README 寫 Maciej Pijanowski） | ⛔ | 3mdeb 頻道（README 寫 ELC，不符） |
| 06b | 同上 2nd edition | jdDZst29VLo | 31:29 | 2024-07-04 | ✓ | ⚠️ 同上 | ⛔ | README 沒列；回顧第一版並更新，暫列入 |
| 07 | Verified Boot: From ROM to Userspace | lkFKtCh2SaU | 54:42 | 2017-04-04 | ✓ | ✓ Marc Kleine-Budde（說明欄） | ⛔ | Linux Foundation；上傳日推斷 ELC 2017（北美），README 寫 ELC Europe → ⚠️ |
| 08 | Secure Boot from A to Z | jtLQ8SzfrDU | 49:04 | 2018-03-14 | ✓ | ✓ Quentin Schulz & Mylène Josserand | ⛔ | Linux Foundation |
| 09 | Implementing UEFI-based Secure Boot + OTA Update for Embedded ARM Devices | H_dBnwkTAbw | 41:52 | 2022-10-08 | ✓ | ✓ Jan Kiszka & Christian Storm | ⛔ | Linux Foundation |
| 10 | FIT Happens: How Secure Boot Wasn't | mMlSsVGGAsI | 38:12 | 2026-11-03 | ✓ | ✓ Ahmad Fatoum | ⛔ | Linux Foundation（README 寫 ELC／FOSDEM，會議名待查） |
| 11 | Practical Application of Verified Boot | 6rGKI5KblZ4 | 42:02 | 2024-10-04 | ✓ | ✓ Rouven Czerwinski | ⛔ | Linux Foundation |
| 12 | Open Source Tools for Secure Boot on Rockchip RK3588 | PSEJD4Bfnyw | 13:59 | 2026-06-25 | ✓ | ✓ Michael Tretter（標題） | ⛔ | BayLibre 頻道，Embedded Recipes 2026；只有 14 分鐘，README 摘要（TZC-400、PTA 等）可能言過其實 |
| 13 | Getting the RK3588 SoC supported upstream | pnIVaig-LoA | 35:01 | — | ✓ | ⚠️ 影片頁抓不到 | ⏭️ | **影片 not available**；搜尋只找到這支。另外主題是上游支援，不是 secure boot |
| 14 | Breaking Samsung's Root of Trust: Exploiting Samsung S10 Secure Boot | BwFtOrkKlbo | 36:36 | 2021-02-26 | ✓ | ⚠️ 影片頁未列講者（README 寫 G. Beniamini et al.，可疑） | ⛔ | Black Hat |
| 15 | Attacking Samsung Galaxy A* Boot Chain, and Beyond | qU9SzAo1G-s | 38:32 | 2025-03-21 | ✓ | ⚠️ 影片頁未列講者（README 寫 D. Komaromy） | ⛔ | Black Hat |
| 16 | Reflections on Trusting TrustZone | 7w40mS5yLjc | 39:25 | 2015-03-19 | ✓ | ✓ Dan Rosenberg（說明欄；README 寫 Black Hat Speakers） | ⛔ | Black Hat USA 2014 |
| 17 | The Bugs in Your Bootloaders: Embedded Device Secure Boot Fails and How to Fix Them | eZczwNFzxus | 38:12 | 2025-05-19 | ✓ | ⚠️ 影片頁未列講者 | ⛔ | Black Hat |

## 範圍判斷（Claude 依 BRIEF 規則，待使用者複核）

- 列入：01–12、14–17（含 06b）。講者 ⚠️ 的幾場標題完全對上，講者等逐字稿開頭自我介紹再確認。
- 略過：13（影片無法播放）。

## 給 README 的修正建議（README 這次不改）

- 所有「YouTube 觀看」連結換成上表影片 ID。
- 03 會議、06 會議（3mdeb 而非 ELC）、07 年份／場次、16 講者 Dan Rosenberg、12 摘要過度推論、13 影片失效。
