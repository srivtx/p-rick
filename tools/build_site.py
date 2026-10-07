#!/usr/bin/env python3
"""Build p-rick site: blog pages, RSS feed, and sitemap (dual-theme site)."""
import os
import re
import html as html_mod

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLOGS_MD = os.path.join(BASE, 'blogs')
BLOG_OUT = os.path.join(BASE, 'blog')
SITE_URL = 'https://srivtx.github.io/p-rick'
BUILD_DATE = '2026-10-07'

BLOGS = [
    ('2026-10-07-your-phone-sees-everything.md', 'blog/p001.html', 'P-001',
     'The Personal Event Bus', 'p-001'),
    ('2026-10-07-largest-unclaimed-money.md', 'blog/p002.html', 'P-002',
     'Consumer Entitlements as Dead Capital', 'p-002'),
    ('2026-10-07-your-inflation-is-not-the-cpi.md', 'blog/p003.html', 'P-003',
     'The n=1 Cost-of-Living Index', 'p-003'),
    ('2026-10-07-your-software-has-a-second-behavior.md', 'blog/p004.html', 'P-004',
     'Degradation Contracts', 'p-004'),
    ('2026-10-07-files-forgot-who-they-are.md', 'blog/p005.html', 'P-005',
     'Provenance-Native Storage', 'p-005'),
    ('2026-10-07-the-most-important-scheduler.md', 'blog/p006.html', 'P-006',
     'The Attention Scheduler', 'p-006'),
    ('2026-10-07-you-own-a-distributed-computer.md', 'blog/p007.html', 'P-007',
     'The Intermittent Compute Fabric', 'p-007'),
    ('2026-10-07-the-company-died-your-lights.md', 'blog/p008.html', 'P-008',
     'The Afterlife of Devices', 'p-008'),
    ('2026-10-07-calendar-average-human.md', 'blog/p009.html', 'P-009',
     'Circadian Orchestration', 'p-009'),
    ('2026-10-07-xz-wasnt-a-hack.md', 'blog/p010.html', 'P-010',
     'The Bus Factor Protocol', 'p-010'),
    ('2026-10-07-we-preserve-films-and-seeds.md', 'blog/p011.html', 'P-011',
     'Model Extinction', 'p-011'),
    ('2026-10-07-every-simplification-is-a-relocation.md', 'blog/p012.html', 'P-012',
     'The Complexity Ledger', 'p-012'),
    ('2026-10-07-software-assumes-one-person.md', 'blog/p013.html', 'P-013',
     'Delegated Operation', 'p-013'),
    ('2026-10-07-your-senses-have-no-failover.md', 'blog/p014.html', 'P-014',
     'Modality Failover', 'p-014'),
    ('2026-10-07-the-spreadsheet-lied.md', 'blog/p015.html', 'P-015',
     'The Uncertain Document', 'p-015'),
    ('2026-10-07-defaults-are-legislation.md', 'blog/p016.html', 'P-016',
     'The Defaults Ledger', 'p-016'),
    ('2026-10-07-you-can-withdraw-anytime.md', 'blog/p017.html', 'P-017',
     'The Revocation Protocol', 'p-017'),
    ('2026-10-07-your-data-has-a-shelf-life.md', 'blog/p018.html', 'P-018',
     'Epistemic Half-Life', 'p-018'),
    ('2026-10-07-the-drawer-is-not-a-vault.md', 'blog/p019.html', 'P-019',
     'Dormancy Engineering', 'p-019'),
    ('2026-10-07-everything-shares-one-fuse.md', 'blog/p020.html', 'P-020',
     'Blast Radius Engineering', 'p-020'),
]

NO_FLASH = (
    "<script>(function(){try{var t=localStorage.getItem('p-rick-theme');"
    "if(!t){t=window.matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light';}"
    "document.documentElement.setAttribute('data-theme',t);}"
    "catch(e){document.documentElement.setAttribute('data-theme','dark');}})();</script>"
)

