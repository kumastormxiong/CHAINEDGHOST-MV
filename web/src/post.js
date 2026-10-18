// 后期管线：场景 → 泛光(Bloom) → 色差/故障/扫描线/颗粒/暗角(FX) → 输出
import * as THREE from 'three';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { ShaderPass } from 'three/addons/postprocessing/ShaderPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';

const FX = {
  uniforms: {
    tDiffuse: { value: null }, uTime: { value: 0 }, uRes: { value: new THREE.Vector2(1920, 1080) },
    uAb: { value: 0.002 }, uGlitch: { value: 0 }, uScan: { value: 0.1 }, uGrain: { value: 0.04 }, uVig: { value: 0.4 },
    uFlash: { value: new THREE.Color(0, 0, 0) }, uTrack: { value: 0 }, uWarp: { value: 0 }, uPix: { value: 0 }
  },
  vertexShader: 'varying vec2 vUv;void main(){vUv=uv;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}',
  fragmentShader: `
  uniform sampler2D tDiffuse;uniform float uTime,uAb,uGlitch,uScan,uGrain,uVig,uTrack,uWarp,uPix;uniform vec3 uFlash;uniform vec2 uRes;varying vec2 vUv;
  float h(float n){return fract(sin(n*12.9898)*43758.5453);}
  float h2(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
  void main(){
    vec2 uv=vUv; vec2 cc=uv-0.5; float r2=dot(cc,cc); uv=0.5+cc*(1.0+uWarp*r2);
    if(uPix>0.0){ vec2 g=uRes/(8.0+uPix*40.0); uv=floor(uv*g)/g; }
    float tt=floor(uTime*18.0);
    float by=floor(uv.y*18.0); float gb=step(1.0-0.45*uGlitch,h(by+tt*3.1)); uv.x+=gb*(h(by*2.0+tt)-0.5)*0.2*uGlitch;
    float fy=floor(uv.y*200.0); float gf=step(1.0-0.1*uGlitch,h(fy+tt*5.0)); uv.x+=gf*(h(fy+tt)-0.5)*0.07*uGlitch;
    float tb=fract(uTime*0.11); float band=smoothstep(0.05,0.0,abs(uv.y-tb))*uTrack; uv.x+=band*0.02*sin(uv.y*420.0);
    vec2 dir=normalize(cc+vec2(1e-5)); float ab=uAb*(0.4+length(cc)*2.4)+gb*0.012*uGlitch;
    vec3 col; col.r=texture2D(tDiffuse,uv+dir*ab).r; col.g=texture2D(tDiffuse,uv).g; col.b=texture2D(tDiffuse,uv-dir*ab).b;
    float sl=sin(vUv.y*uRes.y*3.14159)*0.5+0.5; col*=1.0-uScan*(1.0-sl);
    col+=(h2(vUv*uRes+fract(uTime)*91.0)-0.5)*uGrain;
    col*=1.0-uVig*smoothstep(0.3,0.95,length(vUv-0.5)*1.3);
    col+=uFlash; col=max(col,0.0);
    gl_FragColor=vec4(col,1.0);
  }`
};

// 画质档位：高 = 原画；中 = 0.75 倍分辨率、2x 抗锯齿；低 = 半分辨率、无抗锯齿、关闭泛光（优先保证帧率）
export const QUALITY = {
  high:   { scale: 1.0,  samples: 4, bloom: true,  name: '高' },
  medium: { scale: 0.75, samples: 2, bloom: true,  name: '中' },
  low:    { scale: 0.5,  samples: 0, bloom: false, name: '低' }
};

export function createPost(renderer, W, H, quality = 'high') {
  let composer = null, rp = null, bloom = null, fx = null;
  // 切换画质时重建后期管线（分辨率、抗锯齿、泛光）；场景本身不变
  function build(name) {
    const q = QUALITY[name] || QUALITY.high;
    if (composer) { composer.renderTarget1.dispose(); composer.renderTarget2.dispose(); bloom.dispose(); fx.dispose && fx.dispose(); }
    const w = Math.max(2, Math.round(W * q.scale)), h = Math.max(2, Math.round(H * q.scale));
    const rt = new THREE.WebGLRenderTarget(w, h, { type: THREE.HalfFloatType, samples: q.samples });
    composer = new EffectComposer(renderer, rt); composer.setSize(w, h);
    rp = new RenderPass(new THREE.Scene(), new THREE.PerspectiveCamera());
    bloom = new UnrealBloomPass(new THREE.Vector2(w, h), 0.9, 0.55, 0.12); bloom.enabled = q.bloom;
    fx = new ShaderPass(FX); fx.uniforms.uRes.value.set(w, h);
    composer.addPass(rp); composer.addPass(bloom); composer.addPass(fx); composer.addPass(new OutputPass());
    renderer.setSize(w, h, false);
    Object.assign(post, { quality: name, composer, bloom, fx });
  }
  const post = {
    quality: 'high', composer: null, bloom: null, fx: null,
    // 每帧由场景写入的状态（reset() 恢复默认）
    s: {},
    reset() {
      this.s = { bloom: 0.6, bloomR: 0.45, bloomT: 0.6, ab: 0.0022, glitch: 0, scan: 0.1, grain: 0.04, vig: 0.4, flash: [0, 0, 0], track: 0, warp: 0, pix: 0 };
    },
    setQuality(name) { if (QUALITY[name] && name !== this.quality) build(name); },
    render(scene, camera, t) {
      const s = this.s; rp.scene = scene; rp.camera = camera;
      if (bloom.enabled) { bloom.strength = s.bloom; bloom.radius = s.bloomR; bloom.threshold = s.bloomT; }
      const u = fx.uniforms; u.uTime.value = t; u.uAb.value = s.ab; u.uGlitch.value = s.glitch; u.uScan.value = s.scan; u.uGrain.value = s.grain;
      u.uVig.value = s.vig; u.uFlash.value.setRGB(s.flash[0], s.flash[1], s.flash[2]); u.uTrack.value = s.track; u.uWarp.value = s.warp; u.uPix.value = s.pix;
      composer.render();
    }
  };
  build(quality);
  post.reset();
  return post;
}
