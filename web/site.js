(() => {
  const toggle = document.querySelector(".nav-toggle");
  const nav = document.querySelector(".nav");

  if (toggle && nav) {
    toggle.addEventListener("click", () => {
      const open = nav.classList.toggle("open");
      toggle.setAttribute("aria-expanded", String(open));
    });
  }

  const page = document.body.dataset.page;
  const current = page ? document.querySelector(`[data-nav="${page}"]`) : null;
  if (current) current.setAttribute("aria-current", "page");

  // Information-note dialogs.
  document.querySelectorAll("[data-dialog]").forEach((trigger) => {
    const id = trigger.getAttribute("data-dialog");
    const dialog = id ? document.getElementById(id) : null;
    if (!dialog || typeof dialog.showModal !== "function") return;

    trigger.addEventListener("click", () => {
      dialog.showModal();
    });

    const close = dialog.querySelector(".dialog-close");
    if (close) {
      close.addEventListener("click", () => dialog.close());
    }

    dialog.addEventListener("click", (event) => {
      if (event.target === dialog) {
        dialog.close();
      }
    });
  });

})();