TEMPLATE = """<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} — p-rick</title>
<meta name="description" content="{desc}">
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
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;0,900;1,400&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="../assets/style.css">
</head>
<body>
<header class="site-header">
  <a class="brand" href="../index.html"><span class="brand-mark">p-rick</span><span class="brand-sub">research</span></a>
  <div class="header-right">
    <nav><a href="../papers.html">Papers</a><a href="../blog.html">Blog</a><a href="../method.html">Method</a><a href="../index.html#about">About</a><a href="https://github.com/srivtx/p-rick">GitHub</a></nav>
    <button class="theme-toggle" aria-label="Toggle dark / light mode" title="Toggle dark / light mode">
      <svg class="icon-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>
      <svg class="icon-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
    </button>
  </div>
</header>
<main class="blog-main">
  <article class="post">
    <div class="post-kicker">essay &middot; companion to {paper}</div>
    <h1 class="post-title">{title}</h1>
    <div class="post-meta">{date} &middot; p-rick research program</div>
    {body}
    <div class="post-footer">
      <p>This essay accompanies the research paper <a href="../pdfs/{pdf}.pdf">{paper_full} (PDF)</a>.
      Working papers and sources live in the <a href="https://github.com/srivtx/p-rick">p-rick repository</a>;
      the work ledger is <a href="https://github.com/srivtx/p-rick/blob/main/agents.md">agents.md</a>.</p>
    </div>
  </article>
</main>
<footer class="site-footer">
  <div class="footer-inner">
    <div>
      <div class="f-brand">p-rick</div>
      <div class="f-note">an independent research program on missing software &middot; papers, PDFs, essays</div>
    </div>
    <div class="footer-links">
      <a href="../index.html">Home</a><a href="../papers.html">Papers</a><a href="../blog.html">Blog</a><a href="../method.html">Method</a><a href="{site}/feed.xml">RSS</a><a href="https://github.com/srivtx/p-rick">GitHub</a>
    </div>
  </div>
</footer>
<script src="../assets/theme.js"></script>
</body>
</html>
"""


def inline(s):
    s = html_mod.escape(s, quote=False)
    s = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', s)
    s = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'(?<!\w)\*([^*\n]+)\*(?!\w)', r'<em>\1</em>', s)
    s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
    return s


def md_to_html(md):
    lines = md.split('\n')
    out = []
    in_list = None
    para = []

    def flush_para():
        if para:
            out.append('<p>' + inline(' '.join(para)) + '</p>')
            para.clear()

    def flush_list():
        nonlocal in_list
        if in_list:
            out.append('</%s>' % in_list)
            in_list = None

    for raw in lines:
        ln = raw.rstrip()
        if not ln.strip():
            flush_para()
            flush_list()
            continue
        if ln.startswith('### '):
            flush_para(); flush_list()
            out.append('<h3>' + inline(ln[4:]) + '</h3>')
        elif ln.startswith('## '):
            flush_para(); flush_list()
            out.append('<h2>' + inline(ln[3:]) + '</h2>')
        elif ln.startswith('# '):
            flush_para(); flush_list()
            out.append('<h2>' + inline(ln[2:]) + '</h2>')  # post title is the h1 already
        elif re.match(r'^[-*] ', ln):
            flush_para()
            if in_list != 'ul':
                flush_list(); out.append('<ul>'); in_list = 'ul'
            out.append('<li>' + inline(ln[2:]) + '</li>')
        elif re.match(r'^\d+\. ', ln):
            flush_para()
            if in_list != 'ol':
                flush_list(); out.append('<ol>'); in_list = 'ol'
            out.append('<li>' + inline(re.sub(r'^\d+\. ', '', ln)) + '</li>')
        elif ln.startswith('> '):
            flush_para(); flush_list()
            out.append('<blockquote><p>' + inline(ln[2:]) + '</p></blockquote>')
        elif ln.strip() in ('---', '***'):
            flush_para(); flush_list()
            out.append('<hr>')
        else:
            flush_list()
            para.append(ln.strip())

    flush_para()
    flush_list()
    return '\n    '.join(out)


def parse_front_matter(md):
    fm = {}
    body = md
    m = re.match(r'^---\s*\n(.*?)\n---\s*\n?(.*)$', md, re.S)
    if m:
        for line in m.group(1).split('\n'):
            if ':' in line:
                k, v = line.split(':', 1)
                fm[k.strip()] = v.strip().strip('"')
        body = m.group(2)
    return fm, body


