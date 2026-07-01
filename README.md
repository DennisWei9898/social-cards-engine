# social-cards-engine · 品牌無關的社群圖卡引擎 🎨

> 一個萬用的 IG／Threads／FB 圖卡引擎——**換一個「品牌插件」就換一種風格**。
> 概念像「Claude Design for 社群圖卡」：工具不變，品牌可以無限切換。

---

## 這是什麼？（用做菜比喻，一分鐘看懂）

你想像開一間**中央廚房**：

- 🍳 **引擎 = 廚房 + 鍋具**：固定的一套設備（HTML+CSS 模板 → 用瀏覽器截圖出 1080 圖卡）。廚房不換。
- 📖 **品牌插件（brand pack）= 食譜 + 調味**：A 客戶要清爽日式、B 客戶要濃郁美式——**換一份食譜就好，廚房不用改**。
- 🧑‍⚖️ **審核員（joker）= 試吃員**：菜端出來之前，先給一個「獨立、專門找碴」的試吃員打分，不合格退回重做。

所以：**一套引擎，服務很多品牌，每個品牌長得都不一樣，但都用同一個廚房產出。**

---

## 你會拿到什麼

| 東西 | 白話 |
|---|---|
| **圖卡引擎** | 把「主題／文章／教學」變成一排輪播圖卡，HTML+CSS → Chrome headless 截圖出 PNG |
| **通用模板** | navy / 暖色 Morandi / 暖大地 ELI5 幾套起手模板 |
| **brand pack 架構** | 「一個品牌一個插件」的資料夾約定，教你怎麼新增自己的品牌 |
| **知識型圖卡方法論** | `knowledge_carousel_rubric`：8–10 張的結構模板 + 讓內容「被存、被傳」的擴散規則 |
| **兩個獨立審核員** | `carousel-joker`（正經知識型）、`meme-joker`（迷因型）——預設有罪推定、禁止客套，逐條 PASS/FAIL |
| **迷因 pack** | 白底黃黑紅 Impact 大字的鄉民迷因風（附**版權提醒**） |

---

## 核心概念：引擎 vs 品牌插件

```
主題 / 文章
   │
   ▼  [引擎] social-cards：拆卡 → HTML 模板 → 截圖出 PNG
   │        ▲
   │        └── 載入哪個 brand pack，就出哪種風格（配色/字體/尺寸/母題/敘事）
   ▼
[審核] joker：對「結構/擴散/幽默」逐條 PASS/FAIL → 不過退回改 → 收斂
   ▼
成品：一排 IG 輪播圖卡
```

**重點**：引擎裡的模板**只是通用起手式，不是「某個人的固定風格」**。要做誰的風格，就掛誰的 brand pack。

---

## 資料夾結構

```
social-cards-engine/
├── SKILL.md                      # 引擎說明（怎麼拆卡、渲染、過閘）
├── templates/                    # 通用模板（navy / morandi / eli5）+ icons + render 範例
├── references/
│   └── knowledge_carousel_rubric.md   # 知識型圖卡結構 + 擴散規則（方法論）
├── skills/
│   ├── carousel-joker/           # 正經知識型輪播審核員
│   └── meme-joker/               # 迷因型輪播審核員（定義「幽默感」為可判定要素）
└── brands/
    ├── README.md                 # brand pack 架構 + 怎麼新增品牌
    └── meme/                      # 內建範例：迷因 brand pack
        ├── brand.md
        ├── render_template.py
        └── memes/                # 梗圖放這（自己抓，見下方版權）
```

---

## 快速開始

1. 需要：macOS + Google Chrome（`--headless` 截圖）+ Python 3。
2. 選一個 brand pack（或照 `brands/README.md` 新增自己的）。
3. 複製該 pack 的 `render_template.py` 到你的專案，改掉 `CARDS`（每張卡的標題/內容）。
4. 跑 `python3 render_template.py` → 出一排 1080 PNG。
5. 丟給 `carousel-joker` / `meme-joker` 審一輪 → 照建議改 → 定版。

---

## 兩個「好朋友」工具（推薦搭配安裝）

這個引擎專心做「產圖 + 結構」。另外兩塊建議搭配安裝，體驗更完整：

- 🎨 **美感／版面審查 → 推薦安裝 [`huashu-design`](https://github.com/) 這類 HTML 設計 skill**：幫你把梗圖置中、不變形、IG 排版顧到位。本引擎的 joker 只審「結構/擴散/幽默」，**美感建議交給設計 skill**。
- 📈 **演算法訊號 + 半自動發文 → 推薦安裝 [Hao0321 的 `social-post` skill](https://github.com/Hao0321/claude-skill-social-post)**：內含 2026 社群演算法訊號權重（私訊分享 > 收藏 > 讚）與半自動發文流程。本引擎的擴散規則就是站在它的肩膀上。

> 沒裝這兩個也能用，但裝了會從「產得出圖」升級到「產得出**會擴散又好看**的圖」。

---

## ⚠️ 迷因梗圖的版權提醒（很重要）

- 內建的迷因 pack **不含任何梗圖檔**——經典梗（Drake / This is fine / Surprised Pikachu…）**大多仍有版權**，公開散布會侵權。
- 請自己去 **[imgflip](https://imgflip.com/memetemplates) / [memes.tw](https://memes.tw)** 抓乾淨模板放進 `memes/`。
- **個人非商用**貼文用經典梗風險較低；**品牌／客戶案**請改用**自繪原創**或**買授權**的梗圖（`meme-joker` 會直接把用版權梗的品牌案判 FAIL）。

---

## 授權

MIT License — 可自由修改、使用、商用，保留授權標註即可。

---

## 🤝 合作方式

打造品牌內容自動化、社群圖卡 pipeline、或想聊 AI 工作流，歡迎聯絡：

- ✉️ Email：**dennis.xd.wei@gmail.com**
- 💼 LinkedIn：**https://www.linkedin.com/in/dennis-wei-47393a14a/**
