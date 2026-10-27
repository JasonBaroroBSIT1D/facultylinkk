(function () {
  "use strict";

  var nav = document.getElementById("site-nav");
  var toggle = document.getElementById("nav-toggle");
  var menu = document.getElementById("nav-menu");
  var links = Array.prototype.slice.call(document.querySelectorAll(".nav-link[data-section]"));
  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

  /* Navbar becomes solid once the page scrolls. */
  function onScroll() {
    nav.classList.toggle("is-scrolled", window.scrollY > 24);
  }
  onScroll();
  window.addEventListener("scroll", onScroll, { passive: true });

  /* Mobile menu. */
  function setMenu(open) {
    nav.classList.toggle("menu-open", open);
    toggle.setAttribute("aria-expanded", open ? "true" : "false");
    toggle.setAttribute("aria-label", open ? "Close menu" : "Open menu");
  }
  toggle.addEventListener("click", function () {
    setMenu(toggle.getAttribute("aria-expanded") !== "true");
  });
  menu.addEventListener("click", function (event) {
    if (event.target.closest("a")) setMenu(false);
  });
  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && toggle.getAttribute("aria-expanded") === "true") {
      setMenu(false);
      toggle.focus();
    }
  });
  document.addEventListener("click", function (event) {
    if (!nav.contains(event.target)) setMenu(false);
  });
  window.matchMedia("(min-width: 861px)").addEventListener("change", function (query) {
    if (query.matches) setMenu(false);
  });

  /* Highlight the nav link of the section currently in view. */
  function setActive(id) {
    links.forEach(function (link) {
      var active = link.dataset.section === id;
      link.classList.toggle("is-active", active);
      if (active) link.setAttribute("aria-current", "true");
      else link.removeAttribute("aria-current");
    });
  }
  var sections = links.map(function (link) {
    return document.getElementById(link.dataset.section);
  }).filter(Boolean);

  if ("IntersectionObserver" in window) {
    var spy = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) setActive(entry.target.id);
      });
    }, { rootMargin: "-45% 0px -50% 0px", threshold: 0 });
    sections.forEach(function (section) { spy.observe(section); });
  }
  links.forEach(function (link) {
    link.addEventListener("click", function () { setActive(link.dataset.section); });
  });

  /* Smooth scrolling for in-page links (CSS handles it; this respects reduced motion). */
  document.querySelectorAll('a[href^="#"]').forEach(function (anchor) {
    anchor.addEventListener("click", function (event) {
      var target = document.getElementById(anchor.getAttribute("href").slice(1));
      if (!target) return;
      event.preventDefault();
      target.scrollIntoView({ behavior: reduceMotion.matches ? "auto" : "smooth", block: "start" });
      if (history.replaceState) history.replaceState(null, "", "#" + target.id);
    });
  });

  /* Arriving with a hash (for example login.html -> index.html#about): once images
     and fonts have settled, make sure the target sits just below the navbar. */
  window.addEventListener("load", function () {
    var id = decodeURIComponent(window.location.hash.slice(1));
    var target = id && document.getElementById(id);
    if (!target) return;
    var offset = parseFloat(getComputedStyle(document.documentElement).scrollPaddingTop) || 0;
    var drift = Math.abs(target.getBoundingClientRect().top - offset);
    if (drift > 2 && drift < 600) target.scrollIntoView({ behavior: "auto", block: "start" });
    if (sections.indexOf(target) !== -1) setActive(target.id);
  });

  /* Reveal elements as they scroll into view. */
  var items = Array.prototype.slice.call(document.querySelectorAll("[data-reveal]"));
  function showAll() {
    items.forEach(function (item) { item.classList.add("is-visible"); });
  }
  if (reduceMotion.matches || !("IntersectionObserver" in window)) {
    showAll();
  } else {
    var reveal = new IntersectionObserver(function (entries, observer) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        entry.target.classList.add("is-visible");
        observer.unobserve(entry.target);
      });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.12 });
    items.forEach(function (item) { reveal.observe(item); });
  }
})();
