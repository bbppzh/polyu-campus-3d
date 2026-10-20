# 四棟單體重建（2026-10-20）

[實景／舊版／新版對照](rebuild-20261020/index.html) · [模型下載](models/index.html)

本次針對 Pao Yue-kong Library、Lee Shau Kee Building、Communal Building、Block X。先前只刪除屋頂佔位物件，沒有補齊可辨認的立面；那一版不能作外觀還原的完成標準。

- 圖書館：按[理大前方外觀照](https://www.polyu.edu.hk/about-polyu/)及官方全景，重建直向磚柱／窄窗、退入入口、端部磚塔與玻璃冠部。
- 李兆基樓：[官方命名記錄](https://www.polyu.edu.hk/archive/media-releases/en/index_id_1525.html)列出 14 層；按[官方照片 C0137](https://www.polyu.edu.hk/-/media/department/home/gallery/campus-environment/c0137.jpg)重建藍色橫窗、磚帶、轉折輪廓與頂部格柵。舊版 20 m 扁平模型已更換；新高度屬視覺估算。
- Communal Building：依官方全景 `panorama_1F2411B7_444D_693C_41AE_6224A87E12AE`，改為磚牆／橫窗、退入式地下層及柱廊。
- Block X：[理大 GreenNet](https://www.polyu.edu.hk/greencampus/GreenNet/issue/14/feature.html)確認低層設計、綠化屋頂及步行通道；官方全景及發展項目照辨認玻璃基座、服務翼、屋頂坡道與階級空間。舊版 35 m 體塊及憑空添加的露天球場不再使用。綠化是有來源的屋頂表面，不是散放的草坪／花槽盒。

四棟 GLB 包含實際窗帶、窗框、柱及立面幾何；不依賴網頁的通用窗格 shader。磚紋為程式生成的細緻乾淨磚紋，隨 UV 與影像一同嵌入 GLB。重複立面依材質批次合併，避免數千個物件逐一繪製。

`data/campus.json` 原始 OSM 資料保留。`data/model-overrides.json` 以實際 GLB 的高度更新網頁卡片與相機，並明確標記為估算；目前高度不是測量值。`docs/referenced-models-qa.json` 記錄 GLB 的自包含材質／UV、繪製批次、顯示高度、李兆基窗帶層數，以及 Block X 屋頂表面／坡道扶手承托檢查。幾何測試不等於外觀或實測精度認證。

重建：在 Blender 執行四個 `tools/build_*.py`；以 `tools/render_model_gallery.py -- library leeshaukee communal blockx --pbr` 渲染，再執行 `tools/update_model_overrides.py`、`tools/build_model_gallery.py`、`tools/build_referenced_review.py` 與 `tools/build_scene_layout.py`。
