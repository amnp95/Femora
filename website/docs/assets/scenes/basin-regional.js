import * as THREE from '../vendor/three/three.module.js';

export function createScene(root) {
const W=1600,H=1050;
const scene=new THREE.Scene();scene.background=new THREE.Color('#f4f3ef');
const camera=new THREE.PerspectiveCamera(35,W/H,.1,500);
camera.position.set(76,82,68);camera.up.set(0,0,1);camera.lookAt(0,3,-7);
const renderer=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});
renderer.setSize(W,H);renderer.setPixelRatio(1.5);renderer.outputColorSpace=THREE.SRGBColorSpace;
root.appendChild(renderer.domElement);
scene.add(new THREE.HemisphereLight(0xffffff,0x737c89,2.2));
const sun=new THREE.DirectionalLight(0xffffff,3);sun.position.set(-25,-35,70);scene.add(sun);
function box(size,pos,color,opacity=1){const m=new THREE.Mesh(new THREE.BoxGeometry(...size),new THREE.MeshStandardMaterial({color,transparent:opacity<1,opacity,roughness:.85,depthWrite:opacity===1}));m.position.set(...pos);scene.add(m);return m;}
function line(points,color='#829198',dashed=false){const geo=new THREE.BufferGeometry().setFromPoints(points.map(p=>new THREE.Vector3(...p)));const m=dashed?new THREE.LineDashedMaterial({color,dashSize:.55,gapSize:.4}):new THREE.LineBasicMaterial({color});const l=new THREE.Line(geo,m);l.computeLineDistances();scene.add(l);}
function doubleArrow(start,end,color){
  const a=new THREE.Vector3(...start),b=new THREE.Vector3(...end);
  const direction=b.clone().sub(a),length=direction.length();direction.normalize();
  scene.add(new THREE.ArrowHelper(direction,a,length,color,.9,.48));
  scene.add(new THREE.ArrowHelper(direction.clone().negate(),b,length,color,.9,.48));
}
function label(text,p,dx=0,dy=0){const e=document.createElement('div');e.className='label';e.innerHTML=text;root.appendChild(e);labels.push({e,p:new THREE.Vector3(...p),dx,dy});}
const labels=[];
// A transparent regional block exposes the source plane beneath the surface.
// One rock volume with a shallow recess occupied by the basin, not a third cap.
const rockShape=new THREE.Shape();
rockShape.moveTo(-12.5,-25);rockShape.lineTo(12.5,-25);
rockShape.lineTo(12.5,-1);rockShape.lineTo(-9.5,-1);
rockShape.lineTo(-9.5,0);rockShape.lineTo(-12.5,0);rockShape.closePath();
const rockGeometry=new THREE.ExtrudeGeometry(rockShape,{depth:44,bevelEnabled:false});
rockGeometry.applyMatrix4(new THREE.Matrix4().set(0,0,1,-22,1,0,0,0,0,1,0,0,0,0,0,1));
const rock=new THREE.Mesh(rockGeometry,new THREE.MeshStandardMaterial({color:'#91a2ad',transparent:true,opacity:.18,roughness:.85,depthWrite:false}));
scene.add(rock);
const edges=new THREE.LineSegments(new THREE.EdgesGeometry(rock.geometry),new THREE.LineBasicMaterial({color:'#85969d',transparent:true,opacity:.65}));edges.position.copy(rock.position);scene.add(edges);
// Leave the near-side rock strip exposed, with sediment above the interior.
box([44,22,1],[0,1.5,-.5],'#c8b57e',.30);
// Synthetic normalized slip pattern for illustration only, not SW4 output.
const slipCanvas=document.createElement('canvas');slipCanvas.width=768;slipCanvas.height=384;
const slipContext=slipCanvas.getContext('2d');
const slipImage=slipContext.createImageData(768,384);
const slipColors=[[238,228,186],[223,198,122],[208,160,78],[191,111,55],[163,65,43],[119,44,40]];
for(let j=0;j<384;j++)for(let i=0;i<768;i++){
  const x=i/767,y=j/383;
  const gaussian=(cx,cy,sx,sy)=>Math.exp(-1*((x-cx)/sx)**2-((y-cy)/sy)**2);
  const field=Math.min(.999,(.92*gaussian(.32,.58,.23,.33)+
    .72*gaussian(.73,.38,.20,.28)+.30*gaussian(.57,.78,.17,.18))*
    (1+.07*Math.sin(25*x+9*y)+.05*Math.cos(31*y-7*x)));
  const level=field*6,index=Math.min(5,Math.floor(level));
  const contour=level>.65&&Math.abs(level-Math.round(level))<.035;
  const color=contour?[119,89,65]:slipColors[index];
  const offset=(j*768+i)*4;
  slipImage.data.set([...color,255],offset);
}
slipContext.putImageData(slipImage,0,0);
const slipTexture=new THREE.CanvasTexture(slipCanvas);slipTexture.colorSpace=THREE.SRGBColorSpace;
const fault=box([27,.14,12],[0,-9.5,-6],'#ffffff',.92);
fault.material.map=slipTexture;
line([[-13.5,-9.65,.08],[13.5,-9.65,.08]],'#9d3028');
// Hypocenter, eight kilometres below the fault trace.
const hypo=new THREE.Mesh(new THREE.SphereGeometry(.72,24,16),new THREE.MeshBasicMaterial({color:'#ffcf36'}));hypo.position.set(-4,-9.9,-8);scene.add(hypo);
// Treat the hypocenter as a diagram marker, visible through transparent solids.
hypo.material.transparent=true;hypo.material.depthTest=false;hypo.material.depthWrite=false;hypo.renderOrder=10;
line([[-4,-9.9,0],[-4,-9.9,-8]],'#966c3a',true);
const sites=[[-10,-8.5,'Site 1'],[10,-8.5,'Site 2'],[-10,8.5,'Site 3']];
for(const [x,y,name] of sites){box([1.1,1.1,.65],[x,y,.34],'#287f91');label('<strong>'+name+'</strong>',[x,y,.8],-22,-27);}
line([[-10,-8.5,.12],[-10,8.5,.12]],'#487c85',true);
line([[-10,-8.5,.12],[10,-8.5,.12]],'#487c85',true);
// Keep the distance label outside the surface, with a curved leader to the line.
const strikeCurve=new THREE.QuadraticBezierCurve3(
  new THREE.Vector3(24,-17,4),new THREE.Vector3(13,-20,8),
  new THREE.Vector3(0,-8.5,.2));
