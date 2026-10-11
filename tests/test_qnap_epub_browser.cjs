// No npm install and no browser automation cost: exercise QNAP's actual JS
// in a small Node VM with an in-memory DOM stand-in.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

class FakeElement {
  constructor(tag = 'div') {
    this.tag = tag;
    this.handlers = {};
    this.children = [];
    this.disabled = false;
    this.hidden = false;
    this.textContent = '';
    this.style = {};
    this.removed = false;
  }
  setAttribute() {}
  addEventListener(type, callback) { this.handlers[type] = callback; }
  click() {
    if (this.handlers.click) return this.handlers.click({ target: this });
    if (this.tag === 'a') this.wasClicked = true;
  }
  focus() {}
  remove() { this.removed = true; }
  prepend(child) { this.children.unshift(child); }
  appendChild(child) { this.children.push(child); return child; }
  set innerHTML(value) {
    this.html = value;
    this.elements = new Map();
    for (const name of ['panel', 'message', 'share', 'save', 'dismiss']) {
      this.elements.set('.qnap-epub-' + name, new FakeElement(name));
    }
  }
  querySelector(query) { return this.elements?.get(query) || null; }
}

async function main() {
  const source = fs.readFileSync('tools/qnap_epub_download.js', 'utf8');
  let listener = null, shareCalls = 0, fetchCalls = 0;
  const created = [];
  const body = new FakeElement('body');
  const document = {
    body,
    createElement(name) { const el = new FakeElement(name); created.push(el); return el; },
    addEventListener(type, callback) { if (type === 'click') listener = callback; },
    removeEventListener() {}
  };
  const location = { href: 'http://192.168.68.57:8888/', origin: 'http://192.168.68.57:8888' };
  const link = {
    href: location.origin + '/novels/0/download',
    closest(selector) {
      return selector === 'tr' ? { querySelector: () => ({ textContent: '日本語タイトル' }) } : null;
    }
  };
  const target = new FakeElement('span');
  target.closest = selector => selector === 'a.row-action-btn.btn-download[data-qnap-epub]' ? link : null;
  const navigator = {
    canShare: () => true,
    share: async () => { shareCalls++; }
  };
  const ctx = {
    document, location, navigator, URL, Blob, File, Element: FakeElement,
    Uint8Array, AbortController, setTimeout: (callback, delay) => { const timer = setTimeout(callback, delay); timer.unref(); return timer; }, clearTimeout, console,
    fetch: async () => {
      fetchCalls++;
      return {
        ok: true, headers: { get(name) { return name === 'content-disposition' ? 'attachment; filename="test.epub"' : '32'; } },
        blob: async () => new Blob([new Uint8Array([80,75,3,4,0,0,0,0])])
      };
    }
  };
  const fakeBlobUrls = [];
  ctx.URL = class extends URL {
    static createObjectURL() { const id='blob:test/' + (fakeBlobUrls.length + 1); fakeBlobUrls.push(id); return id; }
    static revokeObjectURL() {}
  };
  vm.runInNewContext(source, ctx, { filename: 'qnap_epub_download.js' });
  assert.equal(typeof listener, 'function');

  let stopped = false, prevented = false;
  listener({ target, preventDefault() { prevented=true; }, stopImmediatePropagation() { stopped=true; } });
  assert(prevented && stopped, 'direct anchor navigation must be blocked');
  assert.equal(location.href, 'http://192.168.68.57:8888/');
  await new Promise(resolve => setImmediate(resolve));
  const modal = created.find(el => el.html?.includes('aria-label="EPUBを保存"'));
  assert(modal, 'modal must be created');
  const share = modal.querySelector('.qnap-epub-share');
  const save = modal.querySelector('.qnap-epub-save');
  assert.equal(share.disabled, false);
  assert.equal(save.disabled, false);
  await share.click();
  assert.equal(shareCalls, 1, 'explicit second tap must call navigator.share');
  save.click();
  const anchor = created.find(el => el.tag === 'a' && el.wasClicked);
  assert(anchor);
  assert.equal(anchor.target, '_blank', 'native preview must not replace novel list');
  assert.match(anchor.href, /^blob:test\//);
  assert.equal(anchor.download, 'test.epub');
  assert.equal(location.href, 'http://192.168.68.57:8888/');
  modal.querySelector('.qnap-epub-dismiss').click();
  assert(modal.removed);

  // No share API on an insecure HTTP LAN context: modal is still usable and
  // download requires its own explicit tap, never automatic navigation.
  navigator.canShare = undefined;
  navigator.share = undefined;
  ctx.fetch = async () => {
    fetchCalls++;
    return { ok: true, headers: { get: () => null },
      blob: async () => new Blob([new Uint8Array([80,75,3,4])]) };
  };
  listener({ target, preventDefault() {}, stopImmediatePropagation() {} });
  await new Promise(resolve => setImmediate(resolve));
  const fallback = created.filter(el => el.html?.includes('aria-label="EPUBを保存"')).at(-1);
  assert(fallback.querySelector('.qnap-epub-share').hidden);
  assert.equal(fallback.querySelector('.qnap-epub-save').disabled, false);
  fallback.querySelector('.qnap-epub-dismiss').click();

  ctx.fetch = async () => ({ ok: false, status: 404, headers: {get:()=>null} });
  listener({ target, preventDefault() {}, stopImmediatePropagation() {} });
  await new Promise(resolve => setImmediate(resolve));
  const errorModal = created.filter(el => el.html?.includes('aria-label="EPUBを保存"')).at(-1);
  assert.match(errorModal.querySelector('.qnap-epub-message').textContent, /HTTP 404/);
  assert(errorModal.querySelector('.qnap-epub-save').disabled);
  errorModal.querySelector('.qnap-epub-dismiss').click();

  console.log('QNAP EPUB modal: share, save, HTTP-LAN fallback, no-navigation, 404 passed');
}
main().catch(err => { console.error(err); process.exitCode = 1; });
