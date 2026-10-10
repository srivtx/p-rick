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

/* p-rick image lightbox — auto-injected, no per-page markup required.
   Any anchor that wraps an <img> and points at an image opens the image
   in an in-page overlay (Esc / backdrop click / x button closes, arrow
   keys move between the page's figures) instead of navigating away to a
   raw image tab. Middle-click, "open in new tab", and no-JS keep the
   original anchor behavior. Caption comes from the enclosing figure's
   <figcaption> (falling back to the image's alt text). */
(function () {
  var IMG_RE = /\.(png|jpe?g|gif|webp|svg)([?#]|$)/i;
  if (!document.addEventListener) return;

  function collect() {
    var links = document.querySelectorAll('a[href]'), out = [], i;
    for (i = 0; i < links.length; i++) {
      var a = links[i];
      if (IMG_RE.test(a.getAttribute('href')) && a.querySelector('img')) {
        out.push(a);
      }
    }
    return out;
  }

  var box = null, cap = null, capNo = null, img = null,
      prev = null, next = null, closeBtn = null,
      items = [], idx = 0, lastFocus = null;

  function build() {
    box = document.createElement('div');
    box.className = 'lb-overlay';
    box.setAttribute('role', 'dialog');
    box.setAttribute('aria-modal', 'true');
    box.setAttribute('aria-label', 'Figure viewer — press Escape to close');
    closeBtn = document.createElement('button');
    closeBtn.className = 'lb-close';
    closeBtn.setAttribute('aria-label', 'Close figure viewer');
    closeBtn.textContent = '\u00d7';
    prev = document.createElement('button');
    prev.className = 'lb-prev';
    prev.setAttribute('aria-label', 'Previous figure');
    prev.innerHTML = '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="15 18 9 12 15 6"/></svg>';
    next = document.createElement('button');
    next.className = 'lb-next';
    next.setAttribute('aria-label', 'Next figure');
    next.innerHTML = '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="9 18 15 12 9 6"/></svg>';
    var fig = document.createElement('figure');
    fig.className = 'lb-fig';
    img = document.createElement('img');
    img.setAttribute('alt', '');
    cap = document.createElement('figcaption');
    cap.className = 'lb-cap';
    capNo = document.createElement('span');
    capNo.className = 'lb-no';
    var capText = document.createElement('span');
    capText.className = 'lb-text';
    cap.appendChild(capNo);
    cap.appendChild(capText);
    fig.appendChild(img);
    fig.appendChild(cap);
    box.appendChild(closeBtn);
    box.appendChild(prev);
    box.appendChild(fig);
    box.appendChild(next);
    document.body.appendChild(box);

    box.addEventListener('click', function (ev) {
      if (ev.target === box) hide();
    });
    closeBtn.addEventListener('click', hide);
    prev.addEventListener('click', function () { show(idx - 1); });
    next.addEventListener('click', function () { show(idx + 1); });
    document.addEventListener('keydown', function (ev) {
      if (!box.classList.contains('open')) return;
      if (ev.key === 'Escape') { ev.preventDefault(); hide(); }
      else if (ev.key === 'ArrowLeft') { ev.preventDefault(); show(idx - 1); }
      else if (ev.key === 'ArrowRight') { ev.preventDefault(); show(idx + 1); }
    });
  }

  function captionFor(a) {
    var fig = a.closest ? a.closest('figure') : null;
    var fc = fig ? fig.querySelector('figcaption') : null;
    var im = a.querySelector('img');
    var no = fc ? (fc.querySelector('.fig-no') || fc.querySelector('.fig-no-solo')) : null;
    var text = (fc ? fc.textContent : (im ? im.getAttribute('alt') : '')) || '';
    if (no) { text = text.replace(no.textContent, ''); }
    text = text.replace(/\s+/g, ' ').trim();
    return { no: no ? no.textContent.trim() : '', text: text };
  }

  function show(i) {
    if (!items.length) return;
    idx = (i + items.length) % items.length;
    var a = items[idx];
    img.setAttribute('src', a.getAttribute('href'));
    img.setAttribute('alt', captionFor(a).text || 'figure');
    var c = captionFor(a);
    capNo.textContent = c.no ? c.no + '  \u00b7  ' + (idx + 1) + ' / ' + items.length
                             : (idx + 1) + ' / ' + items.length;
    box.querySelector('.lb-text').textContent = c.text;
    var many = items.length > 1;
    prev.hidden = !many;
    next.hidden = !many;
    /* preload neighbours for snappy arrow navigation */
    if (many) {
      [items[(idx + 1) % items.length], items[(idx - 1 + items.length) % items.length]]
        .forEach(function (n) {
          var pre = new Image();
          pre.src = n.getAttribute('href');
        });
    }
  }

  function openAt(i) {
    if (!box) build();
    items = collect();
    lastFocus = document.activeElement;
    show(i);
    box.classList.add('open');
    document.documentElement.style.overflow = 'hidden';
    closeBtn.focus();
  }

  function hide() {
    if (!box) return;
    box.classList.remove('open');
    document.documentElement.style.overflow = '';
    if (lastFocus && lastFocus.focus) lastFocus.focus();
  }

  document.addEventListener('click', function (ev) {
    var a = ev.target.closest ? ev.target.closest('a[href]') : null;
    if (!a) return;
    if (!IMG_RE.test(a.getAttribute('href')) || !a.querySelector('img')) return;
    if (ev.metaKey || ev.ctrlKey || ev.shiftKey || ev.altKey || ev.button !== 0) return;
    ev.preventDefault();
    var list = collect();
    var i = list.indexOf(a);
    openAt(i < 0 ? 0 : i);
  }, false);
})();
