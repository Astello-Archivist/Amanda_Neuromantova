/* Static pages keep their content usable with JavaScript disabled. */
(() => {
  'use strict';

  const normalize = value => String(value || '').toLocaleLowerCase('ru').replace(/ё/g, 'е').replace(/\s+/g, ' ').trim();
  const list = document.getElementById('story-list');
  if (list) {
    const entries = Array.from(list.querySelectorAll('.story-item'));
    const search = document.getElementById('story-search');
    const kind = document.getElementById('story-kind');
    const sort = document.getElementById('story-sort');
    const count = document.getElementById('story-count');
    const empty = document.getElementById('story-empty');
    const reset = document.getElementById('story-reset');
    const collator = new Intl.Collator('ru', { sensitivity: 'base', numeric: true });
    const indexed = entries.map((item, index) => ({
      item,
      title: item.dataset.title || item.querySelector('h3')?.textContent || '',
      search: normalize(item.dataset.search || item.textContent),
      kind: item.dataset.kind || 'story',
      order: Number(item.dataset.order) || index + 1,
    }));
    const update = () => {
      const terms = normalize(search?.value).split(' ').filter(Boolean);
      const selected = kind?.value || 'all';
      let visible = 0;
      indexed.forEach(entry => {
        const matches = (selected === 'all' || entry.kind === selected) && terms.every(term => entry.search.includes(term));
        entry.item.hidden = !matches;
        if (matches) visible += 1;
      });
      const ordered = [...indexed].sort(sort?.value === 'archive'
        ? (a, b) => a.order - b.order
        : (a, b) => collator.compare(a.title, b.title));
      ordered.forEach(entry => list.appendChild(entry.item));
      if (count) count.textContent = visible === entries.length ? `Всего: ${entries.length}` : `Найдено: ${visible} из ${entries.length}`;
      if (empty) empty.hidden = visible > 0;
      if (reset) reset.hidden = !terms.length && selected === 'all';
    };
    search?.addEventListener('input', update);
    kind?.addEventListener('change', update);
    sort?.addEventListener('change', update);
    reset?.addEventListener('click', () => {
      if (search) search.value = '';
      if (kind) kind.value = 'all';
      update();
      search?.focus();
    });
    update();
  }

  const viewer = document.getElementById('image-viewer');
  const fullImage = document.getElementById('image-full');
  const closeImage = document.getElementById('image-close');
  const originalImage = document.getElementById('image-original');
  const caption = document.getElementById('image-caption');
  let returnFocus = null;
  if (viewer && fullImage && typeof viewer.showModal === 'function') {
    const close = () => {
      if (viewer.open) viewer.close();
    };
    document.addEventListener('click', event => {
      const trigger = event.target.closest('button.page-zoom');
      if (!trigger) return;
      const thumbnail = trigger.querySelector('img');
      const url = trigger.dataset.image || thumbnail?.currentSrc || thumbnail?.src;
      if (!url) return;
      returnFocus = trigger;
      fullImage.src = url;
      fullImage.alt = thumbnail?.alt || 'Иллюстрация сюжета';
      if (originalImage) originalImage.href = url;
      if (caption) caption.textContent = trigger.closest('figure')?.querySelector('figcaption')?.textContent || fullImage.alt;
      if (!viewer.open) viewer.showModal();
      viewer.scrollTop = 0;
      viewer.scrollLeft = 0;
      closeImage?.focus({ preventScroll: true });
    });
    closeImage?.addEventListener('click', close);
    viewer.addEventListener('click', event => {
      if (event.target === viewer) close();
    });
    viewer.addEventListener('close', () => {
      fullImage.removeAttribute('src');
      returnFocus?.focus({ preventScroll: true });
      returnFocus = null;
    });
  } else {
    // Older browsers retain access to the source image in a normal tab.
    document.querySelectorAll('button.page-zoom').forEach(button => button.addEventListener('click', () => {
      const url = button.dataset.image || button.querySelector('img')?.src;
      if (url) window.open(url, '_blank', 'noopener');
    }));
  }

  const wideButton = document.getElementById('reader-wide');
  if (wideButton) {
    const storageKey = 'black-hand-reader-expanded';
    let expanded = false;
    try { expanded = localStorage.getItem(storageKey) === 'true'; } catch { /* Storage is optional, including local-file previews. */ }
    const applyWidth = () => {
      document.body.classList.toggle('reader-expanded', expanded);
      wideButton.setAttribute('aria-pressed', String(expanded));
      wideButton.textContent = expanded ? 'Обычная ширина' : 'Развернуть чтение';
    };
    wideButton.addEventListener('click', () => {
      expanded = !expanded;
      applyWidth();
      try { localStorage.setItem(storageKey, String(expanded)); } catch { /* No action required. */ }
      window.dispatchEvent(new Event('resize'));
    });
    applyWidth();
  }

  const content = document.getElementById('reading-content');
  const progress = document.getElementById('reading-progress');
  if (content && progress) {
    let scheduled = false;
    const updateProgress = () => {
      const rect = content.getBoundingClientRect();
      const viewport = window.innerHeight || document.documentElement.clientHeight;
      const distance = Math.max(1, rect.height - viewport);
      const value = Math.max(0, Math.min(1, -rect.top / distance));
      if (progress.tagName === 'PROGRESS') {
        progress.max = 100;
        progress.value = value * 100;
      } else {
        progress.style.width = `${value * 100}%`;
      }
      scheduled = false;
    };
    const schedule = () => {
      if (!scheduled) { scheduled = true; requestAnimationFrame(updateProgress); }
    };
    window.addEventListener('scroll', schedule, { passive: true });
    window.addEventListener('resize', schedule);
    window.addEventListener('load', schedule);
    if ('ResizeObserver' in window) new ResizeObserver(schedule).observe(content);
    schedule();
  }

  const toc = document.querySelector('.reader-toc');
  if (toc && 'IntersectionObserver' in window) {
    const links = [...toc.querySelectorAll('a[href^="#"]')];
    const sections = links.map(link => {
      let id;
      try { id = decodeURIComponent(link.hash.slice(1)); } catch { id = link.hash.slice(1); }
      return document.getElementById(id);
    }).filter(Boolean);
    const active = new Set();
    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) active.add(entry.target);
        else active.delete(entry.target);
      });
      const current = sections.find(section => active.has(section));
      if (!current) return;
      links.forEach(link => {
        let id;
        try { id = decodeURIComponent(link.hash.slice(1)); } catch { id = link.hash.slice(1); }
        if (id === current.id) link.setAttribute('aria-current', 'location');
        else link.removeAttribute('aria-current');
      });
    }, { rootMargin: '-8% 0px -50% 0px', threshold: 0 });
    sections.forEach(section => observer.observe(section));
  }
})();
