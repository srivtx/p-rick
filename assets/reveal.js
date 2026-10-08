/* p-rick reveal-on-scroll — subtle, compositor-friendly (opacity/transform only),
   disabled under prefers-reduced-motion via CSS. */
(function () {
  if (!('IntersectionObserver' in window)) return;
  var els = document.querySelectorAll('.reveal');
  if (!els.length) return;
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (e.isIntersecting) {
        e.target.classList.add('in');
        io.unobserve(e.target);
      }
    });
  }, { rootMargin: '0px 0px -8% 0px', threshold: 0.05 });
  els.forEach(function (el) { io.observe(el); });
})();
