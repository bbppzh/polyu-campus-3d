#!/usr/bin/env python3
"""Publish current GLB previews to README, the gallery and legacy image URLs."""
from pathlib import Path
import json,hashlib,shutil,html
ROOT=Path(__file__).resolve().parent.parent
p=ROOT/'docs/models/manifest.json';manifest=json.loads(p.read_text());models=manifest['models']
ALIASES={'lks':'lks3d','jcit':'jcit','jca':'jca3d','gsh':'gsh3d','shaw':'shaw3d','blockx':'blockx3d','blockz':'blockz3d','chan':'chansui3d','taio':'taiho3d','anita':'anita3d','chow':'chow3d','mong':'mong3d','ng':'ng3d','yip':'yip3d','seal':'seal3d','cma':'cma3d','chung':'chung3d','lui':'lui3d','stanley':'stanley3d','choi':'choi3d','shirley':'shirley3d','gh':'gh3d','fong':'fong3d','tang':'tang3d','leeshaukee':'leeshaukee3d','hoi':'hoi3d','industrial':'industrial3d','communal':'communal3d','library':'library3d','hotel_icon':'hotel3d'}
for m in models:
 assert hashlib.sha256((ROOT/m['model']).read_bytes()).hexdigest()==m['model_sha256'],m['slug']+' preview is stale'
 alias='docs/'+ALIASES[m['slug']]+'.png';shutil.copyfile(ROOT/m['preview'],ROOT/alias);m['legacy_preview']=alias
p.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
cards=[]
for m in models:
 name=html.escape(m['name']);zh=html.escape(m['nameZh']);slug=m['slug']
 cards.append(f'<article id="{slug}" data-name="{name.lower()} {zh}"><a href="./{slug}.png"><img src="./{slug}.png" alt="{name} 單體模型" width="900" height="800" loading="lazy"></a><div><h2>{name}</h2><p>{zh}</p><a href="./{slug}.png">放大預覽</a> · <a href="../../{m["model"]}" download>下載 3D 模型</a></div></article>')
page='''<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>單體模型 · PolyU Campus 3D</title>
<style>body{margin:0;background:#f4f1ea;color:#26221f;font:15px/1.6 system-ui,sans-serif}header,main{max-width:1300px;margin:auto;padding:24px}h1{margin:12px 0 8px;font-size:30px}a{color:#ad2035}header p{max-width:850px}input{box-sizing:border-box;width:min(100%,450px);padding:12px;border:1px solid #bcb7ae;border-radius:6px;background:white;font:inherit}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:20px}article{overflow:hidden;background:#fff;border-radius:9px;border:1px solid #ddd7cc}article img{width:100%;height:auto;display:block}article div{padding:15px}h2{font-size:17px;margin:0}article p{margin:4px 0 12px;color:#6c655d}[hidden]{display:none!important}@media(max-width:900px){.grid{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:560px){.grid{grid-template-columns:1fr}header,main{padding:16px}}</style>
<header><a href="../../">← 校園全景</a> · <a href="https://github.com/bbppzh/polyu-campus-3d#單體模型">GitHub</a><h1>單體模型</h1><p>目前使用的 30 棟模型。預覽直接由同一份 3D 模型生成，已清走沒有實景依據的屋頂裝飾。建築輪廓和標高仍屬簡化近似。</p><input id="search" type="search" aria-label="搜尋單體模型" placeholder="搜尋建築名稱"><p id="count">30 棟模型</p></header><main class="grid">'''+''.join(cards)+'''</main><footer style="padding:24px;text-align:center"><a href="../../credits.html">來源及使用條款</a></footer>
<script>const input=document.querySelector('#search'),cards=[...document.querySelectorAll('article')];input.addEventListener('input',()=>{const q=input.value.trim().toLowerCase();let n=0;for(const card of cards){card.hidden=!card.dataset.name.includes(q);if(!card.hidden)n++;}document.querySelector('#count').textContent=n+' 棟模型';});</script></html>'''
(ROOT/'docs/models/index.html').write_text(page)
readme=ROOT/'README.md';s=readme.read_text();start=s.index('## 單體模型') if '## 單體模型' in s else s.index('![Jockey Club Auditorium:');end=s.index('![Dusk over the campus]',start)
intro='''
## 單體模型

以下 30 張預覽直接由目前的 GLB 生成；沒有實景依據的屋頂棚架、獨立支柱、草坪花槽及佔位設備已移除。
[放大查看全部單體模型](https://bbppzh.github.io/polyu-campus-3d/docs/models/) · [修正與檢查記錄](docs/STANDALONE-MODELS-20261019.md)

'''
rows=['| 模型 | 模型 | 模型 |','| --- | --- | --- |']
for i in range(0,len(models),3):
 cells=[]
 for m in models[i:i+3]:cells.append(f'**{m["name"]}**<br>{m["nameZh"]}<br>[![{m["name"]}]({m["preview"]})](https://bbppzh.github.io/polyu-campus-3d/docs/models/#{m["slug"]})')
 rows.append('| '+' | '.join(cells)+' |')
s=s[:start]+intro+'\n'.join(rows)+'\n\n'+s[end:];readme.write_text(s)
print('Gallery and 30 legacy image URLs refreshed')
