(function () {
  "use strict";

  function createElement(tag, className, textContent) {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (textContent) element.textContent = textContent;
    return element;
  }

  function createCard(example) {
    const card = createElement("a", "learning-card");
    card.href = `${example.slug}/`;
    card.dataset.categories = example.categories.join("|");

    const preview = createElement("div", "learning-card__preview");
    const frame = document.createElement("iframe");
    frame.src = example.preview;
    frame.title = example.previewTitle;
    frame.loading = "lazy";
    frame.tabIndex = -1;
    preview.appendChild(frame);

    const body = createElement("div", "learning-card__body");
    body.appendChild(
      createElement(
        "p",
        "learning-card__sequence",
        `${example.categories[0]} / ${example.level}`,
      ),
    );
    body.appendChild(createElement("h2", "", example.title));
    body.appendChild(createElement("p", "", example.summary));

    const metadata = createElement("div", "learning-card__meta");
    metadata.setAttribute("aria-label", "Example metadata");
    example.tags.forEach((tag) => metadata.appendChild(createElement("span", "", tag)));
    body.appendChild(metadata);

    const link = createElement("span", "learning-card__link", "View example ");
    const arrow = createElement("span", "", "\u2192");
    arrow.setAttribute("aria-hidden", "true");
    link.appendChild(arrow);
    body.appendChild(link);

    card.append(preview, body);
    return card;
  }

  function renderGallery(root, manifest) {
    const controls = createElement("div", "example-filters");
    controls.setAttribute("role", "group");
    controls.setAttribute("aria-label", "Filter examples by category");

    const filterPanel = createElement("div", "example-filter-panel");
    filterPanel.id = "example-filter-panel";
    filterPanel.hidden = true;

    const status = createElement("p", "example-filter-status");
    status.setAttribute("aria-live", "polite");

    const gallery = createElement("div", "learning-gallery");
    const cards = manifest.examples.map((example) => {
      const card = createCard(example);
      gallery.appendChild(card);
      return card;
    });

    const categoriesInUse = new Set(
      manifest.examples.flatMap((example) => example.categories),
    );
    const categories = manifest.categories.filter((category) =>
      categoriesInUse.has(category),
    );

    const allButton = createElement("button", "example-filter", "All");
    allButton.type = "button";
    allButton.dataset.category = "All";
    allButton.addEventListener("click", () => toggleCategory("All"));

    const moreButton = createElement("button", "example-filter", "More filters");
    moreButton.type = "button";
    moreButton.setAttribute("aria-controls", filterPanel.id);
    moreButton.setAttribute("aria-expanded", "false");
    moreButton.addEventListener("click", () => {
      filterPanel.hidden = !filterPanel.hidden;
      moreButton.setAttribute("aria-expanded", String(!filterPanel.hidden));
    });

    controls.append(allButton, moreButton);

    const activeCategories = new Set();

    function updateGallery() {
      let visible = 0;
      cards.forEach((card) => {
        const cardCategories = card.dataset.categories.split("|");
        const matches =
          activeCategories.size === 0 ||
          cardCategories.some((category) => activeCategories.has(category));
        card.hidden = !matches;
        if (matches) visible += 1;
      });
      root.querySelectorAll("button[data-category]").forEach((button) => {
        const selected =
          button.dataset.category === "All"
            ? activeCategories.size === 0
            : activeCategories.has(button.dataset.category);
        button.classList.toggle("example-filter--active", selected);
        button.setAttribute("aria-pressed", String(selected));
      });
      moreButton.textContent =
        activeCategories.size === 0
          ? "More filters"
          : `More filters (${activeCategories.size})`;
      const selection =
        activeCategories.size === 0
          ? "all categories"
          : Array.from(activeCategories).join(" + ");
      status.textContent = `${visible} ${visible === 1 ? "example" : "examples"} in ${selection}`;
    }

    function toggleCategory(category) {
      if (category === "All") {
        activeCategories.clear();
      } else if (activeCategories.has(category)) {
        activeCategories.delete(category);
      } else {
        activeCategories.add(category);
      }
      updateGallery();
    }

    categories.forEach((category) => {
      const button = createElement("button", "example-filter", category);
      button.type = "button";
      button.dataset.category = category;
      button.addEventListener("click", () => toggleCategory(category));
      filterPanel.appendChild(button);
    });

    root.replaceChildren(controls, filterPanel, status, gallery);
    updateGallery();
  }

  async function initializeGallery() {
    const root = document.querySelector("[data-example-gallery]");
    if (!root || root.dataset.initialized === "true") return;
    root.dataset.initialized = "true";

    try {
      const response = await fetch(root.dataset.manifest);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      renderGallery(root, await response.json());
    } catch (error) {
      root.innerHTML = "";
      const failure = createElement("div", "gallery-empty");
      const content = createElement("div");
      content.appendChild(createElement("h2", "", "Examples could not be loaded"));
      content.appendChild(
        createElement("p", "", "Reload the page or browse the examples from the navigation."),
      );
      failure.appendChild(content);
      root.appendChild(failure);
      console.error("Femora example gallery failed to load:", error);
    }
  }

  if (typeof document$ !== "undefined") {
    document$.subscribe(initializeGallery);
  } else if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initializeGallery);
  } else {
    initializeGallery();
  }
})();
