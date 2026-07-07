---
name: social-cards
description: 品牌無關的 IG/Threads/X/FB 圖卡引擎——把任何主題（idea / 文章 / 教學）變成輪播圖卡 + 4 平台文案。HTML+CSS 模板 → Chrome headless 渲染 PNG。風格由 brand pack 決定（brands/），接哪個 pack 出哪個風格，引擎不綁死品牌。觸發詞：做圖卡、生 carousel、social card、IG 圖卡、Threads 卡片、貼文文案、教學圖卡、infographic、輪播圖、carousel post。
---

# social-cards · 品牌無關的圖卡引擎

把任何主題（idea、文章、教學、案例）變成一排 IG／Threads／FB 輪播圖卡 + 4 平台文案。

## 🧩 架構：引擎 vs 品牌插件

> **核心觀念**：這個 skill 是**品牌無關的圖卡引擎（tool）**——負責結構、渲染、擴散規則。
> 「長什麼樣、什麼配色、什麼調性」由 **brand pack（品牌插件）** 決定。接哪個 pack → 出哪個風格。
> 一套引擎服務多品牌，各自不同風格，引擎不變。

- **品牌路由**：先看 `brands/README.md`（註冊表）。要用哪個品牌 → 載 `brands/<brand>/brand.md`；沒 pack 就先建一個（見 brands/README 的新增步驟）。
- **引擎不綁品牌**：`templates/*`（navy/warm/morandi）只是**通用起手模板**，不是「某個人的固定風格」。幫別的品牌時用該品牌 pack。

## 🚀 首次使用：選預設 or 對話共創你的風格（安裝完就能開始，使用者不寫 Python）

> **這是 Claude 讀的 skill，不是要使用者手動跑的 CLI。** 使用者只要說「用 social-cards 幫我做圖卡」，Claude 就照下面走。Python + Chrome 只是**渲染那步 Claude 自己會呼叫的相依工具**，使用者全程用「講」的。

使用者第一次用（還沒有自己的 brand pack）時，**先問要走哪條**：

- **A · 用預設風格（最快）**：直接挑一套通用模板 pack（navy 海報 / 暖色 Morandi / 暖大地 ELI5 / meme 鄉民）開始出圖。
- **B · 建立你自己的風格（像 Claude Design 那樣共創）** ← 使用者要的核心體驗。跟使用者對話，把「風格」談出來、寫成 brand pack。兩種輸入擇一或並用：
  1. **對話式訪談**：問品牌名 / 受眾 / 色感 / 字體感 / 語氣 / 有沒有 logo・頭像・產品照（走 `huashu-design` 核心資產協議）→ 邊給假設邊確認 → 定稿。
  2. **給樣本自動萃取**：使用者貼幾篇自己的貼文 / 官網 / 簡報 → Claude 拆解出**配色 + 語氣 DNA** → 寫成 `brand.md`（now6pm、thankyounuts 就是這樣長出來的）。
  → 產出 `brands/<你的品牌>/brand.md`（＋ 從最接近的 pack 複製 `render_template.py` 微調）。之後每次出圖都載這個 pack。
- **C · 已經有 pack**：直接載入用。

> 一句話：**安裝完 → 跟 Claude 聊 → 選預設或共創風格 → 對焦一張封面卡確認「要長這樣嗎」 → 量產出圖 → joker 審**。使用者不碰 Python，那是引擎內部渲染在跑。（對焦那步見下方「🎨 設計對焦閘」。）

### 📥 資產索取規格（onboarding 時給客戶／品牌窗口的話術，可直接複製）

> 新品牌 onboarding 要先跟窗口要對的原始檔，才不會下游一直修白暈。以下白話文案（無術語）可直接複製貼給非技術窗口：

