# Shared 3D documentation viewer

Three.js r170 is hosted once in `assets/vendor/three/` with its MIT license.
All figures share `viewer.html`, `viewer.js`, and `viewer.css`; do not copy the
library or orbit controls into individual examples.

Add geometry in an ES module under `assets/scenes/`. Export
`createScene(root)` returning `{renderer, camera, target, render, width, height}`.
Append the canvas and any projected labels to `root`. The camera uses Z up.
`render()` must draw the scene and update labels after a camera change.
Scene modules import Three.js from `../vendor/three/three.module.js`.

Embed using a path relative to the built page. Raw HTML iframe URLs are not
rewritten by MkDocs. For a page built at `examples/basin/index.html`:

```html
<iframe src="../../assets/viewer/viewer.html?scene=../scenes/basin-regional.js&amp;fallback=../examples/basin/regional_3d.png"
        title="Descriptive figure title" loading="lazy"
        style="width:100%;height:clamp(340px,65vw,720px);border:0"></iframe>
```

Include an ordinary static-image link outside the iframe for printing and
readers without JavaScript. Scene modules and fallback images must be same-origin
assets. Geometry uses fixed logical dimensions; the shared viewer scales it
to fit the available space. No animation loop runs while idle.
