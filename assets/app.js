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
// 闯关测试 + 福袋拼图（通用，数据驱动）
//   - 题目：HTML 里写 .task[data-task=choice|order|pledge]
//   - 拼图：<body data-puzzle="图" data-puzzle-name="名" data-puzzle-total="9">
//   - 规则：不在 .quiz 内的题 = 前置题；前置题全做完才解锁 .quiz.lockable
//   - 答对一题 → 碎片飞入福袋 → 点亮一块拼图；集齐撒花见全貌
//   没有 .task 的关，本模块直接退出，不影响别的课。
// ======================================================================
(function () {
  var tasks = [].slice.call(document.querySelectorAll('.task'));
  if (!tasks.length) return;

  var body = document.body;
  var puzzleSrc = body.getAttribute('data-puzzle');
  var puzzleName = body.getAttribute('data-puzzle-name') || '';
  var TOTAL = parseInt(body.getAttribute('data-puzzle-total'), 10) || tasks.length;
  var KEY = 'puzzle:' + (location.pathname.replace(/.*\//, '') || 'index');
  var secretSrc = body.getAttribute('data-puzzle-secret');
  var isChallenge = location.hash === '#challenge';   // 隐藏款挑战模式
  var CH_MS = 15000;
  var chActive = false, chTimer = null, chTimerEl = null;

  function el(tag, cls) { var e = document.createElement(tag); if (cls) e.className = cls; return e; }

  tasks.forEach(function (t, i) { t.dataset.idx = i; });
  var prereq = tasks.filter(function (t) { return !t.closest('.quiz'); });
  var gate = document.querySelector('.quiz.lockable, .lockable');

  // 存档
  var solved = {};
  try { solved = JSON.parse(localStorage.getItem(KEY)) || {}; } catch (e) { solved = {}; }
  function persist(i) { solved[i] = 1; try { localStorage.setItem(KEY, JSON.stringify(solved)); } catch (e) {} }

  var count = 0;                                  // 已答对题数
  var defaultLit = Math.max(0, TOTAL - tasks.length); // 题不足总块数时，前几块默认亮

  // ---------- 福袋 + 拼图 DOM ----------
  var bag, pop, grid, cells = [], bagCount, ppSub;
  if (puzzleSrc) buildBag();

  function buildBag() {
    bag = el('button', 'lucky-bag');
    bag.setAttribute('aria-label', '福袋 · 拼图进度');
    bag.innerHTML = '<span class="ic">🧧</span><span class="bag-count"></span>';
    bagCount = bag.querySelector('.bag-count');
    body.appendChild(bag);

    pop = el('div', 'puzzle-pop'); pop.hidden = true;
    pop.innerHTML =
      '<button class="close" aria-label="关闭">×</button>' +
      '<p class="ttl">福袋拼图 · <span class="nm">' + puzzleName + '</span></p>' +
      '<p class="pp-sub"></p><div class="puzzle-grid"></div>' +
      '<button class="pz-challenge" type="button">⚡ 隐藏款挑战 · 10 秒内全对</button>' +
      '<button class="pz-reset" type="button">↺ 重新答题</button>';
    body.appendChild(pop);
    grid = pop.querySelector('.puzzle-grid');
    ppSub = pop.querySelector('.pp-sub');

    for (var i = 0; i < TOTAL; i++) {
      var c = el('div', 'pcell');
      // 直接设 inline（相对页面解析路径）；不要用 CSS var(--img)，那会相对 style.css 目录解析而 404
      c.style.backgroundImage = 'url("' + puzzleSrc + '")';
      c.style.backgroundPosition = (i % 3) * 50 + '% ' + Math.floor(i / 3) * 50 + '%';
      var lk = el('div', 'lock'); lk.textContent = '?'; c.appendChild(lk);
      grid.appendChild(c); cells.push(c);
    }
    // 第 i 题固定对应第 i 块；没有题对应的尾部块默认显示
    for (var j = tasks.length; j < TOTAL; j++) cells[j].classList.add('lit');

    bag.addEventListener('click', function () { pop.hidden ? openPop() : (pop.hidden = true); });
    pop.querySelector('.close').addEventListener('click', function () { pop.hidden = true; });
    pop.querySelector('.pz-reset').addEventListener('click', function () {
      if (confirm('重新答题会清空已点亮的拼图，确定吗？')) {
        try { localStorage.removeItem(KEY); } catch (e) {}
        location.reload();
      }
    });
    pop.querySelector('.pz-challenge').addEventListener('click', function () {
      location.hash = 'challenge'; location.reload();   // 进入挑战（不清普通存档）
    });
    refreshBag();
  }
  function openPop() { pop.hidden = false; pop.classList.remove('in'); void pop.offsetWidth; pop.classList.add('in'); }
  function litCount() { return defaultLit + count; }
  function refreshBag() {
    if (!bag) return;
    bagCount.textContent = litCount() + '/' + TOTAL;
    if (ppSub) ppSub.textContent = (litCount() >= TOTAL ? '集齐啦！🎉' : '答对小题，点亮一块 · ' + litCount() + '/' + TOTAL);
  }

  // ---------- 锁定区 ----------
  function buildGate() {
    if (!gate || !prereq.length) return;
    var lock = el('div', 'zone-lock');
    lock.innerHTML = '<div class="box"><span class="lk">🔒</span>先完成上面的 ' +
      prereq.length + ' 个小测验<span class="sub">集齐前 ' + prereq.length + ' 块拼图，这里就解锁啦</span></div>';
    gate.appendChild(lock);
    gate.classList.add('locked');
  }
  function checkUnlock() {
    if (!gate || !gate.classList.contains('locked')) return;
    var done = prereq.every(function (t) { return t.classList.contains('solved'); });
    if (done) gate.classList.remove('locked');
  }
  buildGate();

  // ---------- 反馈动画 ----------
  function feedback(task, ok, msg) {
    var f = task.querySelector('.feedback');
    if (!f) { f = el('p', 'feedback'); task.appendChild(f); }
    f.className = 'feedback ' + (ok ? 'ok' : 'no');
    f.textContent = msg;
  }
  function bingoFloat(task) {
    var b = el('div', 'bingo-float'); b.textContent = 'Bingo! 🎉';
    task.appendChild(b); setTimeout(function () { b.remove(); }, 1000);
  }
  // 答对后，把题目里标着「?」的积木翻成正确答案
  function revealAsk(task) {
    var ask = task.querySelector('.brick.ask'); if (!ask) return;
    var correct = task.querySelector('.opt[data-correct]');
    var role = ask.querySelector('.role');
    if (role && correct) role.textContent = correct.textContent.trim();
    ask.classList.remove('ask');
  }
  function lightCell(idx) { if (cells[idx]) cells[idx].classList.add('lit'); }
  function flyToBag(task, idx) {
    if (!bag) { lightCell(idx); count++; refreshBag(); checkDone(); return; }
    var r = task.getBoundingClientRect(), br = bag.getBoundingClientRect();
    var bit = el('div', 'fly-bit'); bit.textContent = '✨';
    bit.style.left = (r.left + r.width / 2) + 'px';
    bit.style.top = (r.top + 24) + 'px';
    body.appendChild(bit);
    void bit.offsetWidth;
    bit.style.transform = 'translate(' + (br.left + br.width / 2 - (r.left + r.width / 2)) +
      'px,' + (br.top + 12 - (r.top + 24)) + 'px) scale(.4)';
    bit.style.opacity = '0';
    setTimeout(function () {
      bit.remove();
      bag.classList.remove('shake'); void bag.offsetWidth; bag.classList.add('shake');
      lightCell(idx); count++; refreshBag(); checkDone();
    }, 760);
  }
  function confetti() {
    var box = el('div', 'confetti'); var bits = ['🎉', '✨', '⭐', '🎊', '💛'];
    for (var i = 0; i < 28; i++) {
      var s = document.createElement('i');
      s.textContent = bits[i % bits.length];
      s.style.left = Math.random() * 100 + '%';
      s.style.animationDuration = (1.6 + Math.random() * 1.8) + 's';
      s.style.animationDelay = (Math.random() * .5) + 's';
      box.appendChild(s);
    }
    body.appendChild(box); setTimeout(function () { box.remove(); }, 3600);
  }
  function checkDone() {
    if (count < tasks.length) return;
    if (isChallenge && chActive) { challengeWin(); return; }
    if (pop) { pop.classList.add('done'); pop.classList.add('can-challenge'); openPop(); }
    if (bag) bag.classList.add('full');
    confetti();
  }

  // ---------- 标记答对 ----------
  function win(task, restore) {
    if (task.classList.contains('solved')) return;
    task.classList.add('solved');
    var idx = +task.dataset.idx;                  // 第 i 题 → 固定第 i 块
    if (!isChallenge) persist(idx);               // 挑战模式不写存档，避免污染普通进度
    if (restore) {                                // 刷新恢复：直接点亮，不放动画
      lightCell(idx); count++; refreshBag();
    } else if (isChallenge) {                     // 挑战模式：即时计分，避免与倒计时竞态
      feedback(task, true, 'Bingo！🎉'); bingoFloat(task);
      lightCell(idx); count++; refreshBag(); checkDone();
    } else {
      feedback(task, true, 'Bingo！答对啦 🎉');
      bingoFloat(task);
      flyToBag(task, idx);                        // 内部会 count++ / 点亮 / checkDone
    }
    checkUnlock();
  }

  // ---------- 各题型 ----------
  tasks.forEach(function (task) {
    var type = task.dataset.task;
    var done = !isChallenge && solved[task.dataset.idx];   // 挑战模式：全部从未答开始

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
      if (done) { opts.forEach(function (x) { if (x.hasAttribute('data-correct')) x.classList.add('correct'); }); revealAsk(task); win(task, true); }

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
      if (done) {
        toks.sort(function (a, b) { return a.dataset.pos - b.dataset.pos; })
          .forEach(function (t) { slots.appendChild(t); });
        win(task, true);
      }

    } else if (type === 'pledge') {
      var btn = task.querySelector('.pledge-btn');
      btn.addEventListener('click', function () { win(task); });
      if (done) win(task, true);
    }
  });

  // 恢复存档后：确保解锁状态正确；若已全部答对，静默置为完成态（不撒花）
  checkUnlock();
  if (count >= tasks.length && pop) { pop.classList.add('done'); pop.classList.add('can-challenge'); if (bag) bag.classList.add('full'); }

  // ---------- 隐藏款挑战：10 秒内全对 ----------
  function startChallenge() {
    chActive = true;
    if (bag) { bag.classList.add('super'); bag.classList.remove('full'); }
    if (pop) { pop.classList.remove('done'); pop.hidden = true; }
    // 只留题目：把所有 .task 移进挑战舞台（节点移动，事件监听器保留），讲解全部隐藏
    var wrap = document.querySelector('.wrap') || body;
    var stage = el('div', 'challenge-stage');
    var tip = el('p', 'cs-tip'); tip.textContent = '⚡ 限时挑战 · 答对全部 ' + tasks.length + ' 题！';
    stage.appendChild(tip);
    tasks.forEach(function (t) { stage.appendChild(t); });
    wrap.appendChild(stage);
    body.classList.add('challenge-mode');
    window.scrollTo(0, 0);                              // 开始后自动滚到顶
    chTimerEl = el('div', 'timer');
    chTimerEl.innerHTML = '⏱ <span class="t">15.0</span>s';
    body.appendChild(chTimerEl);
    var end = Date.now() + CH_MS;
    chTimer = setInterval(function () {
      var left = Math.max(0, end - Date.now()), sec = left / 1000;
      chTimerEl.querySelector('.t').textContent = sec.toFixed(1);
      if (sec <= 3) chTimerEl.classList.add('hurry');
      if (left <= 0) challengeFail();
    }, 100);
  }
  function challengeWin() {
    if (!chActive) return;
    chActive = false; clearInterval(chTimer);
    if (chTimerEl) chTimerEl.remove();
    cells.forEach(function (c) {
      if (secretSrc) c.style.backgroundImage = 'url("' + secretSrc + '")';
      c.classList.add('secret');
    });
    if (grid) grid.classList.add('secret');
    if (pop) {
      openPop();                                   // 不加 .done（那是绿色普通通关态），用金色 secret 态
      pop.querySelector('.ttl').innerHTML = '🏆 隐藏款 · <span class="nm">' + puzzleName + '</span>';
      if (ppSub) ppSub.textContent = '隐藏款 GET！太快啦 🎉';
    }
    if (bag) bag.classList.add('super');
    try { localStorage.setItem(KEY + ':secret', '1'); } catch (e) {}
    confetti(); setTimeout(confetti, 400);
    if (history.replaceState) history.replaceState(null, '', location.pathname);
  }
  function challengeFail() {
    if (!chActive) return;
    chActive = false; clearInterval(chTimer);
    if (chTimerEl) chTimerEl.remove();
    var m = el('div', 'challenge-end');
    m.innerHTML = '<div class="box"><h3>⏰ 时间到！</h3><p>差一点点~ 再来一次?</p>' +
      '<div class="btns"><button class="again primary" type="button">再挑战一次</button>' +
      '<button class="quit" type="button">先算了</button></div></div>';
    body.appendChild(m);
    m.querySelector('.again').addEventListener('click', function () { location.hash = 'challenge'; location.reload(); });
    m.querySelector('.quit').addEventListener('click', function () {
      if (history.replaceState) history.replaceState(null, '', location.pathname);
      location.reload();
    });
  }
  if (isChallenge) startChallenge();
})();
