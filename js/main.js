(() => {
  // 1. Reveal on scroll — fast-path para los que ya están en viewport al cargar
  const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('in');
        revealObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.15, rootMargin: '0px 0px -40px 0px' });
  const viewportH = window.innerHeight;
  document.querySelectorAll('.reveal').forEach(el => {
    const rect = el.getBoundingClientRect();
    const inViewport = rect.top < viewportH && rect.bottom > 0;
    if (inViewport) {
      el.classList.add('in');
    } else {
      revealObserver.observe(el);
    }
  });

  // 2. Parallax sutil en hero-visual
  const heroVisual = document.querySelector('.hero-visual');
  if (heroVisual) {
    window.addEventListener('scroll', () => {
      heroVisual.style.transform = `translateY(${window.scrollY * 0.08}px)`;
    }, { passive: true });
  }

  // 3. FAQ accordion (todas clickables)
  document.querySelectorAll('.faq-q').forEach(btn => {
    btn.addEventListener('click', () => {
      btn.closest('.faq-item').classList.toggle('open');
    });
  });

  // 4. Email forms + toast + MailerLite (iframe target)
  const toastEl = document.querySelector('.toast');
  const showToast = (msg) => {
    if (!toastEl) return;
    toastEl.textContent = msg;
    toastEl.classList.add('show');
    setTimeout(() => toastEl.classList.remove('show'), 2400);
  };
  const mlForm = document.getElementById('ml-form');
  const mlEmail = document.getElementById('ml-email');
  const mlTarget = document.getElementById('ml-target');

  document.querySelectorAll('.email-form').forEach(form => {
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      const input = form.querySelector('input[type="email"]');
      const btn = form.querySelector('button');
      if (!input.value.includes('@')) {
        input.style.outline = '2px solid #B3261E';
        setTimeout(() => { input.style.outline = ''; }, 1000);
        return;
      }
      if (!mlForm || !mlEmail || !mlTarget) {
        // Fallback si falta el hidden form — no debería pasar en prod.
        showToast('Error, intenta de nuevo');
        return;
      }
      btn.disabled = true;
      const original = btn.textContent;
      mlEmail.value = input.value;

      let settled = false;
      const onLoad = () => {
        if (settled) return;
        settled = true;
        mlTarget.removeEventListener('load', onLoad);
        form.classList.add('success');
        btn.textContent = '¡Hecho ✓';
        showToast('¡Hecho! Te avisamos 48h antes del lanzamiento.');
        setTimeout(() => {
          input.value = '';
          form.classList.remove('success');
          btn.textContent = original;
          btn.disabled = false;
        }, 2500);
      };
      mlTarget.addEventListener('load', onLoad);
      setTimeout(() => {
        if (settled) return;
        settled = true;
        mlTarget.removeEventListener('load', onLoad);
        btn.disabled = false;
        input.style.outline = '2px solid #B3261E';
        setTimeout(() => { input.style.outline = ''; }, 1000);
        showToast('Error, intenta de nuevo');
      }, 8000);
      mlForm.submit();
    });
  });

  // 5. Smooth scroll con offset 60px para anchors internos
  const NAV_OFFSET = 60;
  document.querySelectorAll('a[href^="#"]').forEach(link => {
    link.addEventListener('click', (e) => {
      const href = link.getAttribute('href');
      if (href === '#' || href.length < 2) return;
      const target = document.getElementById(href.slice(1));
      if (!target) return;
      e.preventDefault();
      window.scrollTo({
        top: target.getBoundingClientRect().top + window.scrollY - NAV_OFFSET,
        behavior: 'smooth'
      });
    });
  });

  // 6. Lang toggle ES/EN (cosmético; cambio real de idioma en sesión posterior)
  document.querySelectorAll('.lang-toggle button').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.lang-toggle button').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
    });
  });
})();
