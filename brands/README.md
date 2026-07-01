# Brand Packs 註冊表（引擎 vs 品牌插件）

> 核心概念：**social-cards 是「圖卡引擎」（tool），品牌識別是「插件」（brand pack）。**
> 接上哪個 pack → 產出哪個風格。引擎本身**不綁死任何品牌配色**。
> 一套引擎可服務個人品牌、A 客戶、B 客戶… 各自不同風格。

## 怎麼運作
1. 判斷這次要用哪個品牌。
2. 載入對應 `brands/<brand>/brand.md`（配色、字體、尺寸、wordmark、簽名母題、敘事 DNA）。
3. 用該 pack 的 `render_template.py` 出圖 → 過 `carousel-joker` / `meme-joker` → （可選）發文。
4. **沒有品牌 pack 就先建一個**（見下方步驟）。

## 內建 brand pack

| brand | 用途 | 識別一句話 | pack |
|---|---|---|---|
| **meme** | 迷因模式（可疊任何主題） | 白底・黃黑紅・Impact 大字・真梗圖・4:5 | `brands/meme/`（過 `meme-joker`；⚠️ 品牌案需自繪/授權梗圖）|

> 這裡只附一個**通用的迷因 pack** 當範例。你的個人品牌 / 客戶品牌 pack 請自己照下面步驟建立（放進你自己的私有目錄，不要公開客戶素材）。

## 新增 brand pack（範本步驟）
1. `brands/<brand>/brand.md`：色票 / 字體 / 尺寸 / wordmark / 簽名母題 / 敘事 DNA / footer 樣式 / 何時用。
2. `brands/<brand>/render_template.py`：該品牌的 4:5 或 1:1 渲染模板（`CARDS` 換內容即可重用）。
3. 品牌資產（logo/頭像/產品照）放 pack 內或專案 assets。
4. 到本表註冊一行。

### 建品牌 pack 的資產協議（重要）
涉及具體品牌時，先抓**真實素材**再設計（不要憑感覺配色）：
- **Logo**（任何品牌必備）、**產品照/情境照**（實體產品必備）、**UI 截圖**（數位產品必備）。
- **色票**：從官網 HTML/SVG grep 真實色值，別憑印象。
- **字體 + 氣質關鍵詞**。
- 一律用真實照片，禁 CSS 剪影假圖。

## ⚠️ 引擎不綁品牌（重要原則）
- `../templates/*`（navy/warm/morandi）只是**通用起手模板**，**不是「某個人的固定風格」**。
- 幫某品牌做 → 用該品牌 pack，**絕不套別的品牌配色**。
