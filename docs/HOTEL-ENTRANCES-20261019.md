# Hotel 入口驗收（2026-10-19）

本次關閉「Hotel 三個入口的圖紙定位及模型幾何」項目。這個狀態不代表取得竣工測量、精確垂直標高或完整實景四向驗證。

## 1. G/F 圖配準

以人工辨認的六個角點，把建築師 600×675 地下圖以仿射變換配準到目前 OSM 衍生的校園公尺座標，並按 extract_data.py 相同原點換算入口 WGS84 座標。控制點、原圖 SHA256、變換矩陣、各點殘差均保存在 data/hotel-entrances.json。

- 控制點 RMSE：0.289 m。
- 三個未參與配準的獨立檢查點 RMSE：0.689 m。
- 三個圖像入口點貼合各自外牆的修整距離：酒店入口 1.190 m、學院入口 0.731 m、職員宿舍入口 0.143 m.

低殘差只表示圖像與既有地圖輪廓對得上，不能當成現場絕對精度。控制點來自低解析度圖片和簡化 OSM，圖紙日期與 2026 現況亦未逐項確認。

## 2. 模型修正

酒店與學院入口綁定裙樓外牆；宿舍入口綁定 University House 外牆。模型統一使用同一註冊資料，避免把已轉過座標的低座輪廓再次轉換。對與入口相交的地面主體開出門口和前方空間，移除舊塔樓邊界造成的遮擋；上部塔樓輪廓保留。

酒店入口增加與官方外觀照片對應的玻璃大堂面。門、框柱、雨棚的尺寸仍是外觀簡化設定，不能作施工或無障礙尺寸判定。地面基準仍為模型 y=0。

網站的 Hotel 招牌亦綁定同一酒店入口座標，放在入口雨棚前方，不再使用塔樓最近邊。

## 3. 所有底角檢查

直接讀取最終 GLB 的實際三角面，沒有執行生成器來代替驗證。

- 三組門／雨棚共 24 個底角全部檢查。
- 加上框柱、支架及橫樑，共 24 個入口組件、96 個底角；另檢查頂角及中心。
- 檢查範圍含 Hotel 各結構主體及相鄰背景建築。
- 各入口前 0.3–8 m 通道，以 0.25 m 間距、三個橫向位置、地面及眼高兩種高度抽樣。
- 門檻 y=0.02 m，按模型地面基準核對；雨棚由框柱及支架承托。

目前獨立檢查：PASS，0 個幾何問題。完整逐點資料見 hotel-entrances/geometry-qa.json。這不是全模型每一個三角面之間的窮盡碰撞認證。

## 4. 三張低角度對照

三個入口各輸出修改後低角度圖及相同機位的修改前圖，相機眼高 1.7 m。每組附地下圖入口定位對照。照片僅有酒店整體外觀參照，不將學院／宿舍的平面圖對照冒稱同機位實景驗收。

- [酒店入口](hotel-entrances/hotel-after.png)
- [學院入口](hotel-entrances/school-after.png)
- [宿舍入口](hotel-entrances/staff-after.png)
- [完整互動對照頁](hotel-entrances/index.html)
- [配準疊圖](hotel-entrances/registration.svg)

## 重現

```sh
python3 tools/register_hotel_plan.py
Blender --background --python-exit-code 1 --python tools/build_hicon.py
python3 tools/check_hotel_entrances.py
Blender --background --python-exit-code 1 --python tools/render_hotel_entrances.py
```

Blender 改用本機實際執行檔路徑。build_hicon.py 每次會先按目前 campus.json 重新配準，避免輪廓更新後沿用過期入口位置。render-manifest.json 保存實際渲染 GLB 與配準資料雜湊，相機資料見 cameras.json。
