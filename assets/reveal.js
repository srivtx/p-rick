/* p-rick reveal-on-scroll — subtle, compositor-friendly (opacity/transform only),
   disabled under prefers-reduced-motion via CSS.
   Hardened against instant jumps (anchor links, scroll restoration):
   any element at or above the viewport bottom is revealed on the next
   scroll/resize tick, even if the observer never saw it intersect. */
(function () {
  var els = document.querySelectorAll('.reveal');
  if (!els.length) return;
  var pending = Array.prototype.slice.call(els);

  function mark(el) {
    el.classList.add('in');
  }

  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) {
          mark(e.target);
          io.unobserve(e.target);
          var i = pending.indexOf(e.target);
          if (i !== -1) pending.splice(i, 1);
        }
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.05 });
    els.forEach(function (el) { io.observe(el); });
  }

  /* catch elements jumped past (instant scroll/anchor/restore) */
  var ticking = false;
  function sweep() {
    ticking = false;
    if (!pending.length) return;
    var vh = window.innerHeight || document.documentElement.clientHeight;
    pending = pending.filter(function (el) {
      var top = el.getBoundingClientRect().top;
      if (top < vh) { mark(el); return false; }
      return true;
    });
  }
  window.addEventListener('scroll', function () {
    if (!ticking) { ticking = true; requestAnimationFrame(sweep); }
  }, { passive: true });
  window.addEventListener('resize', function () {
    if (!ticking) { ticking = true; requestAnimationFrame(sweep); }
  }, { passive: true });
  requestAnimationFrame(sweep);
})();

/* p-rick site UI — auto-injected, no per-page markup required.
   1. mobile nav toggle (the masthead nav is display:none under 560px;
      this gives it a dropdown panel with a hamburger button)
   2. back-to-top button (appears after ~1.2 viewport heights of scroll) */
(function () {
  /* ---- mobile nav ---- */
  var mast = document.querySelector('.masthead');
  if (mast && !document.querySelector('.nav-toggle')) {
    var nav = mast.querySelector('nav');
    if (nav) {
      var btn = document.createElement('button');
      btn.className = 'nav-toggle';
      btn.setAttribute('aria-label', 'Toggle navigation menu');
      btn.setAttribute('aria-expanded', 'false');
      btn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><line x1="4" y1="7" x2="20" y2="7"/><line x1="4" y1="12" x2="20" y2="12"/><line x1="4" y1="17" x2="20" y2="17"/></svg>';
      var anchor = mast.querySelector('.theme-toggle');
      if (anchor) { mast.insertBefore(btn, anchor); } else { mast.appendChild(btn); }
      var close = function () {
        nav.classList.remove('open');
        btn.setAttribute('aria-expanded', 'false');
      };
      btn.addEventListener('click', function () {
        var open = nav.classList.toggle('open');
        btn.setAttribute('aria-expanded', open ? 'true' : 'false');
      });
      nav.addEventListener('click', function (ev) {
        if (ev.target && ev.target.closest && ev.target.closest('a')) close();
      });
      document.addEventListener('keydown', function (ev) {
        if (ev.key === 'Escape') close();
      });
    }
  }

  /* ---- back to top ---- */
  var top = document.createElement('button');
  top.className = 'top-btn';
  top.setAttribute('aria-label', 'Back to top');
  top.title = 'Back to top';
  top.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><line x1="12" y1="19" x2="12" y2="5"/><polyline points="5 12 12 5 19 12"/></svg>';
  document.body.appendChild(top);
  var update = function () {
    top.classList.toggle('show', (window.scrollY || window.pageYOffset) > window.innerHeight * 1.2);
  };
  var ticking = false;
  window.addEventListener('scroll', function () {
    if (!ticking) {
      ticking = true;
      requestAnimationFrame(function () { update(); ticking = false; });
    }
  }, { passive: true });
  update();
  top.addEventListener('click', function () {
    var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    try { window.scrollTo({ top: 0, behavior: reduce ? 'auto' : 'smooth' }); }
    catch (e) { window.scrollTo(0, 0); }
  });
})();
