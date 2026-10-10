#!/usr/bin/env python3
"""Shared template pieces for p-rick paper pages (used by build_paper_pages.py)."""

SITE = 'https://srivtx.github.io/p-rick'
GH = 'https://github.com/srivtx/p-rick'

NO_FLASH = (
    "<script>(function(){var t=null;"
    "try{t=localStorage.getItem('p-rick-theme');}catch(e){}"
    "if(t!=='light'&&t!=='dark'){"
    "t=(window.matchMedia&&window.matchMedia('(prefers-color-scheme: dark)').matches)?'dark':'light';}"
    "document.documentElement.setAttribute('data-theme',t);})();</script>"
)

KATEX = """<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css" crossorigin="anonymous">
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js" crossorigin="anonymous"></script>
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js" crossorigin="anonymous" onload="renderMathInElement(document.body,{delimiters:[{left:'$$',right:'$$',display:true},{left:'$',right:'$',display:false}],throwOnError:false,strict:false})"></script>"""

MASTHEAD = """<header class="site-header">
  <div class="masthead">
    <a class="brand" href="../index.html"><span class="brand-mark">p-rick</span><span class="brand-sub">research program</span></a>
    <nav aria-label="Primary">
      <a href="../papers.html" aria-current="page">Papers</a>
      <a href="../blog.html">Essays</a>
      <a href="../method.html">Method</a>
      <a href="https://github.com/srivtx/p-rick">GitHub</a>
    </nav>
    <button class="theme-toggle" aria-label="Toggle dark or light theme" title="Theme (t)">
      <svg class="icon-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>
      <svg class="icon-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
    </button>
  </div>
</header>"""

FOOTER = """<footer class="site-footer">
  <div class="footer-inner">
    <div>
      <div class="f-brand">p-rick</div>
      <div class="f-note">An independent research program on missing software &mdash; working papers, typeset PDFs, companion essays, open harnesses.</div>
      <div class="f-colophon">
        set in fraunces, inter &amp; ibm plex mono &middot; papers cc by 4.0 &middot; code mit<br>
        figures regenerate from code in the repository &middot; srivtx.github.io/p-rick
      </div>
    </div>
    <nav class="footer-links" aria-label="Footer">
      <a href="../index.html">Home</a><a href="../papers.html">Papers</a><a href="../blog.html">Essays</a><a href="../method.html">Method</a><a href="https://srivtx.github.io/p-rick/feed.xml">RSS</a><a href="https://github.com/srivtx/p-rick">GitHub</a>
    </nav>
  </div>
</footer>"""

SCROLLSPY = """<script>
(function(){
  var links = document.querySelectorAll('.paper-toc a[href^="#"]');
  if (!links.length) return;
  var map = {};
  links.forEach(function(a){ map[a.getAttribute('href').slice(1)] = a; });
  var heads = Array.prototype.slice.call(
    document.querySelectorAll('.paper-body h2[id], .paper-body h3[id]'));
  var ticking = false;
  function update(){
    ticking = false;
    var band = window.innerHeight * 0.25;
    var current = null;
    for (var i = 0; i < heads.length; i++) {
      if (heads[i].getBoundingClientRect().top <= band) {
        if (map[heads[i].id]) current = heads[i];
      } else break;
    }
    links.forEach(function(a){ a.classList.remove('on'); });
    if (current) { map[current.id].classList.add('on'); }
    else if (links.length) { links[0].classList.add('on'); }
  }
  window.addEventListener('scroll', function(){
    if (!ticking) { ticking = true; requestAnimationFrame(update); }
  }, { passive: true });
  window.addEventListener('resize', update);
  update();
})();
</script>"""

TEMPLATE = """<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} — p-rick {pid}</title>
<meta name="description" content="{desc}">
<meta name="theme-color" content="#15161a" media="(prefers-color-scheme: dark)">
<meta name="theme-color" content="#fbfaf6" media="(prefers-color-scheme: light)">
<link rel="canonical" href="{og_url}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="p-rick research program">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{og_url}">
<meta property="og:image" content="{site}/og-image.png">
<meta property="article:published_time" content="{date_iso}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{desc}">
<meta name="twitter:image" content="{site}/og-image.png">
<link rel="icon" href="../assets/favicon.svg" type="image/svg+xml">
<link rel="alternate" type="application/rss+xml" title="p-rick essays" href="{site}/feed.xml">
{noflash}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300..700;1,9..144,300..700&family=Inter:ital,wght@0,400..700;1,400..600&family=IBM+Plex+Mono:ital,wght@0,400;0,500;1,400&display=swap" rel="stylesheet">
<link rel="stylesheet" href="../assets/style.css">
<link rel="stylesheet" href="../assets/paper.css">
{katex}
<script type="application/ld+json">{jsonld}</script>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
{masthead}
<main id="main" class="page">
  <article class="paper">
    <header class="paper-head">
      <p class="paper-kicker">working paper {pid} &middot; series {series_label}</p>
      <h1 class="paper-title">{title}</h1>
      <div class="paper-meta">{meta_line}</div>
      <div class="paper-actions">
        <a class="pa pa-lead" href="../pdfs/{pdf}.pdf" download>typeset PDF</a>
        <a class="pa" href="{src_url}">source&thinsp;.md</a>
        <a class="pa" href="../blog/{essay}.html">companion essay</a>
{harness_link}
      </div>
    </header>
{revision}
    <section class="paper-abstract" aria-label="Abstract">
      <div class="abs-label">abstract</div>
      <p class="abs-text">{abstract}</p>
      <div class="abs-kw"><span class="kw-label">keywords</span>{keywords}</div>
    </section>
    <div class="paper-layout">
      <nav class="paper-toc" aria-label="Contents">
        <div class="ptoc-label">contents</div>
        {toc}
      </nav>
      <div class="paper-body">
{body}
      </div>
    </div>
    <nav class="paper-nav" aria-label="Paper navigation">
{prev}<a class="pn pn-all" href="../papers.html"><span class="pn-k">all papers</span><span class="pn-t">30 working papers &rarr;</span></a>{next}
    </nav>
    <section class="paper-cite" aria-label="How to cite">
      <div class="cite-label">cite</div>
      <pre class="bibtex-block">{bibtex}</pre>
      <p class="cite-note">Working paper, self-published with open harnesses and multi-seed data; not peer-reviewed. Figures regenerate from seeded code in the repository. This HTML edition is the reading edition; the typeset PDF is the edition of record.</p>
    </section>
  </article>
</main>
{footer}
<script src="../assets/theme.js"></script>
<script src="../assets/reveal.js"></script>
{scrollspy}
</body>
</html>
"""
