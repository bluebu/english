// 入场动画：元素进入视口时淡入上滑
(function () {
  var items = document.querySelectorAll('.reveal');
  if (!('IntersectionObserver' in window) || !items.length) {
    items.forEach(function (el) { el.classList.add('in'); });
    return;
  }
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (e.isIntersecting) {
        e.target.classList.add('in');
        io.unobserve(e.target);
      }
    });
  }, { threshold: 0.12, rootMargin: '0px 0px -8% 0px' });
  items.forEach(function (el) { io.observe(el); });
})();

// 点击色块 → 用中文念出它的语法成分（主语 / 谓语 / 宾语 / 表语）
// 参照 vocab 项目，使用浏览器自带的 Web Speech API（speechSynthesis）
(function () {
  if (typeof speechSynthesis === 'undefined') return;

  // 色块的角色 class → 默认朗读的语法成分；个别用 data-say 覆盖（如表语、句子）
  var ROLE_TERM = { who: '主语', do: '谓语', what: '宾语', be: '系动词' };

  var voice = null;
  function pickVoice() {
    var all = speechSynthesis.getVoices();
    if (!all.length) return null;
    var zh = all.filter(function (v) { return /^zh/i.test(v.lang || ''); });
    return (
      zh.filter(function (v) { return /Tingting|Ting-Ting|Meijia|Mei-Jia|Sinji|Yu-?shu|Google\s*普通话|中文/i.test(v.name); })[0] ||
      zh[0] || null
    );
  }
  function ensureVoice() { if (!voice) voice = pickVoice(); return voice; }
  // 音色异步加载，加载完重选
  speechSynthesis.onvoiceschanged = function () { voice = null; ensureVoice(); };
  ensureVoice();

  function termOf(el) {
    if (el.dataset && el.dataset.say) return el.dataset.say;
    for (var k in ROLE_TERM) { if (el.classList.contains(k)) return ROLE_TERM[k]; }
    return null;
  }

  function say(el, term) {
    speechSynthesis.cancel();
    var u = new SpeechSynthesisUtterance(term);
    u.lang = 'zh-CN';
    u.rate = 0.85;
    u.pitch = 1.05;
    var v = ensureVoice();
    if (v) u.voice = v;
    el.classList.add('speaking');
    var clear = function () { el.classList.remove('speaking'); };
    u.onend = clear; u.onerror = clear;
    setTimeout(clear, 1600);
    speechSynthesis.speak(u);
  }

  var blocks = document.querySelectorAll('.brick, .mini .b');
  blocks.forEach(function (el) {
    var term = termOf(el);
    if (!term) return;
    el.classList.add('say-able');
    el.setAttribute('role', 'button');
    el.setAttribute('tabindex', '0');
    el.setAttribute('aria-label', '朗读语法成分：' + term);
    el.addEventListener('click', function () { say(el, term); });
    el.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' || e.key === ' ' || e.key === 'Spacebar') {
        e.preventDefault();
        say(el, term);
      }
    });
  });
})();
