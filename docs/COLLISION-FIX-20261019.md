# 穿模修正 — 2026-10-19

此為先前場景穿模修正紀錄。單體模型與屋頂道具的最新清理見 [STANDALONE-MODELS-20261019.md](STANDALONE-MODELS-20261019.md)。

本輪修正針對網站實際載入的 GLB、背景樓體及程序生成裝飾；原始 OSM 記錄仍保留在 `data/campus.json`。

## 修正內容

- **JCIT**：舊版以一條局部邊線決定長軸，另加 15 m 偏移，導致底座與文康大樓／背景平台相交。現在以映射範圍內的輪廓容納程度及鄰樓避讓選擇長軸，沿用原有樓體比例及 71.2 m 高度，移除額外偏移。本輪長軸約 123.04°；這是模型放置校正，不是測繪結果。
- **綜藝館**：原先矩形網格屋頂超出不規則廳體，伸入吳永康樓。曲面及玻璃頂帶現在按廳體周界裁切；保留屋頂起伏。
- **環球學生薈**：裁去伸入周亦卿樓／葉傑全樓的邊角，保留其餘樓體。
- **背景樓體**：從 30 個實際 GLB 的水平投影建立避讓範圍，裁去與地標重疊的部分；背景記錄互相覆蓋時，較高樓體保留其範圍，較低樓體保留外露部分。輸出 447 個有效片段，涉及 143 個原背景記錄；來源資料沒有刪改。
- **背景裝飾**：支持裁切後的孔洞；屋頂物件檢查完整底面；雨棚以多邊形包含及邊線相交檢查避讓。
- **樹木**：避讓實際模型輪廓、所有背景樓體及道路，按最大樹冠半徑預留 3 m；保留 170 棵。

## 檢查結果

| 檢查 | 結果 | 範圍 |
|---|---:|---|
| 地標模型 | 30 棟；0 個非有限頂點／退化三角形 | `final-qa.json` |
| 地標相鄰樓體 | 0 對抽樣重疊（原檢查 31 對） | 1.5 m 網格；1/3/6/10/15/20/30/40/50/60 m 高度；結構面，不含所有裝飾 |
| 背景／地標投影與背景互相相交 | 0 m² | 447 個輸出片段；多邊形精確相交，非網格估算 |
| 實際程序裝飾 | 4,400 個；0 項相交問題 | 對地標投影及較高相鄰背景樓體檢查 |
| 背景屋頂物件底面 | 281 個；0 項問題 | 含孔洞的支撐及標高檢查 |
| 樹木 | 170 棵；0 棵樹冠與樓體相交 | 使用實際實例位置及完整樹冠半徑 |
| Hotel 三個入口 | PASS | 24 個主要底角、96 個組件底角；入口位置及通道檢查維持通過 |

結果見 `model-intersections-qa.json`、`scene-intersections-qa.json`、`scene-layout-qa.json` 及 `hotel-entrances/geometry-qa.json`。新場景資料記錄每個 GLB 及原資料的 SHA256；重建模型後必須重新產生場景資料並檢查。

本機網頁已查看 JCIT／綜藝館周邊及校園全景，未見載入錯誤。以上是指定幾何與檢查範圍內的修正；多高度抽樣不等於整個場景所有三角形皆獲零碰撞證明，建築比例／標高仍受原資料缺口限制。

## 重現

```sh
python3 -m pip install -r tools/requirements-geometry.txt
python3 tools/build_scene_layout.py
node tools/check_scene_layout.mjs /tmp/campus-details.json
python3 tools/check_scene_intersections.py /tmp/campus-details.json
python3 tools/check_model_intersections.py
python3 tools/audit_models.py
python3 tools/check_hotel_entrances.py
```
