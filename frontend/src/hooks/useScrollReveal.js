import { useEffect } from "react";

export function useScrollReveal(dependency) {
  useEffect(() => {
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const seen = new WeakSet();

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.14, rootMargin: "0px 0px -48px 0px" }
    );

    function reveal(items) {
      items.forEach((item, index) => {
        if (seen.has(item)) return;
        seen.add(item);

        if (reducedMotion) {
          item.classList.add("is-visible");
          return;
        }

        item.style.setProperty("--reveal-delay", `${Math.min(index * 45, 280)}ms`);
        observer.observe(item);
      });
    }

    function collect(root = document) {
      const items = [];
      if (root instanceof Element && root.matches("[data-reveal]")) {
        items.push(root);
      }
      items.push(...Array.from(root.querySelectorAll?.("[data-reveal]") || []));
      reveal(items);
    }

    collect();

    const mutationObserver = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        mutation.addedNodes.forEach((node) => collect(node));
      });
    });

    mutationObserver.observe(document.body, { childList: true, subtree: true });

    return () => {
      observer.disconnect();
      mutationObserver.disconnect();
    };
  }, [dependency]);
}
