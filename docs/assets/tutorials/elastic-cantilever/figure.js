const root = document.documentElement;

function resolveSiteTheme() {
  try {
    return window.parent.document.body.dataset.mdColorScheme === "slate"
      ? "dark"
      : "light";
  } catch (_error) {
    return window.matchMedia("(prefers-color-scheme: dark)").matches
      ? "dark"
      : "light";
  }
}

function applySiteTheme() {
  root.dataset.theme = resolveSiteTheme();
}

window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", applySiteTheme);

try {
  const observer = new MutationObserver(applySiteTheme);
  observer.observe(window.parent.document.body, {
    attributes: true,
    attributeFilter: ["data-md-color-scheme"],
  });
} catch (_error) {
  // A standalone figure follows the operating-system preference.
}

applySiteTheme();
