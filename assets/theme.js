/* p-rick theme toggle — dark/light with persistence.
   NOTE: the no-flash bootstrap runs inline in <head> of every page:
   <script>(function(){try{var t=localStorage.getItem('p-rick-theme');if(!t){t=window.matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light';}document.documentElement.setAttribute('data-theme',t);}catch(e){document.documentElement.setAttribute('data-theme','dark');}})();</script>
*/
(function () {
  function init() {
    var btn = document.querySelector('.theme-toggle');
    if (!btn) return;
    btn.addEventListener('click', function () {
      var html = document.documentElement;
      var next = html.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      html.setAttribute('data-theme', next);
      try { localStorage.setItem('p-rick-theme', next); } catch (e) {}
    });
    // keep multiple open tabs in sync
    window.addEventListener('storage', function (ev) {
      if (ev.key === 'p-rick-theme' && ev.newValue) {
        document.documentElement.setAttribute('data-theme', ev.newValue);
      }
    });
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else { init(); }
})();
