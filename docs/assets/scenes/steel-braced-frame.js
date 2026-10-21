import * as THREE from '../vendor/three/three.module.js';

// Geometry is exported by the Python building class, not reconstructed here.
export async function createScene(root) {
  const params = new URLSearchParams(location.search);
  const variant = params.get('variant') || 'default';
  if (!['default', 'lowrise', 'tall'].includes(variant)) throw new Error('Unknown building configuration');
  const response = await fetch(new URL(`../examples/steel-braced-frame/${variant}.json`, import.meta.url));
  if (!response.ok) throw new Error('Building geometry could not be loaded');
  const geometry = await response.json();
  let modes = null, pushover = null;
  if (params.get('response') === 'pushover') {
    const pushResponse = await fetch(new URL(`../examples/steel-braced-frame/${variant}-pushover.json`, import.meta.url));
    if (!pushResponse.ok) throw new Error('Recorded pushover displacements could not be loaded');
    pushover = await pushResponse.json();
  } else if (params.get('modes') === '1') {
    const modalResponse = await fetch(new URL(`../examples/steel-braced-frame/${variant}-modes.json`, import.meta.url));
    if (!modalResponse.ok) throw new Error('Calculated mode shapes could not be loaded');
    modes = await modalResponse.json();
  }
  const width = 1200, height = 900;
  const scene = new THREE.Scene();
  scene.background = new THREE.Color('#f4f3ef');
  const [lx, ly] = geometry.plan_dimensions;
  const elevations = geometry.floor_elevations;
  const totalHeight = elevations.at(-1);
  const target = new THREE.Vector3(lx / 2, ly / 2, totalHeight / 2);
  const camera = new THREE.PerspectiveCamera(35, width / height, .1, 1000);
  camera.up.set(0, 0, 1);
  const span = Math.max(lx, ly, totalHeight);
  camera.position.copy(target).add(new THREE.Vector3(1.6, -2, 1.2).multiplyScalar(span));
  camera.lookAt(target);
  const renderer = new THREE.WebGLRenderer({antialias:true});
  renderer.setSize(width, height);
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  root.appendChild(renderer.domElement);
  scene.add(new THREE.HemisphereLight(0xffffff, 0x607080, 2.5));
  const light = new THREE.DirectionalLight(0xffffff, 2);
  light.position.set(-20, -30, 70);
  scene.add(light);
  const colors = {column:'#376b82', beam:'#78909c', brace:'#c36640'};
  const materials = Object.fromEntries(Object.entries(colors).map(([key,color]) =>
    [key, new THREE.MeshStandardMaterial({color, roughness:.65})]));
  const unitY = new THREE.Vector3(0, 1, 0);
  const originalPoints = geometry.points.map(p => new THREE.Vector3(...p));
  const memberMeshes = [];
  for (const member of geometry.members) {
    const a = new THREE.Vector3(...geometry.points[member.nodes[0]]);
    const b = new THREE.Vector3(...geometry.points[member.nodes[1]]);
    const direction = b.clone().sub(a);
    const radius = member.kind === 'brace' ? .065 : .11;
    const mesh = new THREE.Mesh(new THREE.CylinderGeometry(radius, radius, direction.length(), 7), materials[member.kind]);
    mesh.position.copy(a).add(b).multiplyScalar(.5);
    mesh.quaternion.setFromUnitVectors(unitY, direction.normalize());
    scene.add(mesh);
    memberMeshes.push({mesh, nodes:member.nodes, length:a.distanceTo(b)});
  }
  const floorOutlines = [], massMarkers = [];
  const findNode = (x,y,z) => originalPoints.findIndex(p => p.distanceTo(new THREE.Vector3(x,y,z)) < 1e-7);
  // Dashed outlines illustrate floors without implying slab finite elements.
  for (const z of elevations.slice(1)) {
    const nodes = [[0,0,z],[lx,0,z],[lx,ly,z],[0,ly,z],[0,0,z]].map(p => findNode(...p));
    const outline = new THREE.Line(new THREE.BufferGeometry().setFromPoints(nodes.map(i => originalPoints[i])),
      new THREE.LineDashedMaterial({color:'#9bafb9',transparent:true,opacity:.55,dashSize:.5,gapSize:.35}));
    outline.computeLineDistances();
    scene.add(outline);
    floorOutlines.push({outline,nodes});
    const com = new THREE.Mesh(new THREE.SphereGeometry(.22, 12, 8),
      new THREE.MeshBasicMaterial({color:'#d5a63d'}));
    com.position.set(lx / 2, ly / 2, z);
    scene.add(com);
    massMarkers.push({mesh:com,node:findNode(lx / 2,ly / 2,z)});
  }
  const grid = new THREE.GridHelper(span + 4, Math.round((span + 4) / 2), '#879ba5', '#879ba5');
  grid.rotation.x = Math.PI / 2;
  grid.position.set(lx / 2, ly / 2, -.15);
  grid.material.transparent = true; grid.material.opacity = .25;
  scene.add(grid);
  for (const point of originalPoints.filter(p => Math.abs(p.z) < 1e-7)) {
    const support = new THREE.Mesh(new THREE.ConeGeometry(.28,.5,4),
      new THREE.MeshBasicMaterial({color:'#738a96'}));
    support.rotation.x = Math.PI / 2;
    support.position.copy(point).add(new THREE.Vector3(0,0,-.25));
    scene.add(support);
  }
  const title = document.createElement('div');
  title.className = 'label';
  title.style.cssText = `left:40px;top:${modes || pushover ? 90 : 24}px;font-size:23px`;
  title.textContent = `${geometry.parameters.num_stories} stories | ${lx} x ${ly} m | ${totalHeight} m high`;
  root.appendChild(title);
  const legend = document.createElement('div');
  legend.className = 'label';
  legend.style.cssText = 'left:40px;bottom:24px;font-size:18px';
  legend.textContent = 'Blue: frame | Orange: braces | Gold: floor masses | Grid: fixed-base level';
  root.appendChild(legend);
  const render = () => renderer.render(scene, camera);
  if (modes || pushover) {
    const ghostPositions = geometry.members.flatMap(member => member.nodes.flatMap(i => geometry.points[i]));
    const ghost = new THREE.LineSegments(new THREE.BufferGeometry().setAttribute('position',
      new THREE.Float32BufferAttribute(ghostPositions,3)),
      new THREE.LineBasicMaterial({color:'#93a4b0',transparent:true,opacity:.35}));
    scene.add(ghost);
    const controls = document.createElement('div');
    controls.style.cssText = 'position:absolute;left:40px;top:20px;display:flex;gap:16px;align-items:center;font:20px sans-serif';
    controls.innerHTML = pushover
      ? `<label>Step <input data-frame aria-label="Pushover step" type="range" min="0" max="${pushover.translations.length-1}" value="${pushover.translations.length-1}"></label><label>Display scale <input data-scale aria-label="Displacement display multiplier" type="range" min="1" max="30" value="10"></label><button type="button">Play</button><label><input type="checkbox" checked> Undeformed</label>`
      : '<label>Mode <select data-frame aria-label="Mode number"></select></label><label>Scale <input data-scale aria-label="Relative deformation scale" type="range" min="0" max="2" step="0.05" value="1"></label><button type="button">Animate</button><label><input type="checkbox" checked> Undeformed</label>';
    root.appendChild(controls);
    const select = controls.querySelector('[data-frame]');
    if (modes) {
      modes.frequencies.forEach((f,index) => select.add(new Option(`${index+1}: ${f.toFixed(3)} Hz`, index)));
      const requestedMode = Number(params.get('mode') || 1);
      if (Number.isInteger(requestedMode) && requestedMode >= 1 && requestedMode <= modes.frequencies.length) {
        select.value = requestedMode - 1;
      }
    } else if (params.has('step')) {
      select.value = Math.max(0,Math.min(pushover.translations.length-1,Number(params.get('step')) || 0));
    }
    const slider = controls.querySelector('[data-scale]');
    const animateButton = controls.querySelector('button');
    controls.querySelector('input[type=checkbox]').onchange = event => {ghost.visible=event.target.checked;render();};
    let animation = null, phase = 0;
    const maxTranslations = modes?.translations.map(vectors => Math.max(...vectors.map(v => Math.hypot(...v))));
    function deform(factor=1) {
      const mode = Number(select.value);
      const multiplier = pushover ? Number(slider.value)
        : span*.06*Number(slider.value)*factor/maxTranslations[mode];
      const points = originalPoints.map((p,index) => p.clone().addScaledVector(
        new THREE.Vector3(...(pushover || modes).translations[mode][index]),multiplier));
      for (const {mesh,nodes,length} of memberMeshes) {
        const a=points[nodes[0]],b=points[nodes[1]],direction=b.clone().sub(a);
        mesh.position.copy(a).add(b).multiplyScalar(.5);
        mesh.scale.y=direction.length()/length;
        mesh.quaternion.setFromUnitVectors(unitY,direction.normalize());
      }
      for (const {outline,nodes} of floorOutlines) {
        outline.geometry.setFromPoints(nodes.map(i=>points[i]));outline.computeLineDistances();
      }
      for (const {mesh,node} of massMarkers) mesh.position.copy(points[node]);
      title.textContent = pushover
        ? `Step ${mode}/${pushover.translations.length-1} | Roof = ${(1000*pushover.roof_displacement[mode]).toFixed(1)} mm | Base shear = ${pushover.base_shear[mode].toFixed(1)} kN | View x${slider.value}`
        : `Mode ${mode+1} | f = ${modes.frequencies[mode].toFixed(4)} Hz | T = ${modes.periods[mode].toFixed(4)} s`;
      render();
    }
    function stop() {if(animation!==null) cancelAnimationFrame(animation);animation=null;animateButton.textContent=pushover?'Play':'Animate';}
    select.onchange=select.oninput=()=>{stop();deform();};slider.oninput=()=>{if(animation===null)deform();};
    animateButton.onclick=()=>{
      if(animation!==null){stop();return;}
      animateButton.textContent='Pause';let previous=null, started=null;
      if(pushover && Number(select.value)>=pushover.translations.length-1)select.value=0;
      const firstStep=Number(select.value);
      const tick=time=>{
        if(pushover){
          if(started===null)started=time;
          select.value=Math.min(pushover.translations.length-1,firstStep+Math.floor((time-started)*.008));
          deform();
          if(Number(select.value)>=pushover.translations.length-1){stop();return;}
        }else{if(previous!==null)phase+=(time-previous)*.003;previous=time;deform(Math.sin(phase));}
        animation=requestAnimationFrame(tick);
      };
      animation=requestAnimationFrame(tick);
    };
    document.addEventListener('visibilitychange',()=>{if(document.hidden)stop();});
    new IntersectionObserver(entries=>{if(!entries[0].isIntersecting)stop();}).observe(root);
    deform();
  }
  render();
  return {renderer,camera,target,render,width,height,
    setTheme({background}) {scene.background.set(background); render();}};
}
