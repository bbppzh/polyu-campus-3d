// Exercise the real procedural generator without a browser or a WebGL context.
import fs from 'node:fs';
import vm from 'node:vm';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const root=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const data=JSON.parse(fs.readFileSync(path.join(root,'data/campus.json')));
let source=fs.readFileSync(path.join(root,'src/buildings.js'),'utf8');
source=source.replace(/^import .*;\s*$/gm,'').replace(/^export /gm,'');
source=source.replace('const b = context[i];','const b = context[i]; __activeId = b.id;');
source=source.replaceAll('buckets[bucket].push(g);','buckets[bucket].push(g); __records.push({id:__activeId,bucket,g});');
class Geometry {
 constructor(w,h,d){this.w=w;this.h=h;this.d=d;this.x=0;this.y=0;this.z=0;this.rot=0;}
 translate(x,y,z){this.x=x;this.y=y;this.z=z;return this;}
 rotateY(a){this.rot=a;return this;}
}
class Cylinder extends Geometry {constructor(r1,r2,h,n){super(2*Math.max(r1,r2),h,2*Math.max(r1,r2));this.cylinder=true;}}
const THREE={BoxGeometry:Geometry,CylinderGeometry:Cylinder,Group:class {add(){}},Mesh:class {constructor(g,m){this.geometry=g;this.material=m;this.userData={}}},MeshStandardMaterial:class {constructor(p){this.p=p}}};
const context={Math,console,__activeId:null,__records:[],mergeGeometries:()=>({})};vm.createContext(context);vm.runInContext(source+'\nthis.runContext=buildContextDetails;',context);context.runContext(THREE,data.context,[]);
function inside(poly,x,z){let ok=false;for(let i=0,j=poly.length-1;i<poly.length;j=i++){const a=poly[i],b=poly[j];if((a[1]>z)!=(b[1]>z)&&x<(b[0]-a[0])*(z-a[1])/(b[1]-a[1])+a[0])ok=!ok;}return ok;}
const errors=[];let tested=0;
for(const r of context.__records){
 const b=data.context.find(b=>b.id===r.id),g=r.g,h=Math.max(4,b.height||16);
 if(!(r.bucket==='roof'||r.bucket==='dark'||r.bucket==='green'||g.cylinder))continue;
 tested++;
 const pts=[[-.5,-.5],[-.5,.5],[.5,.5],[.5,-.5],[0,0]];
 if(pts.some(([u,v])=>!inside(b.footprint,g.x+u*g.w,g.z+v*g.d)))errors.push({id:r.id,bucket:r.bucket,reason:'base outside roof'});
 if(Math.abs(g.y-g.h/2-h)>.005)errors.push({id:r.id,bucket:r.bucket,reason:'base not on roof',gap:g.y-g.h/2-h});
}
const report={tested_rooftop_props:tested,errors,scope:'Calls actual buildContextDetails; checks generated roof props against closed context polygons and exact roof elevation.'};fs.writeFileSync(path.join(root,'docs/final-context-qa.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report));if(errors.length)process.exitCode=1;
