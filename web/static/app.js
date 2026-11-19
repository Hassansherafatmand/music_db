// A little JavaScript to make the pages nicer. The website also works without it.

// Messages ("Added to your favorites") fade away after a few seconds.
document.querySelectorAll(".toast").forEach((toast) => {
  const hide = () => {
    toast.classList.add("leaving");
    setTimeout(() => toast.remove(), 300);
  };
  toast.querySelector("button")?.addEventListener("click", hide);
  setTimeout(hide, 4500);
});

// Open menus (like "Add to playlist") close when you click somewhere else.
document.addEventListener("click", (event) => {
  document.querySelectorAll("details.pop[open], details.usermenu[open]").forEach((menu) => {
    if (!menu.contains(event.target)) menu.removeAttribute("open");
  });
});

// The Escape key closes open menus too.
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    document.querySelectorAll("details.pop[open], details.usermenu[open]")
      .forEach((menu) => menu.removeAttribute("open"));
  }
});
