/* CAMPO — Three.js. Fundo WebGL gerado por shader.
 *
 * POR QUE ISTO PAGA OS 118 KB: `app/motion_gap.py` lista o que CSS não entrega e
 * hoje manda o JP gerar um vídeo à mão no Higgsfield — morphing orgânico, fluido/
 * partículas, distorção em tempo real. São 3 dos 6 itens daquela lista. Um shader
 * resolve os três de uma vez, sem asset por cliente, sem crédito de vídeo, e
 * reagindo ao tema em vez de ser um MP4 fixo. A lib entra pra MATAR trabalho
 * manual recorrente, não pra enfeitar.
 *
 * SEM ASSET, SEM MODELO: nenhum GLB, nenhuma textura, nenhum download por cliente.
 * A cor sai das custom properties do tema — o mesmo bundle serve os 68 sites.
 *
 * A BATERIA É O RISCO REAL. Canvas WebGL rodando 60fps sem parar é o que faz site
 * "premium" ser fechado no celular. Este para de renderizar quando sai da tela,
 * quando a aba perde foco, e nunca passa de 1.5x de pixel ratio.
 */
import {
  WebGLRenderer, Scene, OrthographicCamera, PlaneGeometry,
  ShaderMaterial, Mesh, Vector2, Color, Clock,
} from 'three'

const VERT = `void main(){ gl_Position = vec4(position.xy, 0.0, 1.0); }`

/* fbm clássico (valor-ruído em 4 oitavas). Barato: sem textura, sem derivada,
 * sem loop dinâmico — roda liso até em GPU integrada velha. */
const FRAG = `
precision mediump float;
uniform vec2 uRes; uniform float uT;
uniform vec3 uA; uniform vec3 uB; uniform float uForca;

float hash(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453123); }
float ruido(vec2 p){
  vec2 i = floor(p), f = fract(p);
  vec2 u = f * f * (3.0 - 2.0 * f);
  return mix(mix(hash(i), hash(i + vec2(1,0)), u.x),
             mix(hash(i + vec2(0,1)), hash(i + vec2(1,1)), u.x), u.y);
}
float fbm(vec2 p){
  float v = 0.0, a = 0.5;
  for (int i = 0; i < 4; i++) { v += a * ruido(p); p *= 2.02; a *= 0.5; }
  return v;
}

void main(){
  vec2 uv = (gl_FragCoord.xy - 0.5 * uRes) / min(uRes.x, uRes.y);
  float t = uT * 0.06;
  // domain warping: o ruído desloca a própria coordenada. É isto que dá a
  // sensação de fluido/morfologia orgânica em vez de "textura animada".
  vec2 q = vec2(fbm(uv * 1.6 + t), fbm(uv * 1.6 + vec2(3.1, 1.7) - t));
  float n = fbm(uv * 2.2 + q * 1.4);
  vec3 cor = mix(uA, uB, smoothstep(0.25, 0.85, n));
  // vinheta radial: mantém o centro limpo pro texto que vai por cima
  float vig = smoothstep(1.15, 0.15, length(uv));
  gl_FragColor = vec4(cor, n * uForca * vig);
}`

function corDe(el, prop, alt) {
  const v = getComputedStyle(el).getPropertyValue(prop).trim()
  try { return new Color(v || alt) } catch { return new Color(alt) }
}

export function ligar() {
  const alvos = document.querySelectorAll('[data-campo]')
  const vivos = []

  for (const alvo of alvos) {
    let renderer
    try {
      renderer = new WebGLRenderer({
        alpha: true, antialias: false, powerPreference: 'low-power',
        // o fundo é decorativo: perder o contexto não pode custar uma tentativa
        // de recuperação cara. Falhou, some — o CSS por baixo continua ali.
        failIfMajorPerformanceCaveat: true,
      })
    } catch { continue } // sem WebGL: silêncio, o gradiente CSS assume

    const raiz = document.documentElement
    const uniforms = {
      uRes: { value: new Vector2(1, 1) },
      uT: { value: 0 },
      uA: { value: corDe(raiz, '--acento', '#00e6a2') },
      uB: { value: corDe(raiz, '--acento-2', '#4b7bec') },
      uForca: { value: parseFloat(alvo.dataset.campo) || 0.5 },
    }

    renderer.setPixelRatio(Math.min(devicePixelRatio || 1, 1.5))
    const cena = new Scene()
    const cam = new OrthographicCamera(-1, 1, 1, -1, 0, 1)
    cena.add(new Mesh(new PlaneGeometry(2, 2),
      new ShaderMaterial({ vertexShader: VERT, fragmentShader: FRAG, uniforms, transparent: true })))

    const cv = renderer.domElement
    Object.assign(cv.style, {
      position: 'absolute', inset: '0', width: '100%', height: '100%',
      pointerEvents: 'none', zIndex: '0',
      // o bundle chega DEPOIS do LCP, então o canvas sempre entra numa tela já
      // pintada. Sem o fade ele "estala" por cima do fundo CSS e o refino lê como
      // glitch de carregamento.
      opacity: '0', transition: 'opacity .9s ease',
    })
    cv.setAttribute('aria-hidden', 'true')
    if (getComputedStyle(alvo).position === 'static') alvo.style.position = 'relative'
    alvo.prepend(cv)

    const medir = () => {
      const r = alvo.getBoundingClientRect()
      renderer.setSize(r.width, r.height, false)
      uniforms.uRes.value.set(r.width, r.height)
    }
    medir()

    const relogio = new Clock()
    let rodando = false, id = 0, pintou = false
    const quadro = () => {
      // revela só depois do PRIMEIRO quadro real: se a GPU engasgar na compilação
      // do shader, o fade não começa a mostrar um canvas ainda vazio
      if (!pintou) { pintou = true; requestAnimationFrame(() => { cv.style.opacity = '1' }) }
      // o tempo avança com o DELTA, não com o total: voltar pra aba não faz o
      // shader dar um salto de vários segundos
      uniforms.uT.value += relogio.getDelta()
      renderer.render(cena, cam)
      id = requestAnimationFrame(quadro)
    }
    const tocar = (v) => {
      if (v === rodando) return
      rodando = v
      if (v) { relogio.getDelta(); id = requestAnimationFrame(quadro) }
      else cancelAnimationFrame(id)
    }

    // só renderiza o que está NA TELA e numa ABA ATIVA. As duas condições são
    // independentes e ambas precisam poder RETOMAR — guardar só um booleano
    // "rodando" faria a animação nunca voltar depois de trocar de aba.
    let naTela = false
    const avaliar = () => tocar(naTela && !document.hidden)
    const io = new IntersectionObserver(([e]) => { naTela = e.isIntersecting; avaliar() })
    io.observe(alvo)
    document.addEventListener('visibilitychange', avaliar)
    const ro = new ResizeObserver(medir)
    ro.observe(alvo)

    vivos.push({
      alvo,
      parar: () => {
        tocar(false); io.disconnect(); ro.disconnect()
        document.removeEventListener('visibilitychange', avaliar)
        renderer.dispose(); cv.remove()
      },
    })
  }
  return vivos.length
}
