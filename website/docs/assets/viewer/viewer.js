import * as THREE from '../vendor/three/three.module.js';

const stage = document.querySelector('#stage');
const viewport = document.querySelector('#viewport');
const status = document.querySelector('#status');
const params = new URLSearchParams(location.search);

function localAsset(value, directory) {
  if (!value) throw new Error('Missing scene asset');
  const url = new URL(value, location.href);
  const base = new URL(directory, location.href);
  if (url.origin !== base.origin || !url.pathname.startsWith(base.pathname)) {
    throw new Error('Scene assets must be hosted in the documentation assets directory');
  }
  return url;
}

// Iframes do not inherit Material's palette; follow the same-origin parent.
function followTheme(view) {
  const systemTheme = matchMedia('(prefers-color-scheme: dark)');
  let parentBody = null;
  try { if (window.parent !== window) parentBody = window.parent.document.body; } catch {}
  function update() {
    const scheme = parentBody?.getAttribute('data-md-color-scheme');
    const dark = scheme ? scheme === 'slate' : systemTheme.matches;
    const parentStyle = parentBody ? getComputedStyle(parentBody) : null;
    const background = parentStyle?.getPropertyValue('--md-default-bg-color').trim() || (dark ? '#1e2129' : '#f4f3ef');
    const foreground = parentStyle?.getPropertyValue('--md-default-fg-color').trim() || (dark ? '#e5e7eb' : '#243b43');
    document.documentElement.style.setProperty('--viewer-bg', background);
    document.documentElement.style.setProperty('--viewer-fg', foreground);
    document.documentElement.style.setProperty('--viewer-halo', background);
    document.documentElement.style.colorScheme = dark ? 'dark' : 'light';
    view.setTheme?.({background, foreground, dark});
  }
  if (parentBody) new MutationObserver(update).observe(parentBody, {
    attributes:true, attributeFilter:['data-md-color-scheme', 'style', 'class']
  });
  systemTheme.addEventListener('change', update);
  update();
}

// Shared Z-up orbit controls for every scene; geometry stays in scene modules.
function attachControls({renderer, camera, target, render}) {
  const canvas = renderer.domElement;
  const initial = camera.position.clone();
  const initialRadius = initial.distanceTo(target);
  let drag = null;
  canvas.tabIndex = 0;
  canvas.setAttribute('aria-label', '3D model. Drag to rotate; use arrow keys to rotate and plus or minus to zoom.');
  function orbit(dx, dy) {
    const offset = camera.position.clone().sub(target);
    const radius = offset.length();
    const azimuth = Math.atan2(offset.y, offset.x) - dx * .005;
    const elevation = THREE.MathUtils.clamp(Math.asin(offset.z / radius) + dy * .005,
      -Math.PI / 2 + .05, Math.PI / 2 - .05);
    camera.position.set(radius * Math.cos(elevation) * Math.cos(azimuth),
      radius * Math.cos(elevation) * Math.sin(azimuth), radius * Math.sin(elevation)).add(target);
    camera.lookAt(target);
    render();
  }
  function zoom(factor) {
    const offset = camera.position.clone().sub(target);
    camera.position.copy(target).add(offset.setLength(THREE.MathUtils.clamp(
      offset.length() * factor, initialRadius / 3, initialRadius * 2)));
    camera.lookAt(target);
    render();
  }
  canvas.onpointerdown = event => {
    drag = {x:event.clientX, y:event.clientY};
    canvas.setPointerCapture(event.pointerId);
    canvas.style.cursor = 'grabbing';
  };
  canvas.onpointerup = canvas.onpointercancel = canvas.onlostpointercapture = () => {
    drag = null;
    canvas.style.cursor = 'grab';
  };
  canvas.onpointermove = event => {
    if (!drag) return;
    orbit(event.clientX - drag.x, event.clientY - drag.y);
    drag = {x:event.clientX, y:event.clientY};
  };
  canvas.addEventListener('wheel', event => {
    event.preventDefault();
    zoom(Math.exp(event.deltaY * .001));
  }, {passive:false});
  canvas.onkeydown = event => {
    const moves = {ArrowLeft:[-12,0], ArrowRight:[12,0], ArrowUp:[0,-12], ArrowDown:[0,12]};
    if (moves[event.key]) {event.preventDefault(); orbit(...moves[event.key]);}
    if (['+', '=', '-'].includes(event.key)) {event.preventDefault(); zoom(event.key === '-' ? 1.1 : 1 / 1.1);}
  };
  document.querySelector('#reset').onclick = () => {
    camera.position.copy(initial);
    camera.lookAt(target);
    render();
  };
}

try {
  const sceneURL = localAsset(params.get('scene'), '../scenes/');
  if (!sceneURL.pathname.endsWith('.js')) throw new Error('Expected a scene module');
  const {createScene} = await import(sceneURL.href);
  const view = await createScene(stage);
  followTheme(view);
  stage.style.width = `${view.width}px`;
  stage.style.height = `${view.height}px`;
  attachControls(view);
  const resize = () => {
    const scale = Math.min(viewport.clientWidth / view.width, viewport.clientHeight / view.height);
    stage.style.transform = `scale(${scale})`;
    stage.style.left = `${(viewport.clientWidth - view.width * scale) / 2}px`;
    stage.style.top = `${(viewport.clientHeight - view.height * scale) / 2}px`;
  };
  new ResizeObserver(resize).observe(viewport);
  resize();
  status.hidden = true;
} catch (error) {
  stage.replaceChildren();
  document.querySelector('#toolbar').hidden = true;
  status.textContent = 'The interactive view is unavailable. ';
  if (params.has('fallback')) {
    const link = document.createElement('a');
    link.href = localAsset(params.get('fallback'), '../examples/').href;
    link.textContent = 'View the static figure.';
    status.append(link);
  }
  console.error(error);
}
