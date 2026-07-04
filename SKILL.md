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

> 一句話：**安裝完 → 跟 Claude 聊 → 選預設或共創你的風格 → 出圖 → joker 審**。使用者不碰 Python，那是引擎內部渲染在跑。

## 🤝 推薦搭配 skill（偵測到有裝就自動借力，沒裝也能獨立跑）
- **`huashu-design`**（HTML 設計 skill）：出圖前後做**版面 QA**——圖片置中不變形、留白節奏、跑版／溢出檢查、IG 排版。**渲染後有跑版／要顧美感就交給它**；建 brand pack 的「核心資產協議」也用它。
- **`social-post`（Hao0321）**：**2026 演算法訊號權重**（私訊分享 sends > 收藏 saves > 讚）＝本引擎擴散規則的來源；還有**半自動發文**（FB／IG／Threads）＋ 學使用者貼文語氣。**要診斷擴散、要發文、要學語氣就用它**（見 `references/knowledge_carousel_rubric.md` 已內建其權重摘要）。
- 沒裝這兩個 → 引擎照內建 rubric + joker 獨立跑，只是少了版面 QA 與一鍵發文。

## Pipeline

1. **確認主題 + 拆 N 張卡**：主題核心句、拆幾張（知識型建議 8–10）、CTA、每張標題(≤12字)+描述。
2. **選 brand pack**：載入配色/字體/尺寸/母題/敘事 DNA。
3. **寫 render 腳本**：複製 pack 的 `render_template.py`，改 `CARDS` 陣列（每張 dict：name / content / tag）。
4. **渲染**：Chrome headless 截圖：
   ```python
   subprocess.run([CHROME, "--headless=new", "--disable-gpu",
     "--allow-file-access-from-files", "--force-device-scale-factor=2",
     f"--window-size=1080,1350", f"--screenshot={png}", f"file://{html}"])
   ```
5. **過閘（寫審分離・自動不問）**：圖卡出完**一律自動**丟給 `carousel-joker`（知識型）或 `meme-joker`（迷因型）逐條 PASS/FAIL → 改 → 收斂。**不問使用者要不要驗，直接驗、直接修。**
   - **迭代上限（防無停止條件空轉）**：**最多 3 輪**；3 輪仍有 FAIL、或連續 2 輪無改善 → **停止自動修、標記「未過閘」上報使用者裁決，不自動放行**。gate 就是 gate，別「取最高分」矇混，也別無限重跑燒 token。
6. **寫 4 平台文案** `social_captions.md`（每平台一個 code block，copy-paste 友善）。

## 尺寸與擴散（知識型）
- 尺寸：知識型輪播 **4:5（1080×1350）**佔版面最大；快速方形貼可 1:1。
- 張數：8–12 張（一圖一觀念）。
- 擴散：對著 **sends（私訊分享）> saves（收藏）> likes** 設計——封面「這根本你」的轉傳鉤、速查總表卡、「傳給某人」CTA。完整見 `references/knowledge_carousel_rubric.md`。

## 已知陷阱
- Chrome headless 字體 fallback → `@import` Noto Sans TC + `'PingFang TC'` 雙保險。
- 圖片用原始比例**不變形**、置中；文字放圖片**原生空白區**，別去裁壞它。
- IG hashtag ≤5 個、集中末尾；正文連結不可點 → 導 bio/留言。