> **「為了讓您的品牌人物／logo 在我們每一張貼文（不管背景是深藍、白色還是橘紅）邊緣都乾淨俐落、不會出現一圈毛毛的白邊，麻煩您提供以下任一種原始檔，我們就能一勞永逸：(1) 最理想——去背的透明 PNG，寬度至少 1500 像素（檔名通常會標 transparent 或背景是格子狀的）；(2) 或是當初的 AI 原始檔／設計原稿（例如 Illustrator 的 .ai、.svg，或 Photoshop 分層的 .psd）；(3) 真的都沒有的話，給我們解析度越高越好的原圖也行，我們這邊會幫忙去背，但成品會請您過目確認。請避免直接從網頁、IG 截圖或 Word/PPT 裡複製出來的小圖——那種放大會糊、去背會有殘影。若品牌有自有角色，見下方 🎭 品牌角色包引導。」**

### 🎭 品牌角色包引導（企業／品牌／KOL 自有角色）

> 品牌若有自己的吉祥物／代言角色，用「角色主圖＋8 表情 sheet＋8 動作 sheet」三件套，就能讓人物融入每一張圖卡。品牌只需照下方標準 prompt 產圖回傳，最終品質由「🗂 資產入庫閘」保證。

**流程說明（給品牌窗口）：**
1. 品牌先把角色繪製定稿（一張清楚的人物圖即可）。
2. 用下方**標準 prompt**＋那張角色圖，丟給 GPT／Gemini 生成三件套（角色定稿透明底、8 表情 sheet、8 動作 sheet）。
3. 把三張圖回傳給我們。
4. 走「資產入庫閘」（`scripts/asset_prep.py`／`scripts/halo_check.py`／`scripts/sheet_cut.py`），把角色融入圖卡。

**標準 prompt（一字不改照貼給 GPT／Gemini）：**

```
請根據我上傳的人物圖片，幫我生成同一個角色的三張透明底 PNG 圖：角色定稿透明底、角色表情參考 sheet、角色動作參考 sheet。

請務必讓角色樣貌、髮型、五官、眼鏡、服裝、顏色、比例、線條風格都盡量和我上傳的人物一致。風格保持簡單、乾淨、線條清楚，不要增加太多細節，方便後續拿去做影片或圖片生成。

背景請完全透明，不要白底、不要灰底、不要任何背景色。請不要用白底去背的方式處理，請直接生成透明背景版本。透明區域只能是角色外部背景。角色眼睛的眼白必須保留白色，不要透明。角色內部的白色區域，例如眼白、白襯衫、牙齒、文字等，都要保留為不透明白色。角色外輪廓邊緣請乾淨，不要留下白邊、灰邊或半透明髒邊。

第一張：角色定稿透明底
產出一張單一角色的放大版，正面面對鏡頭，表情友善，姿勢可以沿用原圖姿勢或改成適合教學／介紹的姿勢。只保留角色本體，透明背景。

第二張：角色表情參考 sheet
產出同一角色的 8 種表情，排列成 2 排 × 4 格：開心微笑、大笑、生氣、難過／哭泣、驚訝、害羞／尷尬、思考／困惑、自信／堅定。每一格角色樣貌都要一致，不要變成不同人。可以有簡單輔助符號，但不要太複雜。

第三張：角色動作參考 sheet
產出同一角色的 8 種動作，排列成 2 排 × 4 格：揮手打招呼、比讚、指向上方、指向旁邊、歡呼、走路、禮貌鞠躬、雙手插腰自信站立。每一格角色樣貌都要一致，不要變成不同人。動作清楚、簡單，不要過度複雜。
```

