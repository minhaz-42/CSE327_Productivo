document.addEventListener("DOMContentLoaded", () => {
  const categoryForm = document.getElementById("categoryForm");
  const categoryList = document.getElementById("categoryList");

  function getCategories() {
    return JSON.parse(localStorage.getItem("categories")) || [];
  }

  function saveCategories(categories) {
    localStorage.setItem("categories", JSON.stringify(categories));
  }

  function renderCategories() {
    const categories = getCategories();
    categoryList.innerHTML = "";

    if (categories.length === 0) {
      categoryList.innerHTML = `<p class="empty-message">No categories yet.</p>`;
      return;
    }

    categories.forEach((cat, index) => {
      const item = document.createElement("div");
      item.className = "task-item";
      item.innerHTML = `
        <div class="task-header">
          <h4 style="color:${cat.color}">${cat.name}</h4>
          <button class="action-btn delete" data-index="${index}">Delete</button>
        </div>
      `;
      categoryList.appendChild(item);
    });

    // Attach delete events
    document.querySelectorAll(".action-btn.delete").forEach(btn => {
      btn.addEventListener("click", function () {
        const idx = this.dataset.index;
        const cats = getCategories();
        cats.splice(idx, 1);
        saveCategories(cats);
        renderCategories();
      });
    });
  }

  categoryForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const name = document.getElementById("category-name").value.trim();
    const color = document.getElementById("category-color").value;

    if (!name) return;

    const categories = getCategories();
    categories.push({ name, color });
    saveCategories(categories);

    categoryForm.reset();
    renderCategories();
  });

  renderCategories();
});
