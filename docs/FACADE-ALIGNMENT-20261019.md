# 六棟模型構件對齊修正（2026-10-19）

本輪處理 Seal of Love Foundation Building、Chung Sze Yuen Building、Stanley Ho Building、Tang Ping Yuan Building、House of Innovation 及 GH Block 的單體構件錯位。

[六棟多角度預覽](https://bbppzh.github.io/polyu-campus-3d/docs/fourview/alignment.html) · [單體模型及下載](https://bbppzh.github.io/polyu-campus-3d/docs/models/)

- 全部六棟：入口玻璃、門框、雨棚改用實際 footprint 邊線的方向與外法線，雨棚底與入口頂接齊；取消按世界坐標外接方框放置的方式。
- Seal：白色樓層帶與磚牆分層，修正重疊面的鋸齒；圓形樓梯玻璃與磚牆切分，底座落地、圓頂接齊屋頂；女兒牆改為完整閉合接角，移除無依據的屋頂小亭。
- Chung：玻璃帶、牆身與白色帶改為連續的垂直分段，取消縮放重疊殼層；女兒牆閉合接角。
- Stanley：綠牆和框架跟隨實際端牆；三層露台欄板底部接觸樓板，補齊兩端回折欄板。
- Tang：上層直窗及窗台按上層牆面定位；中層框架跟隨玻璃多邊形，底部分層接齊。
- HOI：服務核心與玻璃主體在平面上使用共同頂點切分，取消穿出玻璃外殼的方盒；窗框在核心位置斷開。
- GH：玻璃角沿實際相鄰外牆切分，取消懸在屋頂外的固定 45 度方盒；白帶與磚牆分層。

`tools/check_facade_alignment.py` 直接讀取輸出的六份 GLB，檢查入口牆面對齊、雨棚與門框接縫、主體分層重疊、玻璃／核心分界、女兒牆覆蓋、直窗方向及露台欄板承托。結果記錄在 [facade-alignment-qa.json](facade-alignment-qa.json)。30 張角度圖來自同一批 GLB，圖片與模型摘要記錄在 [alignment-manifest.json](fourview/alignment-manifest.json)。

這輪修正幾何接位，沿用既有 footprint、估算高度及簡化設計；沒有新增實測圖紙，因此不能把構件對齊檢查當作逐面實景測繪認證。
