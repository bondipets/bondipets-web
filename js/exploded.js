// Exploded view — scroll-driven frame sequence + ingredient labels
// Hooks: cambiarFrame(progress) and mostrarLabel(index, visible) are placeholders
// to be wired up once the 36 chew frames are generated.

(function(){
  var wrapper = document.querySelector('.exploded-wrapper');
  if(!wrapper) return;

  // ── Smooth scroll (Lenis) ────────────────────────────────────────────────
  var lenis = new Lenis({
    lerp: 0.1,
    smoothWheel: true
  });

  function raf(time){
    lenis.raf(time);
    requestAnimationFrame(raf);
  }
  requestAnimationFrame(raf);

  // ── GSAP + ScrollTrigger ─────────────────────────────────────────────────
  gsap.registerPlugin(ScrollTrigger);

  // Keep ScrollTrigger in sync with Lenis
  lenis.on('scroll', ScrollTrigger.update);
  gsap.ticker.add(function(time){ lenis.raf(time * 1000); });
  gsap.ticker.lagSmoothing(0);

  // ── Main scroll trigger: 600vh wrapper, 100vh sticky inside ──────────────
  ScrollTrigger.create({
    trigger: wrapper,
    start: 'top top',
    end: 'bottom bottom',
    scrub: true,
    onUpdate: function(self){
      var progress = self.progress; // 0 → 1 across the full 600vh
      cambiarFrame(progress);
      actualizarLabels(progress);
    }
  });

  // ── Frame swapper (placeholder) ──────────────────────────────────────────
  // Will eventually swap `images/frames/chew-frame-XX.webp` based on progress.
  var TOTAL_FRAMES = 36;
  function cambiarFrame(progress){
    // TODO: connect when frames 01–36 are generated
    // var idx = Math.min(TOTAL_FRAMES, Math.max(1, Math.round(progress * (TOTAL_FRAMES - 1)) + 1));
    // var pad = idx < 10 ? '0' + idx : '' + idx;
    // var img = document.getElementById('exploded-chew-img');
    // if(img) img.src = 'images/frames/chew-frame-' + pad + '.webp';
  }

  // ── Label visibility (placeholder) ───────────────────────────────────────
  // Each ingredient label gets its own progress window. Values below are
  // evenly spaced starting points — tune once the animation choreography is set.
  var LABEL_WINDOWS = [
    [0.10, 0.95], // 0 Glucosamina
    [0.20, 0.95], // 1 Condroitina
    [0.30, 0.95], // 2 MSM
    [0.45, 0.95], // 3 Cúrcuma + Piperina
    [0.60, 0.95], // 4 Mejillón Verde
    [0.75, 0.95]  // 5 Probiótico
  ];

  function mostrarLabel(index, visible){
    var el = document.querySelector('.exploded-label[data-label-index="' + index + '"]');
    if(!el) return;
    gsap.to(el, { opacity: visible ? 1 : 0, duration: 0.35, overwrite: 'auto' });
  }

  function actualizarLabels(progress){
    for(var i = 0; i < LABEL_WINDOWS.length; i++){
      var w = LABEL_WINDOWS[i];
      var shouldShow = progress >= w[0] && progress <= w[1];
      mostrarLabel(i, shouldShow);
    }
  }
})();