**收件驗證流程（收到三張後必做 checklist）：**
- [ ] **真透明檢驗**：對每張跑 PIL 檢查——`mode == "RGBA"` 且**外部背景** alpha≈0。⚠️ **ChatGPT 網頁版大概率給假透明（把棋盤格「畫」進 RGB 像素），Gemini 同**。假透明／白底＝**正常情況，不用退件**，直接走 asset_prep 修補路線。
- [ ] **分流**：真透明 → native-alpha 路線直接入庫（asset_prep 跳過修補）；假透明／白底 → repair 管線（自動去背＋機器 QA）。
- [ ] **sheet 切格**：用 `scripts/sheet_cut.py` 切 2×4（silhouette fill-holes，保全瞳孔等內部特徵，不被當背景挖穿）。
- [ ] **全部過閘**：`halo_check`（多底色合成零白暈）＋內容保全 diff（切格前後角色本體不變）＋臉部特徵對照源圖（8 格不能變成不同人），最後寫 `manifest.json`。
- [ ] **提醒品牌**：無論走哪條，最終品質由入庫閘保證——品牌只要照 prompt 產圖即可，假透明／白邊我們這端會處理。

## 🤝 推薦搭配 skill（偵測到有裝就自動借力，沒裝也能獨立跑）
- **`huashu-design`**（HTML 設計 skill）：**兩頭都用**——① **量產前的設計對焦**（產封面卡樣跟使用者確認「要長這樣嗎」，見「🎨 設計對焦閘」）；② **渲染後的版面 QA**（圖片置中不變形、留白節奏、跑版／溢出檢查、IG 排版）。建 brand pack 的「核心資產協議」也用它。
- **`social-post`（Hao0321）**：**2026 演算法訊號權重**（私訊分享 sends > 收藏 saves > 讚）＝本引擎擴散規則的來源；還有**半自動發文**（FB／IG／Threads）＋ 學使用者貼文語氣。**要診斷擴散、要發文、要學語氣就用它**（見 `references/knowledge_carousel_rubric.md` 已內建其權重摘要）。
- 沒裝這兩個 → 引擎照內建 rubric + joker 獨立跑，只是少了版面 QA 與一鍵發文。

## 🗂 資產入庫閘（品牌人物/logo/去背圖進管線前必過）

> 任何品牌資產（人物、logo、去背圖）進 social-cards 管線前，先過**入庫閘**，保證任何底色上零白暈、零裁切、可重複、機器可驗。（實戰沉澱自 now6pm 兩次白暈事故：切腳→白暈的供應鏈級根治。）
> 程式碼權威＝`scripts/asset_prep.py`（入庫）＋`scripts/halo_check.py`（判定，含 alpha 貼邊子檢查與多底色合成）；每張資產的判定結果寫進 `brands/<brand>/assets/manifest.json`。判定門檻的語意規格見 `references/visual-qa-gate.md` §⑤（單一事實源，不在此雙寫數字）。

### 決策樹（資產怎麼來→走哪層）

```
新資產需求
├─ AI 生成新角色/圖 → 首選 OpenAI API gpt-image-1.5 + background=transparent（真 alpha，$0.009-0.133/張）
│   ⚠️ 鎖 1.5：gpt-image-1 於 2026-10-23 停用；gpt-image-2 官方明確不支援透明（倒退）
│   ⚠️ 需 OpenAI API key＋花錢 → 每次用前過人工閘確認
├─ ChatGPT 網頁版生的（現行習慣）→ 視為白底圖：prompt 尾加 "on a pure white background"、
│   禁提 transparent（會畫假棋盤格）、下載存 PNG → 走修補層
├─ 客戶提供 → 照索取規格要：①透明 PNG ≥1500px ②AI/設計原檔(.ai/.svg/.psd) ③高解析原圖（走修補）
├─ flat 卡通/logo（乾淨白底源）→ 向量化母檔：vtracer 預設參數（禁高 color_precision，會產 fringe）
│   → 移除首個背景 path → SVG master → rsvg-convert 按需出 PNG（python-pptx 不吃 SVG，必留此步）
│   ⚠️ 禁餵壞 alpha 圖進向量化（垃圾進、更糟出）
└─ 白底/雜背景點陣（不得已）→ 修補層 asset_prep：背景連通區偵測→alpha ramp→unpremultiply 去污染
    （AI matting 對 flat art 過殺；真要 AI 用 BiRefNet MIT/rembg，需 Python 3.11 venv；棄 u2net 會切腳）
```

