#!/usr/bin/env python3
"""Reject stale, missing or historically substituted README model previews."""
from pathlib import Path
import json,hashlib,struct,re
ROOT=Path(__file__).resolve().parent.parent
manifest=json.loads((ROOT/'docs/models/manifest.json').read_text());rows=manifest['models'];errors=[]
if len(rows)!=30:errors.append('expected 30 previews')
readme=(ROOT/'README.md').read_text()
for m in rows:
 for key,hashkey in [('model','model_sha256'),('preview','preview_sha256')]:
  p=ROOT/m[key]
  if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest()!=m[hashkey]:errors.append(m['slug']+' stale '+key)
 data=(ROOT/m['preview']).read_bytes()
 if data[:8]!=b'\x89PNG\r\n\x1a\n' or struct.unpack('>II',data[16:24])!=(900,800):errors.append(m['slug']+' invalid PNG size')
 if m['preview'] not in readme:errors.append(m['slug']+' absent from README')
 if hashlib.sha256((ROOT/m['legacy_preview']).read_bytes()).hexdigest()!=m['preview_sha256']:errors.append(m['slug']+' stale legacy URL')
report={'previews_checked':len(rows),'legacy_urls_checked':len(rows),'errors':errors,'scope':'All README single-model images and legacy URLs are byte-identical to renders whose source GLB hashes match current exported models.'}
(ROOT/'docs/model-gallery-qa.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if errors:raise SystemExit(1)
