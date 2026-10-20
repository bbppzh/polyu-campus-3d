# 單體模型與屋頂道具清理 — 2026-10-19

此頁為 2026-10-19 歷史清理記錄。四棟最新的輪廓／立面與有實景依據的屋頂重建，請看 [2026-10-20 重建及實景對照](REFERENCED-REBUILD-20261020.md)。

本輪針對 GitHub README 單獨展示的建築。早期 PNG 並不等於現行 GLB；部分圖仍展示過期的懸空／穿模裝飾。現在 30 張預覽均直接從目前使用的 GLB 渲染，並記錄模型及圖片 SHA256；原有 30 個單體圖片網址也同步更新。

## 屋頂內容

- 移除六組沒有足夠實景依據的棚架，以及屋頂花槽、矩形草坪、孤立柱、樹木與佔位設備。先前已發布模型中，24 棟共有 145 個這類物件；現行 30 個 GLB 的對應類別檢查為 0。
- Z 座額外添加的露台玻璃棚及其支柱也一併移除。主要樓體、屋頂本體、連橋、周界結構及必要的承重支撐保留。
- 背景樓體不再隨機生成屋頂草坪、水箱、設備箱或通風管。
- 補充清理：移除圖書館屋頂玻璃盒及兩側天窗、李兆基樓額外天窗、Communal Building 天窗及頂框，以及 Block X 整組屋頂球場、劃線、圍柱與燈柱。共移除 51 件構件，其餘 65 組網格幾何保持一致（[逐項記錄](roof-cleanup-qa.json)）。這些物件的生成程式已移除，匯出前也會逐名排除。
- 陽台欄杆不再送入「移至屋頂」的支撐處理。CMA／何鴻燊樓的欄杆留在各自陽台，避免屋頂出現無來由的玻璃條。

這是清除沒有來源支持的模型添加物，不表示真實屋頂完全沒有綠化或設備。後續只應根據可核對的照片／圖則加入具體構件。

## 單體幾何與展示

- 綜藝館、邵逸夫體育館的曲面屋頂按廳體周界裁切，牆身頂部沿屋頂底面閉合；修正懸空接縫及原平頂牆體穿過曲面的情況。
- 每張預覽顯示完整模型，避免裁邊；有入口的模型以入口方向選擇視角。
- README 改為 30 棟目前模型的展示表；[完整圖庫](models/index.html) 可搜尋、放大及下載相同 GLB。
- 移除已失效的四棟舊合成圖及早期自動批次展示圖。`reference/` 中標明為歷史參考的影像繼續保留。

## 檢查與重現

`model-gallery-qa.json` 核對全部 30 張預覽、來源 GLB 及 30 個舊圖片網址；`standalone-assemblies-qa.json` 檢查沒有相關屋頂道具，並核對兩個曲面屋頂共 1,538 個底面三角形的中心與廳體頂部接合。其餘幾何／場景／Hotel 入口檢查沿用現有工具並重新執行。

```sh
# Blender 重建後，先更新模型預覽及其舊網址。
blender --background --python tools/render_model_gallery.py
python3 tools/build_model_gallery.py
python3 tools/check_model_gallery.py
python3 tools/check_standalone_assemblies.py
python3 tools/build_scene_layout.py
python3 tools/audit_models.py
node tools/check_scene_layout.mjs /tmp/campus-details.json
python3 tools/check_scene_intersections.py /tmp/campus-details.json
python3 tools/check_model_intersections.py
python3 tools/check_hotel_entrances.py
```

Python 幾何檢查使用 `tools/requirements-geometry.txt`。上述檢查不是完整的實景測繪或所有三角形配對零碰撞證明；幾何比例與標高仍受 [DATA-GAPS-20261019.md](DATA-GAPS-20261019.md) 所列資料限制。
