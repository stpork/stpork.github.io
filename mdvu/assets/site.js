'use strict';
document.documentElement.classList.add('js');
const ru = document.documentElement.lang === 'ru';
const platform = /Win/i.test(navigator.userAgentData?.platform || navigator.platform) ? 'win' : 'mac';
function selectPlatform(value) {
  document.querySelectorAll('[data-download-platform]').forEach(link => {
    link.classList.toggle('button-outline', link.dataset.downloadPlatform !== value);
  });
}
selectPlatform(platform);
document.querySelectorAll('[role="tablist"]').forEach(group => {
  const tabs = [...group.querySelectorAll('[role="tab"]')];
  function activateTab(tab) {
    tabs.forEach(item => {
      const active = item === tab;
      item.setAttribute('aria-selected', String(active));
      item.tabIndex = active ? 0 : -1;
      document.getElementById(item.getAttribute('aria-controls')).hidden = !active;
    });
    const image = document.getElementById(tab.getAttribute('aria-controls')).querySelector('img');
    if (image) { image.loading = 'eager'; image.fetchPriority = 'high'; }
    if (tab.dataset.platform) selectPlatform(tab.dataset.platform);
  }
  if (tabs.length) activateTab(tabs.find(tab => tab.dataset.platform === platform) || tabs[0]);
  tabs.forEach((tab, index) => {
    tab.addEventListener('click', () => activateTab(tab));
    tab.addEventListener('keydown', event => {
      let next;
      if (event.key === 'ArrowRight') next = (index + 1) % tabs.length;
      if (event.key === 'ArrowLeft') next = (index + tabs.length - 1) % tabs.length;
      if (event.key === 'Home') next = 0;
      if (event.key === 'End') next = tabs.length - 1;
      if (next !== undefined) {
        event.preventDefault();
        activateTab(tabs[next]);
        tabs[next].focus();
      }
    });
  });
});
const toast = document.querySelector('.toast');
let toastTimer;
function announce(message) {
  clearTimeout(toastTimer);
  toast.textContent = message;
  toast.classList.add('visible');
  toastTimer = setTimeout(() => toast.classList.remove('visible'), 3500);
}
document.querySelectorAll('[data-copy]').forEach(button => {
  button.addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(button.dataset.copy);
      announce(ru ? 'Команда скопирована' : 'Command copied');
    } catch {
      const range = document.createRange();
      range.selectNodeContents(button.parentElement.querySelector('code'));
      const selection = window.getSelection();
      selection.removeAllRanges();
      selection.addRange(range);
      announce(ru ? 'Команда выделена. Нажмите ⌘C / Ctrl+C.' : 'Command selected. Press ⌘C / Ctrl+C.');
    }
  });
});
const dialog = document.querySelector('.image-dialog');
if (dialog && typeof dialog.showModal === 'function') {
  const image = dialog.querySelector('img');
  const content = dialog.querySelector('.preview-content');
  let opener, previousOverflow;
  function fitContent() {
    if (!dialog.open || content.hidden) return;
    const copy = content.firstElementChild;
    const scale = dialog.clientWidth / copy.offsetWidth;
    content.style.height = copy.offsetHeight * scale + 'px';
    copy.style.transform = `scale(${scale})`;
  }
  window.addEventListener('resize', fitContent);
  document.querySelectorAll('[data-preview],[data-preview-content]').forEach(link => link.addEventListener('click', event => {
    if (event.button || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    const isContent = !!link.dataset.previewContent;
    const source = isContent ? document.getElementById(link.dataset.previewContent) : link.querySelector('img');
    const rect = source.getBoundingClientRect();
    const width = Number(source.getAttribute('width')) || rect.width || 1;
    const height = Number(source.getAttribute('height')) || rect.height || 1;
    image.hidden = isContent;
    content.hidden = !isContent;
    dialog.dataset.kind = isContent ? 'content' : 'image';
    if (isContent) {
      const copy = source.cloneNode(true);
      copy.removeAttribute('id');
      copy.style.width = width + 'px';
      copy.style.height = height + 'px';
      content.replaceChildren(copy);
    } else {
      image.width = width;
      image.height = height;
      image.alt = source.alt;
      image.src = link.href;
    }
    dialog.style.setProperty('--preview-ratio', width / height);
    opener = isContent ? link.querySelector('button') : link;
    dialog.setAttribute('aria-label', source.alt || opener.getAttribute('aria-label'));
    previousOverflow = document.body.style.overflow;
    dialog.showModal();
    fitContent();
    document.body.style.overflow = 'hidden';
  }));
  dialog.querySelector('.close-dialog').addEventListener('click', () => dialog.close());
  dialog.addEventListener('click', event => {
    if (event.target === dialog) {
      const box = dialog.getBoundingClientRect();
      if (event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom) dialog.close();
    }
  });
  dialog.addEventListener('close', () => {
    document.body.style.overflow = previousOverflow;
    image.removeAttribute('src');
    content.replaceChildren();
    opener?.focus({preventScroll:true});
  });
}
