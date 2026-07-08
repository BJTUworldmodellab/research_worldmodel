import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "visual" / "cinematic_3d_showcase.html"

SCENE_PICK = {
    "bedroom": 78,
    "livingroom": 29,
    "diningroom": 39,
}


def exact_count(target, pred):
    pred = list(map(tuple, pred))
    total = 0
    for rel in map(tuple, target):
        if rel in pred:
            total += 1
            pred.remove(rel)
    return total


def relation_targets(scene):
    selected = [tuple(x) for x in scene["selected_relations"]]
    before = set(map(tuple, scene["layout_relations"]))
    after = set(map(tuple, scene["repair_relations"]))
    improved = [rel for rel in selected if rel not in before and rel in after]
    return improved or selected


def pack_scene(room, idx):
    path = ROOT / "results" / "full" / room / "relation_aware_parsed_mesh_p2_close0.75_far1.6_eval.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    scene = data["per_scene"][idx]
    selected = scene["selected_relations"]
    return {
        "room": room,
        "index": idx,
        "scene_uid": scene["scene_uid"],
        "text": scene["text"],
        "beforeScore": exact_count(selected, scene["layout_relations"]),
        "afterScore": exact_count(selected, scene["repair_relations"]),
        "totalRelations": len(selected),
        "beforeMeshPairs": scene["layout_mesh_collision"]["collision_pairs"],
        "afterMeshPairs": scene["repair_mesh_collision"]["collision_pairs"],
        "targets": relation_targets(scene),
        "before": scene["layout_boxes"],
        "after": scene["repair_boxes"],
    }