def build_feed(items):
    """RSS 2.0 feed of essays, newest series first (list order preserved)."""
    esc = html_mod.escape
    rows = []
    for it in items:
        rows.append('    <item>')
        rows.append('      <title>%s</title>' % esc(it['title']))
        rows.append('      <link>%s/%s</link>' % (SITE_URL, it['path']))
        rows.append('      <guid isPermaLink="true">%s/%s</guid>' % (SITE_URL, it['path']))
        rows.append('      <description>%s</description>' % esc(it['desc']))
        rows.append('      <pubDate>%s</pubDate>' % it['pubdate'])
        rows.append('    </item>')
    feed = '\n'.join([
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">',
        '  <channel>',
        '    <title>p-rick research program — essays</title>',
        '    <link>%s</link>' % SITE_URL,
        '    <description>Essays accompanying the p-rick working papers on missing software: the argument in plain language, written the way technical leaders write.</description>',
        '    <language>en</language>',
        '    <lastBuildDate>%s</lastBuildDate>' % items[0]['pubdate'],
        '    <atom:link href="%s/feed.xml" rel="self" type="application/rss+xml"/>' % SITE_URL,
        '\n'.join(rows),
        '  </channel>',
        '</rss>',
        '',
    ])
    path = os.path.join(BASE, 'feed.xml')
    open(path, 'w', encoding='utf-8').write(feed)
    print('wrote feed.xml (%d items)' % len(items))


def build_sitemap(paths):
    urls = ['    <loc>%s/%s</loc>' % (SITE_URL, p) for p in paths]
    body = '\n'.join('  <url>\n%s\n  </url>' % u for u in urls)
    sm = '\n'.join([
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        body,
        '</urlset>',
        '',
    ])
    path = os.path.join(BASE, 'sitemap.xml')
    open(path, 'w', encoding='utf-8').write(sm)
    print('wrote sitemap.xml (%d urls)' % len(paths))


def main():
    os.makedirs(BLOG_OUT, exist_ok=True)
    feed_items = []
    for md_name, out_rel, paper, paper_full, pdf in BLOGS:
        path = os.path.join(BLOGS_MD, md_name)
        if not os.path.exists(path):
            print('MISSING:', md_name)
            continue
        raw = open(path, encoding='utf-8').read()
        fm, body_md = parse_front_matter(raw)
        title = fm.get('title', md_name)
        date = fm.get('date', '')
        # strip leading "# Title" dup (title is in the h1)
        body_md = re.sub(r'^#\s+.*\n+', '', body_md, count=1)
        desc = re.sub(r'[<>]', '', inline(body_md[:180]).replace('<p>', '').replace('</p>', '')) + '…'
        body = md_to_html(body_md)
        html_out = TEMPLATE.format(
            noflash=NO_FLASH, title=inline(title), desc=desc.strip()[:300],
            paper=paper, paper_full=paper_full, date=date, body=body, pdf=pdf,
            og_url='%s/%s' % (SITE_URL, out_rel), site=SITE_URL,
            date_iso='%sT00:00:00Z' % date)
        out_path = os.path.join(BASE, out_rel)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        open(out_path, 'w', encoding='utf-8').write(html_out)
        print('wrote', out_rel, '(%d chars)' % len(html_out))
        # RFC 822 pubDate (statically dated essays; UTC)
        y, m, d = date.split('-')
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug',
                  'Sep', 'Oct', 'Nov', 'Dec']
        feed_items.append({
            'title': title, 'path': out_rel, 'desc': desc.strip()[:280],
            'pubdate': '%s %s %s 00:00:00 +0000' % (
                d.zfill(2), months[int(m) - 1], y)})
    # feed: newest series first (reverse of file order)
    build_feed(list(reversed(feed_items)))
    # sitemap: all pages + PDFs
    pages = ['', 'papers.html', 'blog.html', 'method.html', '404.html',
             'og-image.png', 'feed.xml']
    pages += ['blog/p%03d.html' % n for n in range(1, 21)]
    pages += ['pdfs/p-%03d.pdf' % n for n in range(1, 21)]
    build_sitemap(pages)


if __name__ == '__main__':
    main()
