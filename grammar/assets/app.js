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

  var blocks = document.querySelectorAll('.brick, .mini .b, .pron-pair');
  blocks.forEach(function (el) {
    if (el.closest && el.closest('.task')) return; // 题目里的示例积木只做展示，不朗读
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

// ======================================================================
// 练习题判定（通用，数据驱动）
//   题目：HTML 里写 .task[data-task=choice|order|pledge]
//   答对 → 高亮正确答案 + 一句反馈；答错 → 提示再试。纯练习，无进度 / 奖励。
//   没有 .task 的关，本模块直接退出，不影响别的课。
// ======================================================================
(function () {
  var tasks = [].slice.call(document.querySelectorAll('.task'));
  if (!tasks.length) return;

  function el(tag, cls) { var e = document.createElement(tag); if (cls) e.className = cls; return e; }

  function feedback(task, ok, msg) {
    var f = task.querySelector('.feedback');
    if (!f) { f = el('p', 'feedback'); task.appendChild(f); }
    f.className = 'feedback ' + (ok ? 'ok' : 'no');
    f.textContent = msg;
  }
  // 答对后，把题目里标着「?」的积木翻成正确答案
  function revealAsk(task) {
    var ask = task.querySelector('.brick.ask'); if (!ask) return;
    var correct = task.querySelector('.opt[data-correct]');
    var role = ask.querySelector('.role');
    if (role && correct) role.textContent = correct.textContent.trim();
    ask.classList.remove('ask');
  }
  function win(task) {
    if (task.classList.contains('solved')) return;
    task.classList.add('solved');
    feedback(task, true, 'Bingo！答对啦 🎉');
  }

  tasks.forEach(function (task) {
    var type = task.dataset.task;

    if (type === 'choice') {
      var opts = [].slice.call(task.querySelectorAll('.opt'));
      opts.forEach(function (o) {
        o.addEventListener('click', function () {
          if (task.classList.contains('solved')) return;
          if (o.hasAttribute('data-correct')) {
            opts.forEach(function (x) { if (x.hasAttribute('data-correct')) x.classList.add('correct'); });
            revealAsk(task);
            win(task);
          } else {
            o.classList.add('wrong');
            feedback(task, false, '再想想~ 💪');
            setTimeout(function () { o.classList.remove('wrong'); }, 600);
          }
        });
      });

    } else if (type === 'order') {
      var pool = task.querySelector('.order-pool');
      var slots = task.querySelector('.order-slots');
      var toks = [].slice.call(task.querySelectorAll('.tok'));
      var total = toks.length;
      function judge() {
        var inSlots = [].slice.call(slots.children);
        if (inSlots.length < total) return;
        var ok = inSlots.every(function (t, i) { return +t.dataset.pos === i; });
        if (ok) { win(task); }
        else {
          slots.classList.add('wrong');
          feedback(task, false, '就快好啦，再调调顺序~ 💪');
          setTimeout(function () {
            slots.classList.remove('wrong');
            toks.forEach(function (t) { pool.appendChild(t); });
          }, 700);
        }
      }
      task.addEventListener('click', function (e) {
        var t = e.target.closest('.tok');
        if (!t || task.classList.contains('solved')) return;
        (t.parentNode === pool ? slots : pool).appendChild(t);
        judge();
      });

    } else if (type === 'pledge') {
      var btn = task.querySelector('.pledge-btn');
      btn.addEventListener('click', function () { win(task); });
    }
  });
})();
