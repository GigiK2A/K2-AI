document.addEventListener('DOMContentLoaded', () => {
  const filterBtns = document.querySelectorAll('.filter-btn');
  const caseCards = document.querySelectorAll('.case-card');

  if (!filterBtns.length || !caseCards.length) return;

  filterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      // Update active state
      filterBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      const filter = btn.dataset.filter;

      caseCards.forEach(card => {
        const sector = card.dataset.sector || '';
        const show = filter === 'tutti' || sector === filter;
        card.hidden = !show;
      });
    });
  });
});