line(strikeCurve.getPoints(48).map(p=>p.toArray()),'#a34c39');
scene.add(new THREE.ArrowHelper(strikeCurve.getTangent(1).normalize(),
  strikeCurve.getPoint(1).sub(strikeCurve.getTangent(1).multiplyScalar(.9)),
  .9,'#a34c39',.9,.48));
label('20 km along strike',[24,-17,4],-145,-25);
label('17 km',[-10,1,.2],-62,-6);
function curvedCallout(start,control,end,color,overlay=false){
  const curve=new THREE.QuadraticBezierCurve3(new THREE.Vector3(...start),
    new THREE.Vector3(...control),new THREE.Vector3(...end));
  line(curve.getPoints(48).map(p=>p.toArray()),color);
  if(overlay){const leader=scene.children[scene.children.length-1];leader.material.transparent=true;leader.material.depthTest=false;leader.renderOrder=11;}
  const direction=curve.getTangent(1).normalize();
  const arrow=new THREE.ArrowHelper(direction,curve.getPoint(1).addScaledVector(direction,-.9),
    .9,color,.9,.48);
  if(overlay)arrow.traverse(part=>{if(part.material){part.material.transparent=true;part.material.depthTest=false;part.renderOrder=11;}});
  scene.add(arrow);
}
curvedCallout([32,-20,-7],[28,-20,-1],[13.5,-9.5,-5],'#a34c39');
label('<strong>Fault plane</strong><br>27 km by 12 km<br><span style="font-size:14px">Schematic slip contours</span>',[32,-20,-7],-120,8);
curvedCallout([-22,23,0],[-11,23,4],[3,9,-.3],'#8b7950');
label('Sedimentary basin',[-22,23,0],12,-10);
// Screen-space leader cannot disappear behind the transparent fault or basin.
const leaderOverlay=document.createElementNS('http://www.w3.org/2000/svg','svg');
leaderOverlay.setAttribute('viewBox',`0 0 ${W} ${H}`);
leaderOverlay.style.cssText=`position:absolute;left:0;top:0;width:${W}px;height:${H}px;pointer-events:none`;
leaderOverlay.innerHTML='<defs><marker id="hypo-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto"><path d="M0 0L10 5L0 10Z" fill="#a47b37"/></marker></defs><path id="hypo-leader" fill="none" stroke="#a47b37" stroke-width="1.4" marker-end="url(#hypo-arrow)"/>';
root.appendChild(leaderOverlay);
const hypoLeader=leaderOverlay.querySelector('#hypo-leader');
function updateHypocenterLeader(){
  const project=p=>{const v=p.clone().project(camera);return new THREE.Vector2((v.x+1)*W/2,(-v.y+1)*H/2);};
  const start=project(new THREE.Vector3(12,-17,17));
  const center=project(hypo.position);
  const control=new THREE.Vector2(start.x+(center.x-start.x)*.65,start.y);
  const radius=center.distanceTo(project(hypo.position.clone().addScaledVector(
    new THREE.Vector3().setFromMatrixColumn(camera.matrixWorld,0),.72)));
  const end=center.clone().add(control.clone().sub(center).normalize().multiplyScalar(radius+2));
  hypoLeader.setAttribute('d',`M${start.x},${start.y} Q${control.x},${control.y} ${end.x},${end.y}`);
}
label('<strong>Hypocenter</strong><br>8 km depth',[12,-17,17],-110,-40);
curvedCallout([-22,23,-16],[-14,23,-11],[-2,12.5,-16],'#657d89');
label('Rock',[-22,23,-16],12,-10);
doubleArrow([-22,-14,-25],[22,-14,-25],'#7c8c94');
label('44 km',[0,-14,-25],-25,12);
doubleArrow([25,-12.5,-25],[25,12.5,-25],'#7c8c94');
label('25 km',[25,0,-25],15,4);
function render(){renderer.render(scene,camera);for(const {e,p,dx,dy} of labels){const v=p.clone().project(camera);e.style.left=((v.x+1)*W/2+dx)+'px';e.style.top=((-v.y+1)*H/2+dy)+'px';}updateHypocenterLeader();root.dataset.ready='true';}
render();

return {renderer,camera,render,target:new THREE.Vector3(0,3,-7),width:W,height:H,
  setTheme({background}){scene.background.set(background);render();}};
}
