(() => {
  'use strict';
  const assets = new URL('.', document.currentScript.src);
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const preferenceKey = 'black-hand-background-paused';
  let savedPause = false;
  try { savedPause = localStorage.getItem(preferenceKey) === 'true'; } catch {}
  let paused = reduceMotion.matches || savedPause;
  let attempt = 0;
  const layer = document.createElement('div');
  layer.className = 'site-background';
  layer.setAttribute('aria-hidden', 'true');
  const video = document.createElement('video');
  video.muted = true;
  video.defaultMuted = true;
  video.loop = true;
  video.playsInline = true;
  video.disablePictureInPicture = true;
  video.preload = 'none';
  video.poster = new URL('black-hand-background.webp', assets).href;
  const toggle = document.createElement('button');
  toggle.className = 'background-toggle';
  toggle.type = 'button';
  function updateLabel() {
    toggle.textContent = paused ? 'Включить фон' : 'Пауза фона';
    toggle.setAttribute('aria-label', paused ? 'Включить анимацию фона' : 'Остановить анимацию фона');
    toggle.setAttribute('aria-pressed', String(paused));
  }
  function apply() {
    const current = ++attempt;
    if (paused) {
      video.pause();
    } else {
      if (!video.hasAttribute('src')) {
        video.src = new URL('black-hand-background.mp4', assets).href;
        layer.append(video);
      }
      video.play().catch(() => {
        if (attempt === current && !paused) { paused = true; updateLabel(); }
      });
    }
    updateLabel();
  }
  toggle.addEventListener('click', () => {
    paused = !paused;
    try { localStorage.setItem(preferenceKey, String(paused)); } catch {}
    apply();
  });
  reduceMotion.addEventListener('change', event => {
    if (event.matches) { paused = true; apply(); }
  });
  document.body.prepend(layer);
  document.body.append(toggle);
  apply();
})();
