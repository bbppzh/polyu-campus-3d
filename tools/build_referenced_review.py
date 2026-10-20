#!/usr/bin/env python3
"""Build a photo / previous model / current exported model comparison page."""
from pathlib import Path
import json,html,hashlib
R=Path(__file__).resolve().parent.parent;out=R/'docs/rebuild-20261020';out.mkdir(exist_ok=True)
items=[
 ('library','直向磚柱、窄窗、退入入口與端部識別塔；取消中央佔位玻璃盒。','https://www.polyu.edu.hk/-/media/department/home/content/about-polyu/strategic-plan_2_1080x524.jpg','https://www.polyu.edu.hk/about-polyu/'),
 ('leeshaukee','表達官方記錄的 14 層、弧形／轉折立面、藍色橫窗與磚帶。米制高度為照片估算。','https://www.polyu.edu.hk/-/media/department/home/gallery/campus-environment/c0137.jpg','https://www.polyu.edu.hk/archive/media-releases/en/index_id_1525.html'),
 ('communal','磚牆與連續橫窗、退入式地下玻璃及外側承重柱。','https://www.polyu.edu.hk/saso/vtour/media/panorama_1F2411B7_444D_693C_41AE_6224A87E12AE_0/b/2/0_0.jpg','https://www.polyu.edu.hk/saso/vtour/'),
 ('blockx','改為低層玻璃基座、窄服務翼、屋頂綠化與連接坡道，扶手底腳跟隨坡面。','https://www.polyu.edu.hk/giving/-/media/department/giving/content/priorities/campus-development/dec-2021-revised-version/photo06.jpg?hash=86F2BA360E138E072ADCA85279E04661&mh=1000&mw=478&rev=67cc0cee2a3e4dfaa20450d6e0455b84','https://www.polyu.edu.hk/greencampus/GreenNet/issue/14/feature.html')]
models={m['slug']:m for m in json.loads((R/'docs/models/manifest.json').read_text())['models']}
sections=[];records=[]
for slug,note,photo,source in items:
 m=models[slug];assert hashlib.sha256((R/m['model']).read_bytes()).hexdigest()==m['model_sha256']
 sections.append(f'<section id="{slug}"><h2>{html.escape(m["name"])}</h2><p>{note}</p><div class="compare"><figure><a href="{html.escape(source)}"><img src="{html.escape(photo)}" alt="{html.escape(m["name"])} 官方實景參考" loading="lazy"></a><figcaption>官方實景 · <a href="{html.escape(source)}">來源</a></figcaption></figure><figure><img src="before-{slug}.png" alt="{html.escape(m["name"])} 修正前模型" loading="lazy"><figcaption>修正前 · 9f13d2a</figcaption></figure><figure><a href="../../{m["model"]}"><img src="../models/{slug}.png?v={m["preview_sha256"][:12]}" alt="{html.escape(m["name"])} 修正後模型" loading="lazy"></a><figcaption>修正後 · <a href="../../{m["model"]}">同一份 GLB</a></figcaption></figure></div></section>')
 records.append({'slug':slug,'source':source,'reference_image':photo,'features':note,'model_sha256':m['model_sha256'],'preview_sha256':m['preview_sha256'],'before_commit':'9f13d2a'})
page='''<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>四棟重建 · 實景與模型對照</title><style>body{margin:0;background:#f4f1ea;color:#29251f;font:15px/1.7 system-ui}main{max-width:1450px;margin:auto;padding:26px}a{color:#a72337}h1{font-size:29px}h2{font-size:22px;margin:44px 0 8px}.compare{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:15px}figure{margin:0;background:white;border:1px solid #ddd7ce;border-radius:8px;overflow:hidden}img{display:block;width:100%;aspect-ratio:9/8;object-fit:contain;background:#e9e7e2}figcaption{padding:10px}nav{display:flex;flex-wrap:wrap;gap:16px}.note{max-width:1050px;color:#645c51}@media(max-width:750px){.compare{grid-template-columns:1fr}main{padding:16px}}</style><main><a href="../models/?v=20261020-facades1">← 單體模型</a><h1>四棟重建 · 實景與模型對照</h1><p>2026-10-20 · 窗帶、磚柱、入口及屋頂結構直接包含在可下載的 3D 模型內。</p><p class="note">照片用於辨認可見輪廓及建築特徵；比例、標高與未見立面仍為簡化估算。照片與模型視點不同，這頁不是測繪驗收。官方照片由原站載入，版權屬原作者及理大；修正前圖片只作歷史對照。</p><nav>'''+''.join(f'<a href="#{s}">{html.escape(models[s]["name"])}</a>' for s,_,_,_ in items)+'</nav>'+''.join(sections)+'<p><a href="../referenced-models-qa.json">模型檔案及幾何檢查</a> · <a href="../REFERENCED-REBUILD-20261020.md">重建記錄</a></p></main></html>'
(out/'index.html').write_text(page);(out/'manifest.json').write_text(json.dumps({'models':records},ensure_ascii=False,indent=2)+'\n')
print('Photo comparison page: four models')