### 目錄規範（每個 brand pack 內）
- `source/` — 原檔・唯讀・永不覆寫（供應鏈證據層：客戶原圖／ChatGPT 產出／官網下載）。
- `master/` — 母檔・權威版本：flat 卡通/logo 向量化後的 `master.svg`（優先），或 ≥1500px 透明底高解析 `master.png`。
- `derived/` — 末端產物・可從 master 重生，內含 `qa/`（halo_check 自動輸出的多底色合成驗證圖 + report）。
- `manifest.json` — 全品牌單一機器可讀事實源，記每張資產的來源(provenance)／處理法(processing)／QA 結果(qa)。brand.md 只記使用規則、不抄 QA 數字（避免雙寫）。

### 入庫流程（一行版）
`source（存原檔＋provenance）→ 判型（asset_prep --route auto）→ 處理（native-alpha 跳過／vectorize 出 SVG／repair 修補）→ halo_check（多底色合成＋alpha 貼邊，PASS/FAIL）→ 肉眼覆判（zoom 四點位：髮頂/手指/鞋底/衣緣，見 references/visual-qa-gate.md §③B）→ 寫 manifest qa 節點（checked_by=獨立 verifier，寫審分離）`。機器閘只是入場券，肉眼逐張仍是裁判。

## 🖼 圖片來源與自動找圖（版權優先・附出處・交使用者定奪）

> 需要真實照片（知識卡情境圖、封面配圖）或迷因模板時，**引擎自己會找圖**——但守三條鐵則：
> **① 版權優先**（先抓 CC／公眾領域）**② 永不靜默使用**（每張附來源／授權／作者，交使用者挑）**③ 迷因例外走版權提醒**。
> 工具＝`scripts/fetch_image.py`（純標準庫、零安裝、免金鑰即可跑）。

### 決策樹（要什麼圖 → 走哪個來源）

```
需要圖
├─ 真實照片 / 情境圖 / 封面配圖
│   ① 首選：Openverse（CC/PD）→ 不夠再 Wikimedia Commons（PD/CC）  ← 免 key、版權友善
│       python3 scripts/fetch_image.py "keyword(英文命中率高)" --count 3 --out <專案>/assets/fetched
│   ② 想要更精緻的攝影圖 → Unsplash / Pexels（需免費 API key，走環境變數）
│       --source unsplash   （export UNSPLASH_ACCESS_KEY=... 才有）
│   ③ 前兩者都找不到理想的 → 用 WebSearch 找，挑到後：
│       python3 scripts/fetch_image.py --url "<圖片URL>" --credit "作者·來源頁·授權" --out ...
│       （WebSearch 撿到的圖版權未定，一律附出處交使用者判斷是否可用）
├─ 迷因模板 → imgflip 乾淨模板（免 key），抓完**必印版權提醒**
│       python3 scripts/fetch_image.py "drake" --meme --out brands/meme/memes
│       ⚠️ 個人非商用風險較低；品牌／客戶案改自繪原創或買授權（meme-joker 會擋版權梗）
└─ 品牌 logo / 吉祥物 / 產品照 → 不是「找圖」，走上面「🗂 資產入庫閘」跟窗口索取原檔
```

### 鐵則（Claude 出圖前必守）
1. **版權優先**：預設 `--source auto`（Openverse→Wikimedia，全是可標註的 CC/PD）。付費攝影站當升級選項、不是預設。
2. **選圖不替使用者拍板**：`fetch_image.py` 一次抓一排候選、寫 `fetch_manifest.json`（來源／頁面／授權／作者／標註句）並印清單。**把候選＋出處回報給使用者挑**，或讓他說「換來源／換關鍵字」。不要自己選一張就套上去。
3. **每張採用的圖，出處要能回溯**：採用後把該圖的授權／作者／標註句記到專案（社群文案的「圖片來源」或 brand pack manifest），需標註的（如 CC BY）就在貼文附上。
4. **迷因＝先給出處再讓使用者決定是否上**：抓到的梗圖模板一律附「來源＋版權未定提醒」，由使用者決定要不要用、要不要換自繪版；品牌案直接走原創／授權。
5. **抓來當「品牌固定資產」的圖（人物／logo）仍要過「🗂 資產入庫閘」**；只當單次卡片配圖的照片，附出處即可、不必入庫。

