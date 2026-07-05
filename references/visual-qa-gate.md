# 視覺校稿閘（Visual QA Gate）· 單一事實源

> **這份文件是 social-cards 引擎「視覺校稿閘」的唯一標準本體。**
> 各消費端（SKILL.md 的 pipeline、各 brand pack 的出圖流程）只放 2-3 行指針指回這裡，
> 細則以本檔為準，避免多份漂移。
>
> （本檔源自作者跨 skill 共用的視覺校稿標準，抽出來隨引擎自包含發佈。）

---

## ① 緣起（真實事故）

一批「**通過了所有機器檢查、卻明顯壞掉**」的視覺產出，是這道閘存在的理由：

- **PPTX 標題與副標互疊**、kicker 被裝飾圓吃掉——版面靜態檢查（`design_review.py` 類）照樣 exit 0。
- **圖卡人物被切腳、切頭髮**（CTA 人物頭頂平切）——shape 座標檢查全過。

根因：**機器檢查只看 box（shape 座標 / exit code），看不見 text 溢出 box、文字互疊、圖片內容被裁**。工具說「過」不等於「好看」。這道閘就是為了讓「肉眼」成為最後一關而存在。

---

## ② 鐵律：機器檢查當篩選器、肉眼當裁判

- 機器檢查（exit 0 / shape 座標 / audit_layout / measure_balance / Playwright assert）**只是篩選器**——先擋掉明顯壞的，讓人不用看爛稿。
- **逐張渲染成圖、用肉眼看過，才算「過閘」。** 用座標級檢查替代渲染目視 ＝ gate 未跑完，一律打回。
- 產圖者自評不算數（見 ⑥ 寫審分離）。

---

## ③ 依產出類型的執行程序

### A. PPTX / 簡報

1. 先跑該專案自己的機器檢查（如 `design_review.py`），要求 0 issue —— 這只是**入場券**。
2. 轉圖：
   ```bash
   soffice --headless --convert-to pdf --outdir . "<輸出>.pptx"
   # 再把 pdf 轉 png（pymupdf 或 pdf2image）
   ```
   `soffice`（LibreOffice）多在 `/opt/homebrew/bin`（`which soffice` 可驗）——**「本機沒有 LibreOffice」不成立時，不准用這句跳過。**
3. **全數逐張 `Read` 目視**（不是抽樣），對照 ④ 通用 checklist。逐張看完才算過。

### B. 圖卡 / PNG（social-cards、carousel、輪播）

1. **逐張 `Read`＋zoom**：放大標題區（明體非 fallback）與人物區。
2. 每張確認：文字無互疊、無被裝飾元素（圓 / blob / flame / bar）壓住、卡片內容無溢出底部、中英斷行正常。
3. **人物卡加驗**：zoom 頭髮 / 手指 / 鞋子完整；人物「出血」只允許刻意貼齊畫布邊，禁止懸空切一半。
4. 人物 / 圖像資產使用前先跑 ⑤ 的 alpha 貼邊檢查。

### C. HTML deck / 原型

1. Playwright 截圖，或跑版面均衡兩腳本（`audit_layout` / `measure_balance`）。
2. 機器過關後**肉眼覆核截圖**——同鐵律，機器只篩、眼睛裁。
3. 固定尺寸 deck / 海報 / infographic 特別注意跑版（overflow / overlap / clipping）與留白過散。

---

## ④ 通用 checklist（每張逐項）

- [ ] 文字**無互疊**（標題不壓副標、不壓 kicker）
- [ ] 文字**未被裝飾元素壓住**（圓 / blob / flame / dot-grid / bar 之下無字）
- [ ] 內容**無溢出**卡片 / 畫布底部
- [ ] 中英**斷行正常**，無怪異切斷、無孤字
- [ ] **人物頭髮 / 手指 / 鞋子完整**，無被畫布邊平切（除非刻意貼齊出血）
- [ ] **臉部特徵對照源圖完整**——把資產臉部 zoom 與 `_origin` 源圖同一 cell 並排，逐點對：**瞳孔×2（含遠側/被眼白包圍的那顆）／眉×2／嘴／鏡框**不得缺。⚠️ 事故先例：切圖的「移除浮動斷片」把「被白眼白包圍的孤立深色瞳孔」誤當碎片刪，一整批人物遠側瞳孔全空、機器白暈/貼邊閘全過卻沒抓到——閉眼姿勢無此風險，睜眼一律逐顆點名。機器側對應閘＝asset_prep 的 content-preservation（見 ⑤）。
- [ ] **對比可讀**（深底不放深字、赤陶不壓赤陶）
- [ ] **標題是明體**（或指定字體），非 system font fallback（豆腐字 / 細線字）

---

## ⑤ 人物與圖像資產貼邊＋白暈檢查（規格本體；程式碼權威在 halo_check.py）

> **程式碼權威源＝`scripts/halo_check.py`**（含「貼邊」與「殘白」兩子檢查）。本節只留**語意規格**，不再內嵌可執行碼（避免與腳本雙寫漂移）。
> **入庫時** `scripts/asset_prep.py` 會自動跑 halo_check 並把結果寫進 `brands/<brand>/assets/manifest.json` 的 `qa` 節點；**臨時手驗單張** 執行 `python3 scripts/halo_check.py --input <png> --alpha-only`（只跑貼邊）或不帶 `--alpha-only`（貼邊＋多底色白暈全跑）。入庫閘全貌見 `SKILL.md`「🗂 資產入庫閘」。

判定規格（供腳本實作與人工覆判對照）：

