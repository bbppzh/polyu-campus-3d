// Runs the real procedural builders and verifies the deployed layout inputs.
import fs from 'node:fs';
import vm from 'node:vm';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath, pathToFileURL } from 'node:url';
import * as THREE from '../vendor/three/three.module.js';
const root=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const data=JSON.parse(fs.readFileSync(path.join(root,'data/campus.json')));
const layout=JSON.parse(fs.readFileSync(path.join(root,'data/scene-layout.json')));
const errors=[];
for(const [slug,hash] of Object.entries(layout.model_sha256)){
 const actual=crypto.createHash('sha256').update(fs.readFileSync(path.join(root,`assets/models/${slug}.glb`))).digest('hex');
 if(actual!==hash) errors.push(`stale model ${slug}`);
}
if(crypto.createHash('sha256').update(fs.readFileSync(path.join(root,'data/campus.json'))).digest('hex')!==layout.campus_sha256)errors.push('stale source data');
const threeURL=pathToFileURL(path.join(root,'vendor/three/three.module.js')).href;
const utils=fs.readFileSync(path.join(root,'vendor/three/addons/utils/BufferGeometryUtils.js'),'utf8').replace(/from 'three'/g,`from '${threeURL}'`);
const {mergeGeometries}=await import('data:text/javascript;base64,'+Buffer.from(utils).toString('base64'));
let source=fs.readFileSync(path.join(root,'src/buildings.js'),'utf8').replace(/^import .*;\s*$/gm,'').replace(/^export /gm,'');
source=source.replace('const b = context[i];','const b = context[i]; __activeBuilding=b;');
source=source.replaceAll('buckets.white.push(g);','buckets.white.push(g); __records.push({building:__activeBuilding,bucket:"parapet",g});');
source=source.replaceAll('buckets[bucket].push(g);','buckets[bucket].push(g); __records.push({building:__activeBuilding,bucket,g});');
const context={Math,console,__activeBuilding:null,__records:[],mergeGeometries};
vm.createContext(context);vm.runInContext(source+'\nthis.builders={buildContextDetails,buildTrees,pointInFootprint};',context);
const start=performance.now();
context.builders.buildContextDetails(THREE,layout.context,[],layout.landmarkEnvelopes);
let roofProps=0;
for(const {building,bucket,g} of context.__records){
 if(!['roof','dark','green'].includes(bucket)&&g.type!=='CylinderGeometry')continue;
 roofProps++;g.computeBoundingBox();const lo=g.boundingBox.min,hi=g.boundingBox.max;
 const floor=Math.max(4,building.height||16);
 if(Math.abs(lo.y-floor)>.005)errors.push(`roof elevation ${building.id}`);
 for(let ix=0;ix<=4;ix++)for(let iz=0;iz<=4;iz++){
  const x=lo.x+(hi.x-lo.x)*(ix/4*.998+.001),z=lo.z+(hi.z-lo.z)*(iz/4*.998+.001);
  if(!context.builders.pointInFootprint(x,z,building))errors.push(`unsupported roof prop ${building.id}`);
 }
}
const trees=context.builders.buildTrees(THREE,data.landmarks,data.areas,layout.treeObstacles);
const positions=[];const mat=new THREE.Matrix4();const pos=new THREE.Vector3(),rot=new THREE.Quaternion(),scale=new THREE.Vector3();
for(let i=0;i<trees.children[0].count;i++){
 trees.children[1].getMatrixAt(i,mat);mat.decompose(pos,rot,scale);
 if(layout.treeObstacles.some(shape=>context.builders.pointInFootprint(pos.x,pos.z,shape)))errors.push(`tree obstacle ${i}`);
 if(Math.max(scale.x,scale.z)>layout.tree_clearance_m)errors.push(`tree crown exceeds setback ${i}`);
 positions.push({x:pos.x,z:pos.z,r:Math.max(scale.x,scale.z)});
}
const report={model_hashes_checked:Object.keys(layout.model_sha256).length,context_pieces:layout.context.length,roof_props_checked:roofProps,trees_checked:positions.length,tree_crown_clearance_m:layout.tree_clearance_m,procedural_build_ms:Math.round(performance.now()-start),errors,scope:'Actual context/tree builders; GLB/source hashes, roof support samples including holes and every tree instance against buffered building/road exclusions.'};
fs.writeFileSync(path.join(root,'docs/scene-layout-qa.json'),JSON.stringify(report,null,2)+'\n');
const geometryPath=process.argv[2] || process.env.QA_GEOMETRY_PATH;
if(geometryPath){
 const details=context.__records.map(({building,bucket,g})=>{
  const a=g.getAttribute('position'),pts=[];let bottom=Infinity;
  for(let i=0;i<a.count;i++){pts.push([a.getX(i),a.getZ(i)]);bottom=Math.min(bottom,a.getY(i));}
  return {id:building.id,bucket,bottom,points:pts};
 });
 fs.writeFileSync(geometryPath,JSON.stringify({details,trees:positions}));
}
console.log(JSON.stringify(report));if(errors.length)process.exitCode=1;
