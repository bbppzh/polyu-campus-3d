#!/usr/bin/env python3
"""Publish the six repaired models' exported multi-angle review renders."""
from pathlib import Path
import html,json,hashlib
ROOT=Path(__file__).resolve().parent.parent
slugs=['seal','chung','stanley','tang','hoi','gh']
manifest=json.loads((ROOT/'docs/models/manifest.json').read_text())['models']
models={m['slug']:m for m in manifest}
views={'front':'正面','back':'背面','left':'左面','right':'右面','iso':'立體'}
nav=' · '.join(f'<a href="#{s}">{html.escape(models[s]["name"])}</a>' for s in slugs)
sections=[];records=[]
for slug in slugs:
    m=models[slug]
    assert hashlib.sha256((ROOT/m['model']).read_bytes()).hexdigest()==m['model_sha256']
    pics=[]
    for view,label in views.items():
        path=ROOT/'docs/fourview'/f'{slug}-{view}.png'
        records.append({'slug':slug,'view':view,'model_sha256':m['model_sha256'],'image_sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
        pics.append(f'<figure><a href="{slug}-{view}.png"><img src="{slug}-{view}.png" width="800" height="700" loading="lazy" alt="{html.escape(m["name"])} {label}"></a><figcaption>{label}</figcaption></figure>')
    sections.append(f'<section id="{slug}"><h2>{html.escape(m["name"])}</h2><div class="views">'+''.join(pics)+'</div></section>')
page='''<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>六棟模型 · 多角度檢查</title><style>body{margin:0;background:#f4f1ea;color:#26221f;font:15px/1.6 system-ui}main{max-width:1400px;margin:auto;padding:24px}a{color:#ad2035}h1{font-size:28px}h2{font-size:21px;margin-top:44px}.views{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}figure{margin:0;background:white;border:1px solid #ddd7cc;border-radius:8px;overflow:hidden}img{display:block;width:100%;height:auto}figcaption{padding:8px 12px}@media(max-width:800px){.views{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:500px){.views{grid-template-columns:1fr}}</style><main><a href="../models/">← 單體模型</a><h1>六棟模型 · 多角度檢查</h1><p>修正入口、立面構件及樓層帶的錯位。每張圖直接由更新後的 3D 模型生成；建築位置及尺寸仍屬簡化近似。</p><nav>'''+nav+'</nav>'+''.join(sections)+'</main></html>'
(ROOT/'docs/fourview/alignment.html').write_text(page)
(ROOT/'docs/fourview/alignment-manifest.json').write_text(json.dumps({'renders':records},indent=2)+'\n')
print('Alignment review: six models, 30 views')
