/*
 * QnapNarou EPUB save/share overlay.
 * This is appended at native build time to the pinned upstream render.js.
 * No external UI bundle, server route, polling, logging or library writes.
 * Deliberately NEVER navigate the original window to an EPUB URL.
 */
const QNAP_EPUB_MAX_BYTES = 150 * 1024 * 1024;
let qnapEpubActive = null;

function qnapEpubName(header, fallback) {
  // Content-Disposition may contain an RFC5987-encoded filename* or a
  // quoted filename. Only use a safe basename; never interpret it as markup.
  const star = header?.match(/filename\*\s*=\s*UTF-8''([^;\s]+)/i);
  let name = '';
  if (star) {
    try { name = decodeURIComponent(star[1]); } catch (_) { /* fallback */ }
  }
  if (!name) {
    const quoted = header?.match(/filename\s*=\s*"([^"]*)"/i);
    const bare = header?.match(/filename\s*=\s*([^;\s]+)/i);
    name = quoted?.[1] || bare?.[1] || fallback;
  }
  name = String(name || 'ebook.epub').split(/[\\/]/).pop()
    .replace(/[\u0000-\u001f\u007f<>:"|?*]/g, '_').trim().slice(0, 180);
  if (!name) name = 'ebook.epub';
  if (!/\.epub$/i.test(name)) name += '.epub';
  return name;
}

function qnapEpubModal() {
  const shade = document.createElement('div');
  shade.className = 'qnap-epub-overlay';
  shade.setAttribute('role', 'presentation');
  const style = document.createElement('style');
  style.textContent = [
    '.qnap-epub-overlay{position:fixed;inset:0;z-index:2147483646;',
    'background:rgba(0,0,0,.65);display:flex;align-items:center;',
    'justify-content:center;padding:calc(18px + env(safe-area-inset-top,0px))',
    ' 16px calc(18px + env(safe-area-inset-bottom,0px));box-sizing:border-box;}',
    '.qnap-epub-panel{box-sizing:border-box;width:min(100%,440px);',
    'max-height:85vh;overflow:auto;border-radius:15px;padding:22px;',
    'background:#1d2b3a;color:#f6f8fc;box-shadow:0 14px 40px #0009;',
    'font:16px/1.55 system-ui,-apple-system,sans-serif;}',
    '.qnap-epub-panel h2{font-size:19px;margin:0 0 12px;}',
    '.qnap-epub-panel p{margin:8px 0 18px;overflow-wrap:anywhere;}',
    '.qnap-epub-actions{display:flex;gap:9px;flex-wrap:wrap;}',
    '.qnap-epub-actions button{font:inherit;touch-action:manipulation;',
    'border:0;border-radius:9px;min-height:45px;padding:9px 14px;',
    'background:#4e9bed;color:#071827;cursor:pointer;}',
    '.qnap-epub-actions button[disabled]{opacity:.4;cursor:default;}',
    '.qnap-epub-actions button.qnap-epub-dismiss{background:#35495b;',
    'color:#fff;}'
  ].join('');
  // This HTML contains no upstream/user/novel data.
  shade.innerHTML = '<section class="qnap-epub-panel" role="dialog" aria-modal="true" ' +
    'aria-label="EPUBを保存"><h2>EPUBを保存</h2>' +
    '<p class="qnap-epub-message" role="status" aria-live="polite">準備中…</p>' +
    '<div class="qnap-epub-actions">' +
    '<button type="button" class="qnap-epub-share" disabled>共有・保存</button>' +
    '<button type="button" class="qnap-epub-save" disabled>ダウンロード</button>' +
    '<button type="button" class="qnap-epub-dismiss">閉じる</button></div></section>';
  shade.prepend(style);
  document.body.appendChild(shade);
  const panel = shade.querySelector('.qnap-epub-panel');
  const message = shade.querySelector('.qnap-epub-message');
  const share = shade.querySelector('.qnap-epub-share');
  const save = shade.querySelector('.qnap-epub-save');
  const close = shade.querySelector('.qnap-epub-dismiss');
  close.focus();

  let controller = new AbortController();
  let file = null;
  let objectUrl = null;
  let timer = null;
  const cleanup = () => {
    controller.abort();
    if (timer) clearTimeout(timer);
    if (objectUrl) {
      // Allow iOS time to hand off the blob to its download manager.
      const staleUrl = objectUrl;
      setTimeout(() => URL.revokeObjectURL(staleUrl), 60000);
    }
    shade.remove();
    if (qnapEpubActive?.shade === shade) qnapEpubActive = null;
    document.removeEventListener('keydown', handleEscape, true);
  };
  const handleEscape = event => {
    if (event.key === 'Escape') { event.preventDefault(); cleanup(); }
  };
  document.addEventListener('keydown', handleEscape, true);
  close.addEventListener('click', cleanup);
  shade.addEventListener('click', event => {
    if (event.target === shade) cleanup();
  });
  share.addEventListener('click', async () => {
    if (!file || !navigator.share) return;
    try {
      // This explicit second tap preserves transient iOS user activation.
      await navigator.share({ files: [file], title: file.name });
      message.textContent = '共有・保存操作を完了しました。';
    } catch (error) {
      if (error?.name !== 'AbortError') {
        message.textContent = '共有できませんでした。ダウンロードをお試しください。';
      }
    }
  });
  save.addEventListener('click', () => {
    if (!file) return;
    if (!objectUrl) objectUrl = URL.createObjectURL(file);
    const link = document.createElement('a');
    link.href = objectUrl;
    link.download = file.name;
    // On iOS implementations ignoring the download attribute, this prevents
    // replacing the original novel-list page with the native EPUB preview.
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    document.body.appendChild(link);
    link.click();
    link.remove();
    message.textContent = '保存を開始しました。元の小説一覧はこの画面に残ります。';
  });
  return {
    shade, controller, message, share, save, cleanup,
    setTimer(value) { timer = value; },
    setFile(value) {
      file = value;
      let sharable = false;
      try {
        sharable = typeof navigator.share === 'function'
          && typeof navigator.canShare === 'function'
          && navigator.canShare({ files: [file] });
      } catch (_) { /* unsupported share; show download instead */ }
      share.disabled = !sharable;
      if (!sharable) share.hidden = true;
      save.disabled = false;
      message.textContent = file.name + ' (' +
        (file.size / 1024 / 1024).toFixed(1) + ' MB) を準備しました。' +
        (sharable ? '「共有・保存」でブックやファイルに渡せます。' :
          '「ダウンロード」を押して保存してください。');
    }
  };
}

async function qnapEpubFetch(link) {
  if (qnapEpubActive) return;
  const modal = qnapEpubModal();
  qnapEpubActive = modal;
  const url = new URL(link.href, location.href);
  if (url.origin !== location.origin || !/^\/novels\/[^/]+\/download\/?$/.test(url.pathname)) {
    modal.message.textContent = 'ダウンロードURLを確認できませんでした。';
    return;
  }
  modal.setTimer(setTimeout(() => modal.controller.abort(), 120000));
  try {
    const response = await fetch(url.href, {
      credentials: 'same-origin', redirect: 'error', cache: 'no-store',
      signal: modal.controller.signal
    });
    if (!response.ok) throw new Error('HTTP ' + response.status);
    const declared = Number(response.headers.get('content-length') || 0);
    if (declared > QNAP_EPUB_MAX_BYTES) throw new Error('ファイルが大きすぎます');
    const blob = await response.blob();
    if (modal.controller.signal.aborted || qnapEpubActive !== modal) return;
    if (!blob.size || blob.size > QNAP_EPUB_MAX_BYTES) throw new Error('EPUBのサイズを確認できません');
    // ZIP local file header. Guard against HTML/login/error text served as .epub.
    const first = new Uint8Array(await blob.slice(0, 4).arrayBuffer());
    if (first.length !== 4 || first[0] !== 80 || first[1] !== 75 ||
        first[2] !== 3 || first[3] !== 4) throw new Error('EPUB形式ではありません');
    const fallback = (link.closest('tr')?.querySelector('.col-title')?.textContent
      || 'ebook').trim() + '.epub';
    const filename = qnapEpubName(response.headers.get('content-disposition'), fallback);
    modal.setFile(new File([blob], filename, { type: 'application/epub+zip' }));
  } catch (error) {
    if (qnapEpubActive !== modal) return;
    modal.message.textContent = modal.controller.signal.aborted
      ? 'タイムアウトしました。閉じて再試行してください。'
      : '取得できませんでした: ' + (error?.message || String(error));
  }
}

// Capture before upstream row click handlers. No document navigation, ever.
document.addEventListener('click', event => {
  const element = event.target instanceof Element ? event.target : event.target?.parentElement;
  const link = element?.closest('a.row-action-btn.btn-download[data-qnap-epub]');
  if (!link) return;
  event.preventDefault();
  event.stopImmediatePropagation();
  void qnapEpubFetch(link);
}, true);
