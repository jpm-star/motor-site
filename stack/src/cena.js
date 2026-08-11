/* CENA — GSAP + ScrollTrigger. Pin + scrub.
 *
 * POR QUE GSAP AQUI E NÃO CSS: a camada CSS (app/motion.py, 1,7 KB) já faz reveal,
 * stagger, parallax e tipografia cinética — `animation-timeline: view()` cobre tudo
 * isso de graça. O que ela NÃO faz é PIN: travar a seção na tela e rodar uma
 * sequência encadeada enquanto o scroll avança. Não existe primitiva CSS pra isso.
 * É o efeito assinatura do Lusion, e é a única razão de esta lib existir no bundle.
 *
 * DEGRADAÇÃO: sem JS os passos ficam todos visíveis, empilhados e legíveis. Quem
 * esconde é o GSAP, nunca o CSS — senão um erro de rede apaga o conteúdo da página.
 */
import gsap from 'gsap'
import ScrollTrigger from 'gsap/ScrollTrigger'

gsap.registerPlugin(ScrollTrigger)

export function ligar() {
  const cenas = document.querySelectorAll('[data-cena]')
  let ligadas = 0

  for (const cena of cenas) {
    const passos = cena.querySelectorAll('[data-passo]')
    if (passos.length < 2) continue // 1 passo não é sequência, é um bloco parado

    // altura da zona pinada = quanto scroll o visitante gasta atravessando a cena.
    // 70svh por passo dá tempo de ler sem parecer que a página travou.
    const tl = gsap.timeline({
      scrollTrigger: {
        trigger: cena,
        start: 'top top',
        end: () => `+=${passos.length * 70}%`,
        pin: true,
        // scrub com inércia: o movimento acompanha o dedo mas não treme a cada pixel
        scrub: 0.6,
        anticipatePin: 1,
        invalidateOnRefresh: true,
      },
    })

    // libera o layout sobreposto (CSS em stack_pesada.css_cena) só agora que há
    // quem revele os passos — antes disto o grid empilhado é o certo
    cena.classList.add('cena-ativa')

    // O PRIMEIRO PASSO JÁ NASCE VISÍVEL. Animá-lo a partir de autoAlpha:0 deixava a
    // cena PINADA E VAZIA no instante em que ela trava na tela — o visitante trava o
    // scroll olhando pro nada e acha que o site quebrou. Só do segundo em diante há
    // o que revelar; o primeiro apenas sai.
    gsap.set([...passos].slice(1), { autoAlpha: 0, y: 48 })

    passos.forEach((passo, i) => {
      if (i > 0) tl.to(passo, { autoAlpha: 1, y: 0, duration: 1 }, i)
      // último passo não sai: a cena termina com ele na tela, senão o visitante
      // destrava o pin olhando pra uma seção vazia
      if (i < passos.length - 1) tl.to(passo, { autoAlpha: 0, y: -48, duration: 1 }, i + 1)
    })
    ligadas++
  }

  // fontes web mudam a altura do texto DEPOIS do cálculo do pin; sem isto a cena
  // termina alguns pixels fora do lugar em quem não tem a fonte em cache
  if (ligadas && document.fonts) document.fonts.ready.then(() => ScrollTrigger.refresh())
  return ligadas
}