## 🎨 設計對焦閘（Step 0.5 · 先用 huashu-design 對焦風格，確認後才量產）

> **量產之前先對焦。** 使用者一講風格（選預設 / 描述 / 給樣本），別急著渲整套 8–12 張——
> 先用 `huashu-design` 產「一張封面卡樣」跟使用者確認「**要長這樣嗎**」，過了才鎖進 brand pack、才量產其餘卡。
> 為什麼：風格錯了，量產完＋審完才發現＝全部打掉重做（本引擎最痛點）。一張卡的對焦成本，換掉一整輪重渲。

### 何時跑 / 何時跳過
- **跑**：新品牌、新風格、使用者還沒有鎖定 pack，或明講「想換個樣子」。
- **跳過**：已有鎖定的 brand pack（回頭客同風格續做）——已對焦過，直接量產，別每次都問。

### 路由（依風格已定義程度）
| 使用者給的 | 對焦方式 |
|---|---|
| 模糊 /「幫我決定」 | huashu **設計方向顧問模式**：2–3 個差異化方向的封面 mockup → 使用者選 1 |
| 有描述 / 給了樣本（貼文・官網・簡報） | huashu 產 **1 張封面 hi-fi mockup** → 確認 or 用 Tweaks 即時切配色/字體/元素微調 |
| 選了預設 pack | 直接用引擎渲該 pack **一張真封面卡** → 快速確認（輕量，預設已定義好） |

> **沒裝 huashu-design？對焦閘照跑**（huashu 是選用伴生 skill，不隨本 repo 打包）：跳過第 1 段的 huashu 發散，直接用引擎渲一張真封面卡（下方第 2 段）當「要長這樣嗎」的樣，或 Claude 自己用純 HTML 快速 mockup。要裝：`bash scripts/install_companions.sh`（從官方 repo 裝；⚠️ huashu 為 alchaincyf/花叔 Personal Use License，個人免費、公司/客戶交付/商用須另外取得授權）。

### 兩段式（發散便宜、定版精準）
1. **發散（huashu，便宜可迭代）**：HTML 原型／方向板，收斂「**模板 + 元素 + 風格**」三件——配色 hex、字體感、版型骨架、必用裝飾元素。即時切 variant 讓使用者從「大概」收斂到「就是這個」。
2. **定版（引擎，所見即所得）**：用 social-cards 引擎**真的渲一張封面卡**（1080×1350，真字體/真尺寸/真品牌裝飾）→ 問「**要長這樣嗎？**」。**過了才進量產**；不過 → 回第 1 步微調。
   - 單卡渲染：既有 `render_template.py` 吃 argv 只渲一張（例 `python3 render_template.py m1_cover`），不必新腳本。

### 鎖定（對焦定稿 → 寫進 brand pack）
確認後把定稿的 **色票 hex / 字體 / 版型 variant / 必用裝飾元素** 寫進 `brands/<brand>/brand.md`（單一事實源）。這次量產與未來續做都依它——brand pack 從「憑感覺配色」升級成「有視覺定稿背書」。

### 三閘分清（別混為一談）
| 閘 | 問什麼 | 時機 | 誰判 |
|---|---|---|---|
| **設計對焦（本節・新）** | 方向 / 樣子對不對 | 量產**之前** | 使用者拍板 |
| **視覺校稿（Pipeline 4.5）** | 有沒有跑版 / 切壞 | 量產**之中**（每張渲完） | 獨立肉眼 pass |
| **joker 擴散（Pipeline 末）** | 會不會擴散 / 好不好笑 | 量產**之後** | 獨立審稿員 |