def main():
    scenes = [pack_scene(room, idx) for room, idx in SCENE_PICK.items()]
    payload = json.dumps(scenes, ensure_ascii=False)
    html = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Relation-Aware InstructScene Cinematic 3D</title>
  <style>
    :root {{
      --bg: #05070a;
      --panel: rgba(12, 17, 24, .76);
      --line: rgba(156, 235, 216, .22);
      --text: #effffb;
      --muted: #9eb9b2;
      --accent: #3cf2c2;
      --warn: #ffad66;
    }}
    * {{ box-sizing: border-box; }}
    html, body {{ margin: 0; height: 100%; overflow: hidden; background: var(--bg); color: var(--text); font-family: Inter, ui-sans-serif, system-ui, "Segoe UI", sans-serif; }}
    #app {{ position: fixed; inset: 0; }}
    canvas {{ display: block; }}
    .hud {{
      position: fixed; left: 22px; top: 22px; width: min(520px, calc(100vw - 44px));
      padding: 18px 18px 16px; border: 1px solid var(--line); border-radius: 10px;
      background: linear-gradient(135deg, rgba(12,17,24,.86), rgba(12,17,24,.58));
      box-shadow: 0 24px 80px rgba(0,0,0,.36), inset 0 0 32px rgba(60,242,194,.035);
      backdrop-filter: blur(14px);
    }}
    .eyebrow {{ margin: 0 0 8px; color: var(--accent); font-size: 12px; font-weight: 800; letter-spacing: .12em; text-transform: uppercase; }}
    h1 {{ margin: 0; font-size: clamp(28px, 4vw, 54px); line-height: .95; letter-spacing: 0; }}
    .prompt {{ margin: 12px 0 0; color: var(--muted); line-height: 1.42; font-size: 14px; }}
    .controls {{ display: flex; gap: 9px; flex-wrap: wrap; margin-top: 14px; }}
    button {{
      border: 1px solid var(--line); background: rgba(255,255,255,.06); color: var(--text);
      border-radius: 8px; padding: 9px 11px; cursor: pointer; font-weight: 750; letter-spacing: 0;
    }}
    button.active {{ background: rgba(60,242,194,.18); border-color: rgba(60,242,194,.7); color: #dffff7; }}
    .metrics {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-top: 14px; }}
    .metric {{ border: 1px solid var(--line); border-radius: 8px; padding: 10px; background: rgba(255,255,255,.045); }}
    .metric span {{ display: block; color: var(--muted); font-size: 11px; text-transform: uppercase; letter-spacing: .08em; }}
    .metric strong {{ display: block; margin-top: 3px; font-size: 22px; }}
    .legend {{
      position: fixed; right: 22px; bottom: 22px; width: min(390px, calc(100vw - 44px));
      padding: 13px 14px; border: 1px solid var(--line); border-radius: 10px;
      background: rgba(12, 17, 24, .68); color: var(--muted); line-height: 1.45; font-size: 13px;
      backdrop-filter: blur(14px);
    }}
    .hotkey {{ color: var(--text); font-weight: 800; }}
    @media (max-width: 760px) {{
      .metrics {{ grid-template-columns: 1fr; }}
      .legend {{ display: none; }}
    }}
  </style>
</head>
<body>
  <div id="app"></div>
  <section class="hud">
    <p class="eyebrow">Cinematic 3D Layout Showcase</p>
    <h1 id="title">Relation-Aware InstructScene</h1>
    <p id="prompt" class="prompt"></p>
    <div class="controls">
      <button id="beforeBtn">Before</button>
      <button id="afterBtn" class="active">After</button>
      <button id="bedroomBtn">Bedroom</button>
      <button id="livingroomBtn">Living</button>
      <button id="diningroomBtn">Dining</button>
      <button id="spinBtn" class="active">Auto Camera</button>
    </div>
    <div class="metrics">
      <div class="metric"><span>Relation Score</span><strong id="relationMetric"></strong></div>
      <div class="metric"><span>Mesh Pairs</span><strong id="meshMetric"></strong></div>
      <div class="metric"><span>Scene</span><strong id="sceneMetric"></strong></div>
    </div>
  </section>
  <aside class="legend">
    Drag to orbit, scroll to zoom. Cyan arrows mark repaired relation targets. This is a stylized 3D layout view using generated boxes and retrieved-object sizes; raw mesh diagnostics remain available separately.
  </aside>
  <script type="application/json" id="scene-data">{payload}</script>
  <script type="importmap">
    {{
      "imports": {{
        "three": "https://unpkg.com/three@0.160.0/build/three.module.js",
        "three/addons/": "https://unpkg.com/three@0.160.0/examples/jsm/"
      }}
    }}
  </script>
  <script type="module">
    import * as THREE from 'three';
    import {{ OrbitControls }} from 'three/addons/controls/OrbitControls.js';

    const scenes = JSON.parse(document.getElementById('scene-data').textContent);
    const app = document.getElementById('app');
    const renderer = new THREE.WebGLRenderer({{ antialias: true, alpha: false }});
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.25;
    app.appendChild(renderer.domElement);

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x05070a);
    scene.fog = new THREE.FogExp2(0x05070a, 0.026);

    const camera = new THREE.PerspectiveCamera(48, window.innerWidth / window.innerHeight, 0.1, 120);
    camera.position.set(6.5, 7.4, 8.2);
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.055;
    controls.target.set(0, 0.55, 0);

    const root = new THREE.Group();
    scene.add(root);

    const ambient = new THREE.HemisphereLight(0x9fffea, 0x182230, 1.25);
    scene.add(ambient);
    const key = new THREE.DirectionalLight(0xffffff, 2.2);
    key.position.set(6, 10, 6);
    key.castShadow = true;
    key.shadow.mapSize.set(2048, 2048);
    key.shadow.camera.near = 0.5;
    key.shadow.camera.far = 35;
    key.shadow.camera.left = -10;
    key.shadow.camera.right = 10;
    key.shadow.camera.top = 10;
    key.shadow.camera.bottom = -10;
    scene.add(key);
    const cyan = new THREE.PointLight(0x34ffd2, 60, 16);
    cyan.position.set(-4, 4, 3);
    scene.add(cyan);
    const amber = new THREE.PointLight(0xff9d56, 34, 14);
    amber.position.set(5, 3, -4);
    scene.add(amber);

    const floorMat = new THREE.MeshStandardMaterial({{ color: 0x08120f, roughness: .58, metalness: .18, emissive: 0x061d18, emissiveIntensity: .6 }});
    const floor = new THREE.Mesh(new THREE.PlaneGeometry(20, 20), floorMat);
    floor.rotation.x = -Math.PI / 2;
    floor.receiveShadow = true;
    scene.add(floor);
    const grid = new THREE.GridHelper(20, 40, 0x35f5c8, 0x1d403b);
    grid.material.transparent = true;
    grid.material.opacity = 0.34;
    scene.add(grid);

    const palette = [0x4e79a7,0x59a14f,0xf28e2b,0xe15759,0x76b7b2,0xedc948,0xb07aa1,0xff9da7,0x9c755f,0x8cd17d,0x499894,0xd37295];
    const colorMap = new Map();
    function colorFor(name) {{
      if (!colorMap.has(name)) colorMap.set(name, palette[colorMap.size % palette.length]);
      return colorMap.get(name);
    }}
    function labelText(name) {{
      name = name.replaceAll('_', ' ');
      const rules = [['multi seat sofa','sofa'],['corner side table','side table'],['double bed','bed'],['dining table','table'],['dining chair','chair'],['coffee table','coffee tbl'],['pendant lamp','lamp'],['bookshelf','shelf']];
      for (const [k,v] of rules) if (name.includes(k)) return v;
      return name.split(' ').slice(0,2).join(' ');
    }}
    function makeLabel(text) {{
      const canvas = document.createElement('canvas');
      canvas.width = 512; canvas.height = 128;
      const ctx = canvas.getContext('2d');
      ctx.fillStyle = 'rgba(2,8,10,.78)';
      ctx.strokeStyle = 'rgba(60,242,194,.65)';
      ctx.lineWidth = 3;
      roundRect(ctx, 12, 20, 488, 78, 18);
      ctx.fill(); ctx.stroke();
      ctx.fillStyle = '#effffb';
      ctx.font = '700 42px Inter, Arial';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(text, 256, 60);
      const texture = new THREE.CanvasTexture(canvas);
      const sprite = new THREE.Sprite(new THREE.SpriteMaterial({{ map: texture, transparent: true, depthWrite: false }}));
      sprite.scale.set(1.18, .3, 1);
      return sprite;
    }}
    function roundRect(ctx, x, y, w, h, r) {{
      ctx.beginPath();
      ctx.moveTo(x+r,y); ctx.arcTo(x+w,y,x+w,y+h,r); ctx.arcTo(x+w,y+h,x,y+h,r); ctx.arcTo(x,y+h,x,y,r); ctx.arcTo(x,y,x+w,y,r); ctx.closePath();
    }}
    function makeBox(box, highlighted) {{
      const sx = Math.max(box.size[0] * 2, .06);
      const sy = Math.max(box.size[1] * 2, .08);
      const sz = Math.max(box.size[2] * 2, .06);
      const mat = new THREE.MeshPhysicalMaterial({{
        color: colorFor(box.class_name),
        roughness: .42,
        metalness: .12,
        clearcoat: .32,
        transparent: true,
        opacity: highlighted ? .92 : .78,
        emissive: highlighted ? 0x0b6b58 : 0x000000,
        emissiveIntensity: highlighted ? .24 : 0,
      }});
      const mesh = new THREE.Mesh(new THREE.BoxGeometry(sx, sy, sz), mat);
      mesh.position.set(box.translation[0], sy / 2, box.translation[2]);
      mesh.rotation.y = -box.angle;
      mesh.castShadow = true; mesh.receiveShadow = true;
      const edges = new THREE.LineSegments(new THREE.EdgesGeometry(mesh.geometry), new THREE.LineBasicMaterial({{ color: highlighted ? 0x3cf2c2 : 0x101719, transparent: true, opacity: highlighted ? .95 : .58 }}));
      mesh.add(edges);
      const label = makeLabel(labelText(box.class_name));
      label.position.set(0, sy / 2 + .18, 0);
      mesh.add(label);
      return mesh;
    }}
    function pairForRelation(boxes, rel) {{
      const [subj,, obj] = rel;
      const subjBoxes = boxes.filter(b => Number(b.class_id) === Number(subj));
      const objBoxes = boxes.filter(b => Number(b.class_id) === Number(obj));
      let best = null, bestD = Infinity;
      for (const a of subjBoxes) for (const b of objBoxes) {{
        const dx = a.translation[0] - b.translation[0], dz = a.translation[2] - b.translation[2];
        const d = dx*dx + dz*dz;
        if (d < bestD) {{ bestD = d; best = [a,b]; }}
      }}
      return best;
    }}
    function makeArrow(from, to) {{
      const start = new THREE.Vector3(from.translation[0], 1.05, from.translation[2]);
      const end = new THREE.Vector3(to.translation[0], 1.05, to.translation[2]);
      const dir = new THREE.Vector3().subVectors(end, start);
      const len = dir.length();
      if (len < .05) return new THREE.Group();
      const group = new THREE.Group();
      const shaft = new THREE.Mesh(new THREE.CylinderGeometry(.025, .025, Math.max(len - .22, .05), 16), new THREE.MeshStandardMaterial({{ color: 0x3cf2c2, emissive: 0x20c9a4, emissiveIntensity: 1.2 }}));
      shaft.position.copy(start).addScaledVector(dir, .5);
      shaft.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0), dir.clone().normalize());
      const cone = new THREE.Mesh(new THREE.ConeGeometry(.095, .24, 24), shaft.material);
      cone.position.copy(end).addScaledVector(dir.clone().normalize(), -.08);
      cone.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0), dir.clone().normalize());
      group.add(shaft, cone);
      const glow = new THREE.PointLight(0x3cf2c2, 4, 2.2);
      glow.position.copy(end);
      group.add(glow);
      return group;
    }}

    let currentScene = 0;
    let mode = 'after';
    let spin = true;
    function clearRoot() {{
      while(root.children.length) root.remove(root.children[0]);
    }}
    function renderLayout() {{
      clearRoot();
      colorMap.clear();
      const data = scenes[currentScene];
      const boxes = mode === 'after' ? data.after : data.before;
      const targetSet = new Set();
      for (const rel of data.targets) {{
        const pair = pairForRelation(boxes, rel);
        if (pair) {{ targetSet.add(pair[0].index); targetSet.add(pair[1].index); }}
      }}
      for (const box of boxes) root.add(makeBox(box, targetSet.has(box.index)));
      for (const rel of data.targets) {{
        const pair = pairForRelation(boxes, rel);
        if (pair) root.add(makeArrow(pair[1], pair[0]));
      }}
      document.getElementById('title').textContent = `${{data.room}} #${{data.index}}`;
      document.getElementById('prompt').textContent = data.text;
      const score = mode === 'after' ? data.afterScore : data.beforeScore;
      const meshPairs = mode === 'after' ? data.afterMeshPairs : data.beforeMeshPairs;
      document.getElementById('relationMetric').textContent = `${{score}}/${{data.totalRelations}}`;
      document.getElementById('meshMetric').textContent = meshPairs;
      document.getElementById('sceneMetric').textContent = mode.toUpperCase();
      document.getElementById('beforeBtn').classList.toggle('active', mode === 'before');
      document.getElementById('afterBtn').classList.toggle('active', mode === 'after');
      ['bedroom','livingroom','diningroom'].forEach((room, i) => document.getElementById(room+'Btn').classList.toggle('active', i === currentScene));
      frameCamera(boxes);
    }}
    function frameCamera(boxes) {{
      const xs = boxes.map(b => b.translation[0]), zs = boxes.map(b => b.translation[2]);
      const cx = (Math.min(...xs) + Math.max(...xs)) / 2;
      const cz = (Math.min(...zs) + Math.max(...zs)) / 2;
      controls.target.set(cx, .65, cz);
    }}
    document.getElementById('beforeBtn').onclick = () => {{ mode='before'; renderLayout(); }};
    document.getElementById('afterBtn').onclick = () => {{ mode='after'; renderLayout(); }};
    document.getElementById('bedroomBtn').onclick = () => {{ currentScene=0; renderLayout(); }};
    document.getElementById('livingroomBtn').onclick = () => {{ currentScene=1; renderLayout(); }};
    document.getElementById('diningroomBtn').onclick = () => {{ currentScene=2; renderLayout(); }};
    document.getElementById('spinBtn').onclick = () => {{ spin=!spin; document.getElementById('spinBtn').classList.toggle('active', spin); }};

    renderLayout();
    const clock = new THREE.Clock();
    function animate() {{
      requestAnimationFrame(animate);
      const t = clock.getElapsedTime();
      if (spin) {{
        const target = controls.target;
        const radius = 9.5;
        camera.position.x = target.x + Math.cos(t * .18) * radius;
        camera.position.z = target.z + Math.sin(t * .18) * radius;
        camera.position.y = 6.2 + Math.sin(t * .33) * .45;
        camera.lookAt(target);
      }}
      root.children.forEach((child, i) => {{
        if (child.isMesh) child.position.y += Math.sin(t*1.3 + i) * 0.0009;
      }});
      controls.update();
      renderer.render(scene, camera);
    }}
    animate();
    window.addEventListener('resize', () => {{
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    }});
  </script>
</body>
</html>"""
    OUT.write_text(html, encoding="utf-8")
    print(OUT)


if __name__ == "__main__":
    main()