- **貼邊（alpha padding）**：量去背 RGBA 資產不透明像素的 alpha bbox 四邊距，**任一邊 < 4px ＝ 資產本身已被裁**（放進版面前就缺角）→ FAIL，先修資產再用。**貼邊只驗 master；等比 derivative 不重驗**——等比縮放不會新增裁切，故 derivative 帶 `--skip-pad` 只驗白暈＋孤島。
- **不透明孤島（opaque islands）**：偵測 a≥250、亮度>200、中性（近白／淺灰、非人物主色）且「漂浮於透明背景」（周圍環帶透明佔比高，有別於嵌在人物內的襯衫／眼白）的孤立連通區——向量化凹陷區殘留或裁切斷片。**任一面積 > 10px 的孤島 ＝ 結構性缺陷 → FAIL（不給 WARN）**。asset_prep 於 vectorize 渲染時以同一判準幾何摳除（連亮中性 AA 外緣一併清、保留黑描邊）。
- **白暈（多底色合成殘白）**：把資產合成到 navy `#14233B` / 白 / 橘紅三底色，量輪廓外邊界帶亮度異常像素比例（取 `max(navy%, orange%)`；白底對白暈天生不敏感，只作對照不判定）。**PASS `< 15%` ／ WARN `15–25%`（人工 zoom 四點位覆判）／ FAIL `≥ 25%`（打回重去背）**。
- **內容保全（content-preservation）**：入庫時 asset_prep 拿「源 cell 內部前景（erode 2px 去邊）」比對「master 不透明覆蓋」，把損失像素 label 成連通塊。**最大一塊 > 30px（＝整顆瞳孔/高光級特徵被抹掉）→ FAIL**；全域損失 % 僅輔助紀錄。⚠️ 關鍵：不可只用「總前景 % 損失」當門檻——一顆瞳孔只佔全身前景 0.2–0.4%，會被 0.5% 全域門檻放過（正是那次瞳孔事故的漏網主因），必須用「連通塊」尺度無關判據。切圖側（sheet_cut.py）另記 `interior_fg_lost`（輪廓內損失須=0）＋輪廓外移除清單。
- **底色無關輔助判準**：邊界帶自身 RGB 亮度中位數 **`fg_edge_lum > 120` 觸發 WARN**——即使合成幾何剛好遮住暈，只要邊緣像素近白（污染未清）仍示警。
- **人工覆判**：貼邊/白暈機器過關不代表邊乾淨——WARN 或人物卡須把資產合成到實際深色純底、zoom ≥2x 檢查輪廓一圈（髮頂／手指／鞋底／外緣四點），出現一圈白暈即未過。成因＝邊緣抗鋸齒半透明像素 RGB 混白未去污染；根治要「白 matte 反解 alpha ＋ unpremultiply 去污染」從原圖重做，不可在已壞 alpha 上疊修。

> 門檻基準（U3 校準，flat 卡通粗描邊風格）：現況一批 17 張 halo 2.82–7.85%、陽性對照 59.92%，分離帶 7.6×。換品牌／換畫風（尤其大面積白色服裝）建議重跑分佈再確認 15% 是否適用。

---

## ⑥ 寫審分離

- **校稿由「產圖之外的 pass」執行**：不同一次對話 / 獨立 agent。
- 產圖者自評不算數（同源自評放水，同 maker/verifier 分離原理）。
- 校稿者只判 PASS / FAIL + 逐張證據，改是回去給產圖者改。
- **provenance 追溯必到 `_origin`，不可信任中間產物**：驗「這張切對了沒」要比對 `source/_origin/` 的真源 sheet（唯讀證據層），**不是** `source/<id>/raw.png`——那是切圖流程自己產的中間 cut cell，跟成品同源自證等於沒驗。⚠️ 事故先例：某輪 verifier 拿中間 raw 當源頭比，誤判「源頭就這樣」，放過了瞳孔誤刪。manifest `provenance.source_file` 一律指 `_origin`＋`cell_bbox_on_sheet`，中間 cut cell 記在 `provenance.cut_cell`。

---

## ⑦ 工具引用

| 工具 | 用途 | 定位 |
|---|---|---|
| `design_review.py`（各 pptx 專案自帶） | shape 座標 / 版面靜態檢查 | 篩選器 |
| 版面均衡 `audit_layout` | 抓 HTML deck 跑版（overflow / overlap / clipping） | 篩選器 |
| 版面均衡 `measure_balance` | 量留白 / 太散 | 篩選器 |
| `carousel-joker` 品質閘（本 repo `skills/carousel-joker/`） | 輪播圖卡品質對抗審查 | 篩選器＋建議 |
| Playwright 截圖 / assert | HTML 原型渲染與互動驗證 | 篩選器 |
| **肉眼逐張 Read＋zoom** | 互疊 / 壓字 / 裁切 / 對比 | **裁判（最終關）** |

> 所有機器工具都只在「篩選器」欄，沒有任何一個能取代肉眼逐張。

---

## ⑧ 重要交付：加跑設計 skill 5 維專家評審

風格大改版、新模板 / 新 style pack 首用、或對外重要交付：在上述肉眼校稿之外，**加跑設計 QA skill**（如安裝了 `huashu-design`）——反 AI slop checklist ＋跑版五項；重要交付再跑 **5 維專家評審**（哲學一致性 / 視覺層級 / 細節執行 / 功能性 / 創新性 各 10 分 + 修復清單）。沒裝也可用本檔 ④ checklist 手動逐項過。

---

## 一句話總結

**機器 exit 0 只是入場券；逐張渲染成圖、肉眼看過、由產圖之外的 pass 判過，才算過閘。**