> 對焦＝方向對不對；校稿＝有沒有做壞；joker＝會不會紅。三個都保留，各司其職。

## Pipeline

> **新風格 / 新品牌**：先過上方「🎨 設計對焦閘」確認封面卡樣、鎖進 brand pack，再進下面量產（已鎖定 pack 可跳過）。

1. **確認主題 + 拆 N 張卡**：主題核心句、拆幾張（知識型建議 8–10）、CTA、每張標題(≤12字)+描述。
2. **選 brand pack**：載入配色/字體/尺寸/母題/敘事 DNA。
3. **寫 render 腳本**：複製 pack 的 `render_template.py`，改 `CARDS` 陣列（每張 dict：name / content / tag）。
   - **要真實照片 / 迷因？** 先跑 `scripts/fetch_image.py` 抓候選（版權優先、附出處），把清單回報使用者挑定後再填進模板——見上面「🖼 圖片來源與自動找圖」。
4. **渲染**：Chrome headless 截圖：
   ```python
   subprocess.run([CHROME, "--headless=new", "--disable-gpu",
     "--allow-file-access-from-files", "--force-device-scale-factor=2",
     f"--window-size=1080,1350", f"--screenshot={png}", f"file://{html}"])
   ```
4.5. **視覺校稿閘（必過，不可跳過）**：每張 PNG 渲染完必做，全過才進下一步。細則見單一事實源 `references/visual-qa-gate.md`（§③B 圖卡程序 + §④ checklist + §⑤ 貼邊＋白暈規格 + §⑥ 寫審分離）。標題級摘要：
   - **逐張 Read＋zoom**：標題（明體非 fallback）、文字無互疊/無被裝飾元素壓住、卡片無溢出、斷行正常、對比可讀。
   - **人物卡加驗**：頭髮/手指/鞋子完整；出血只允許刻意貼齊畫布邊，禁止懸空切一半。人物資產須先經「🗂 資產入庫閘」，使用時讀 `manifest.json` 的 `qa` 節點確認 PASS。
   - **寫審分離**：校稿由產圖之外的獨立 pass 執行，產圖者自評不算數。機器檢查（座標/exit code）只當篩選器，肉眼當裁判。
5. **過閘（寫審分離・自動不問）**：圖卡出完**一律自動**丟給 `carousel-joker`（知識型）或 `meme-joker`（迷因型）逐條 PASS/FAIL → 改 → 收斂。**不問使用者要不要驗，直接驗、直接修。**
   - **迭代上限（防無停止條件空轉）**：**最多 3 輪**；3 輪仍有 FAIL、或連續 2 輪無改善 → **停止自動修、標記「未過閘」上報使用者裁決，不自動放行**。gate 就是 gate，別「取最高分」矇混，也別無限重跑燒 token。
6. **寫 4 平台文案** `social_captions.md`（每平台一個 code block，copy-paste 友善）。文案完成後過 `references/de-ai-rubric.md`（去 AI 味閘門，寫審分離）：§1 機械層全套 + §2 走分支 A 克制 + §3 P7 自檢；輪播另疊加 `references/knowledge_carousel_rubric.md` 結構規則。

## 尺寸與擴散（知識型）
- 尺寸：知識型輪播 **4:5（1080×1350）**佔版面最大；快速方形貼可 1:1。
- 張數：8–12 張（一圖一觀念）。
- 擴散：對著 **sends（私訊分享）> saves（收藏）> likes** 設計——封面「這根本你」的轉傳鉤、速查總表卡、「傳給某人」CTA。完整見 `references/knowledge_carousel_rubric.md`。

## 已知陷阱
- Chrome headless 字體 fallback → `@import` Noto Sans TC + `'PingFang TC'` 雙保險。
- 圖片用原始比例**不變形**、置中；文字放圖片**原生空白區**，別去裁壞它。
- IG hashtag ≤5 個、集中末尾；正文連結不可點 → 導 bio/留言。
