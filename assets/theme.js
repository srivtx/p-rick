/* p-rick theme toggle — dark/light with persistence.
   The no-flash bootstrap runs inline in <head> of every page and reads
   localStorage('p-rick-theme') -> prefers-color-scheme -> light.
   This file only wires the toggle, cross-tab sync, and browser-chrome color.
*/
(function () {
  var KEY = 'p-rick-theme';
  var CHROME = { dark: '#15161a', light: '#fbfaf6' };

  function stored() {
    try {
      var t = localStorage.getItem(KEY);
      return (t === 'light' || t === 'dark') ? t : null;
    } catch (e) { return null; }
  }

  function syncChrome(theme) {
    var metas = document.querySelectorAll('meta[name="theme-color"]');
    for (var i = 0; i < metas.length; i++) {
      metas[i].setAttribute('content', CHROME[theme] || CHROME.light);
    }
  }

  function init() {
    syncChrome(document.documentElement.getAttribute('data-theme') || 'light');

    var btn = document.querySelector('.theme-toggle');
    if (!btn) return;
    btn.addEventListener('click', function () {
      var html = document.documentElement;
      var next = html.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      html.setAttribute('data-theme', next);
      syncChrome(next);
      try { localStorage.setItem(KEY, next); } catch (e) {}
    });

    // keep multiple open tabs in sync
    window.addEventListener('storage', function (ev) {
      if (ev.key === KEY && (ev.newValue === 'light' || ev.newValue === 'dark')) {
        document.documentElement.setAttribute('data-theme', ev.newValue);
        syncChrome(ev.newValue);
      }
    });

    // follow OS theme changes live, but only when the user has not
    // expressed an explicit preference (no stored value)
    if (window.matchMedia) {
      try {
        var mq = window.matchMedia('(prefers-color-scheme: dark)');
        var onChange = function (e) {
          if (stored()) return; // explicit user choice wins
          var t = e.matches ? 'dark' : 'light';
          document.documentElement.setAttribute('data-theme', t);
          syncChrome(t);
        };
        if (mq.addEventListener) { mq.addEventListener('change', onChange); }
        else if (mq.addListener) { mq.addListener(onChange); }
      } catch (e) {}
    }

    // keyboard shortcut: t toggles the theme (unless typing)
    document.addEventListener('keydown', function (ev) {
      var tag = (ev.target && ev.target.tagName) || '';
      if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' || ev.metaKey || ev.ctrlKey || ev.altKey) return;
      if (ev.key === 't' || ev.key === 'T') {
        btn.click();
      }
    });
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else { init(); }
})();
