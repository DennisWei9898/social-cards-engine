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
5. **過閘（寫審分離）**：丟給 `carousel-joker`（知識型）或 `meme-joker`（迷因型）逐條 PASS/FAIL → 改 → 收斂。
6. **寫 4 平台文案** `social_captions.md`（每平台一個 code block，copy-paste 友善）。

## 尺寸與擴散（知識型）
- 尺寸：知識型輪播 **4:5（1080×1350）**佔版面最大；快速方形貼可 1:1。
- 張數：8–12 張（一圖一觀念）。
- 擴散：對著 **sends（私訊分享）> saves（收藏）> likes** 設計——封面「這根本你」的轉傳鉤、速查總表卡、「傳給某人」CTA。完整見 `references/knowledge_carousel_rubric.md`。

## 已知陷阱
- Chrome headless 字體 fallback → `@import` Noto Sans TC + `'PingFang TC'` 雙保險。
- 圖片用原始比例**不變形**、置中；文字放圖片**原生空白區**，別去裁壞它。
- IG hashtag ≤5 個、集中末尾；正文連結不可點 → 導 bio/留言。
