/* Jeolmi Office — app logic */
(function () {
  'use strict';

  const KEY = 'jeolmi-office.v1';
  const $ = (sel, root) => (root || document).querySelector(sel);
  const $$ = (sel, root) => Array.from((root || document).querySelectorAll(sel));

  const uid = () => 'x' + Math.random().toString(36).slice(2, 9) + Date.now().toString(36).slice(-3);
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

  /* ---------- 방 정의 ---------- */
  const ROOMS = {
    hq: {
      emoji: '🎯', name: '지휘실', meta: '비서실 · 절미 Lv.3', badge: '가동 중',
      summary: '아침 브리핑과 회사 메일, 배송·일정까지 절미가 직접 챙기는 본부 책상이에요.',
      parts: true,
      tasks: [
        { text: '회사 메일 새 소식 확인', done: false },
        { text: '오늘 일정·브리핑 정리', done: true },
        { text: '쿠팡·네이버 배송 상태 확인', done: false },
        { text: '이번 주 교육자료 발송 점검', done: false }
      ]
    },
    meet: {
      emoji: '🏛️', name: '대회의실', meta: '일정 · 회의 준비', badge: '가동 중',
      summary: '오늘 일정과 할 일을 모아 두는 방이에요. 여기서 체크하면 현황과 타임라인에도 바로 반영돼요.',
      parts: true,
      tasks: [
        { text: '사무실 근무 · 오늘 일정 확인', done: true },
        { text: '오후 회의 자료 초안 점검', done: false },
        { text: '내일 일정 미리 알림 설정', done: false }
      ]
    },
    work: {
      emoji: '💻', name: '작업실', meta: '웹앱 · 도구 만들기', badge: '가동 중',
      summary: '절미와 함께 만든 웹앱과 새 아이디어를 굴리는 방이에요. 스틱맨 계산기부터 마이스탁까지 모여 있어요.',
      parts: true,
      tasks: [
        { text: '스틱맨 계산기 링크 동작 확인', done: true },
        { text: '마이스탁 관심종목 시세 체크', done: false },
        { text: '새 도구 아이디어 하나 적어 두기', done: false }
      ]
    },
    event: {
      emoji: '🎁', name: '이벤트·주식', meta: '무료 응모 · 관심종목', badge: '가동 중',
      summary: '매일 오후 1시 무료 응모와 루닛·원익IPS 소식을 챙기는 자리예요. 응모 전엔 꼭 대표님 확인을 받아요.',
      parts: true,
      tasks: [
        { text: '오늘의 무료 응모 1건 찾아 두기', done: false },
        { text: '체험단 당첨 결과 확인', done: false },
        { text: '루닛·원익IPS 뉴스 체크', done: true }
      ]
    },
    lounge: {
      emoji: '☕', name: '라운지', meta: '휴게 공간 · 잠깐 숨 고르기', badge: '휴게 공간', soft: true,
      summary: '대표님이 잠깐 쉬어 가는 자리예요. 쉬는 동안 절미가 나머지를 조용히 챙겨 둘게요.',
      parts: false,
      tasks: [
        { text: '커피 한 잔 마시기', done: false },
        { text: '어깨·허리 스트레칭 3분', done: false }
      ]
    }
  };

  const DEFAULT_TOOLS = [
    { emoji: '🧮', name: '스틱맨 계산기', url: 'https://kimkyungse48-ui.github.io/stickman-calc/' },
    { emoji: '📈', name: '마이스탁', url: 'https://mystock-kimgyeongse.netlify.app' },
    { emoji: '🎬', name: '세이브클립', url: 'https://saveclip-kimgyeongse.netlify.app' },
    { emoji: '🔗', name: '링크네스트', url: 'https://grand-khapse-7e2189.netlify.app' }
  ];

  /* ---------- 배경(주간/야간) ---------- */
  const BG = {
    day: {
      jpg: 'assets/office-bg.jpg',
      png: 'assets/office-bg.png',
      alt: '따뜻한 우드 톤의 미니어처 오피스, 지휘실·대회의실·작업실·라운지가 한눈에 보인다'
    },
    night: {
      jpg: 'assets/office-bg-night.jpg',
      png: 'assets/office-bg-night.png',
      alt: '밤이 된 미니어처 오피스, 창밖은 어두운 밤이고 스탠드와 벽등 불빛만 따뜻하게 켜져 있다'
    }
  };
  const THEME_COLOR = { day: '#F7F3EC', night: '#171310' };

  /* ---------- 상태 ---------- */
  const minutesAgo = (m) => new Date(Date.now() - m * 60000).toISOString();

  function seedState() {
    const tasks = {};
    Object.keys(ROOMS).forEach((id) => {
      tasks[id] = ROOMS[id].tasks.map((t) => ({ id: uid(), text: t.text, done: !!t.done }));
    });
    return {
      version: 1,
      theme: 'day',
      motion: true,
      tasks,
      tools: DEFAULT_TOOLS.map((t) => ({ id: uid(), ...t })),
      memos: [],
      events: [
        { id: uid(), room: 'hq', text: '회사 메일 3건 확인 · 답장 초안 준비', at: minutesAgo(24) },
        { id: uid(), room: 'work', text: '스틱맨 계산기 링크 점검 완료', at: minutesAgo(68) },
        { id: uid(), room: 'event', text: '오늘의 무료 응모 후보 2건 찾아 둠', at: minutesAgo(132) },
        { id: uid(), room: 'meet', text: '내일 일정 미리 알림 준비', at: minutesAgo(60 * 20) }
      ]
    };
  }

  let state;
  function load() {
    try {
      const raw = localStorage.getItem(KEY);
      if (!raw) return seedState();
      const parsed = JSON.parse(raw);
      if (!parsed || typeof parsed !== 'object') return seedState();
      const base = seedState();
      const merged = Object.assign(base, parsed);
      merged.tasks = Object.assign({}, base.tasks, parsed.tasks || {});
      Object.keys(ROOMS).forEach((id) => {
        if (!Array.isArray(merged.tasks[id])) merged.tasks[id] = base.tasks[id];
      });
      if (!Array.isArray(merged.tools)) merged.tools = base.tools;
      if (!Array.isArray(merged.memos)) merged.memos = [];
      if (!Array.isArray(merged.events)) merged.events = base.events;
      merged.theme = parsed.theme === 'night' ? 'night' : 'day';
      return merged;
    } catch (e) {
      return seedState();
    }
  }

  function save() {
    try {
      localStorage.setItem(KEY, JSON.stringify(state));
    } catch (e) {
      toast('저장 공간이 부족해서 이번 변경은 남지 않아요');
    }
  }

  /* ---------- 공통 ---------- */
  let toastTimer;
  function toast(msg) {
    const el = $('#toast');
    el.textContent = msg;
    el.classList.add('is-show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => el.classList.remove('is-show'), 1900);
  }

  function relTime(iso) {
    const t = new Date(iso).getTime();
    if (!t) return '';
    const diff = Math.max(0, Date.now() - t);
    const min = Math.floor(diff / 60000);
    if (min < 1) return '방금 전';
    if (min < 60) return min + '분 전';
    const hr = Math.floor(min / 60);
    if (hr < 24) return hr + '시간 전';
    const day = Math.floor(hr / 24);
    if (day === 1) return '어제';
    if (day < 7) return day + '일 전';
    return new Date(t).toLocaleDateString('ko-KR', { month: 'long', day: 'numeric' });
  }

  function countDone(roomId) {
    const list = state.tasks[roomId] || [];
    return { done: list.filter((t) => t.done).length, total: list.length };
  }

  function logEvent(room, text) {
    state.events.unshift({ id: uid(), room, text, at: new Date().toISOString() });
    state.events = state.events.slice(0, 40);
  }

  function progressPct(roomId) {
    const { done, total } = countDone(roomId);
    return total ? Math.round((done / total) * 100) : 0;
  }

  /* ---------- 렌더: 할 일 ---------- */
  function taskRow(room, t) {
    return '<li class="task' + (t.done ? ' is-done' : '') + '">' +
      '<button class="box' + (t.done ? ' is-on' : '') + '" data-act="toggle" data-room="' + room + '" data-id="' + t.id + '" aria-pressed="' + (t.done ? 'true' : 'false') + '" aria-label="완료 표시"></button>' +
      '<span class="txt">' + esc(t.text) + '</span>' +
      '<button class="del" data-act="del" data-room="' + room + '" data-id="' + t.id + '" aria-label="삭제">✕</button>' +
      '</li>';
  }

  function renderMeeting() {
    const list = state.tasks.meet || [];
    const { done, total } = countDone('meet');
    $('#meetList').innerHTML = list.length
      ? list.map((t) => taskRow('meet', t)).join('')
      : '<li class="empty" style="padding:14px 0">할 일이 비어 있어요. 아래에서 추가해 보세요.</li>';
    $('#meetCount').textContent = done + ' / ' + total;
    $('#meetBar').style.width = (total ? Math.round((done / total) * 100) : 0) + '%';
    const badge = $('#meetBadge');
    if (!total) { badge.textContent = '비어 있음'; badge.className = 'list-badge done'; }
    else if (done === total) { badge.textContent = '다 끝났어요'; badge.className = 'list-badge'; }
    else { badge.textContent = '진행 중'; badge.className = 'list-badge soft'; }

    const d = new Date();
    $('#todayDate').textContent = new Intl.DateTimeFormat('ko-KR', { month: 'long', day: 'numeric', weekday: 'long' }).format(d);
  }

  /* ---------- 렌더: 도구 ---------- */
  function renderTools() {
    const grid = $('#toolGrid');
    if (!state.tools.length) {
      grid.innerHTML = '<p class="empty" style="grid-column:1/-1">아직 등록한 도구가 없어요.</p>';
      return;
    }
    grid.innerHTML = state.tools.map((t) => {
      let host = '';
      try { host = new URL(t.url).hostname.replace(/^www\./, ''); } catch (e) { host = t.url; }
      return '<div class="tool">' +
        '<a class="tool-open" href="' + esc(t.url) + '" target="_blank" rel="noopener noreferrer">' +
          '<span class="tool-emoji">' + esc(t.emoji || '🔧') + '</span>' +
          '<span class="tool-name">' + esc(t.name) + '</span>' +
          '<span class="tool-host">' + esc(host) + '</span>' +
          '<span class="tool-arrow" aria-hidden="true">↗</span>' +
        '</a>' +
        '<button class="tool-x" data-act="del-tool" data-id="' + t.id + '" aria-label="' + esc(t.name) + ' 삭제">✕</button>' +
      '</div>';
    }).join('');
  }

  /* ---------- 렌더: 현황 ---------- */
  function renderStatus() {
    const grid = $('#statusGrid');
    const ids = ['hq', 'meet', 'work', 'event'];
    grid.innerHTML = ids.map((id) => {
      const r = ROOMS[id];
      const { done, total } = countDone(id);
      const last = state.events.find((e) => e.room === id);
      const sub = last ? last.text : '새로 챙길 일을 기다리는 중';
      return '<button class="status-card" data-act="open-room" data-room="' + id + '">' +
        '<span class="status-emoji">' + r.emoji + '</span>' +
        '<span class="status-main">' +
          '<span class="status-name"><i class="status-dot"></i>' + esc(r.name) + '</span>' +
          '<span class="status-sub">' + esc(sub) + '</span>' +
          '<span class="status-bar"><i style="width:' + (total ? Math.round((done / total) * 100) : 0) + '%"></i></span>' +
        '</span>' +
        '<span class="status-count">' + done + '/' + total + '</span>' +
      '</button>';
    }).join('');
  }

  function renderTimeline() {
    const el = $('#timeline');
    if (!state.events.length) {
      el.innerHTML = '<li class="empty">아직 기록이 없어요.</li>';
      return;
    }
    el.innerHTML = state.events.slice(0, 12).map((e) => {
      const room = ROOMS[e.room];
      const label = room ? room.name : (e.room === 'memo' ? '메모' : '오피스');
      return '<li class="tl-item" data-room="' + esc(e.room) + '">' +
        '<span class="tl-dot" aria-hidden="true"></span>' +
        '<div class="tl-body">' +
          '<p class="tl-text"><b>' + esc(label) + '</b> · ' + esc(e.text) + '</p>' +
          '<p class="tl-time">' + relTime(e.at) + '</p>' +
        '</div>' +
      '</li>';
    }).join('');
  }

  /* ---------- 렌더: 메모 ---------- */
  function renderMemos() {
    const list = state.memos;
    const el = $('#memoList');
    $('#memoBadge').textContent = list.length + '개';
    $('#memoEmpty').style.display = list.length ? 'none' : 'block';
    const sorted = list.slice().sort((a, b) => (b.pinned ? 1 : 0) - (a.pinned ? 1 : 0) || new Date(b.at) - new Date(a.at));
    el.innerHTML = sorted.map((m) => (
      '<li class="memo' + (m.pinned ? ' is-pinned' : '') + '">' +
        '<div class="memo-top">' +
          (m.pinned ? '<span class="memo-tag">고정</span>' : '') +
          '<span class="memo-time">' + relTime(m.at) + '</span>' +
          '<button class="memo-btn' + (m.pinned ? ' is-on' : '') + '" data-act="pin-memo" data-id="' + m.id + '" aria-label="고정">📌</button>' +
          '<button class="memo-btn" data-act="del-memo" data-id="' + m.id + '" aria-label="삭제">🗑</button>' +
        '</div>' +
        '<p class="memo-text">' + esc(m.text) + '</p>' +
      '</li>'
    )).join('');
  }

  /* ---------- 모션 ---------- */
  function renderMotion() {
    const chip = $('#motionChip');
    const on = state.motion !== false;
    document.body.classList.toggle('motion-off', !on);
    chip.classList.toggle('is-on', on);
    chip.setAttribute('aria-pressed', on ? 'true' : 'false');
    $('.chip-label', chip).textContent = on ? '모션 ON' : '모션 OFF';
  }

  /* ---------- 야간 모드 ---------- */
  function setOfficeBg(mode) {
    const img = $('#officeBg');
    if (!img) return;
    const g = BG[mode] || BG.day;
    if (img.getAttribute('src') !== g.jpg) {
      // JPEG가 없거나 못 불러오면 PNG로 넘어간다
      img.onerror = function () {
        img.onerror = null;
        img.src = g.png;
      };
      img.src = g.jpg;
    }
    img.alt = g.alt;
  }

  function renderTheme() {
    const night = state.theme === 'night';
    document.body.classList.toggle('theme-night', night);

    const chip = $('#themeChip');
    if (chip) {
      chip.classList.toggle('is-on', night);
      chip.setAttribute('aria-pressed', night ? 'true' : 'false');
      chip.setAttribute('aria-label', night ? '주간 모드로 바꾸기' : '야간 모드 켜기');
      chip.setAttribute('title', night ? '주간 모드로 바꾸기' : '야간 모드 켜기');
      $('#themeEmoji').textContent = night ? '☀️' : '🌙';
      $('#themeLabel').textContent = night ? '주간' : '야간';
    }

    const meta = $('#metaThemeColor');
    if (meta) meta.setAttribute('content', night ? THEME_COLOR.night : THEME_COLOR.day);

    setOfficeBg(night ? 'night' : 'day');
  }

  function toggleTheme() {
    state.theme = state.theme === 'night' ? 'day' : 'night';
    save();
    renderTheme();
    toast(state.theme === 'night' ? '야간 모드로 바꿨어요 🌙' : '주간 모드로 바꿨어요 ☀️');
  }

  function renderAll() {
    renderTheme();
    renderMotion();
    renderMeeting();
    renderTools();
    renderStatus();
    renderTimeline();
    renderMemos();
  }

  /* ---------- 탭 ---------- */
  function switchTab(name) {
    $$('.tab').forEach((b) => {
      const on = b.dataset.tab === name;
      b.classList.toggle('is-active', on);
      b.setAttribute('aria-selected', on ? 'true' : 'false');
    });
    $$('.panel').forEach((p) => {
      const on = p.id === 'panel-' + name;
      p.classList.toggle('is-active', on);
      p.hidden = !on;
    });
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  /* ---------- 바텀시트 ---------- */
  let lastFocus = null;

  function openSheet(opts) {
    lastFocus = document.activeElement;
    $('#sheetEmoji').textContent = opts.emoji;
    $('#sheetTitle').textContent = opts.title;
    $('#sheetMeta').textContent = opts.meta || '';
    const badge = $('#sheetBadge');
    badge.textContent = opts.badge || '';
    badge.className = 'sheet-badge' + (opts.soft ? ' soft' : '');
    badge.style.display = opts.badge ? '' : 'none';
    $('#sheetBody').innerHTML = opts.body;
    const wrap = $('#sheetWrap');
    wrap.hidden = false;
    document.body.style.overflow = 'hidden';
    $('#sheetBody').scrollTop = 0;
    if (opts.onMount) opts.onMount();
    setTimeout(() => { const c = $('.icon-btn', wrap); if (c) c.focus({ preventScroll: true }); }, 60);
  }

  function closeSheet() {
    const wrap = $('#sheetWrap');
    if (wrap.hidden) return;
    wrap.hidden = true;
    document.body.style.overflow = '';
    if (lastFocus && lastFocus.focus) { try { lastFocus.focus({ preventScroll: true }); } catch (e) {} }
  }

  function roomSheetBody(id) {
    const room = ROOMS[id];
    const { done, total } = countDone(id);
    const items = state.tasks[id] || [];
    const pct = total ? Math.round((done / total) * 100) : 0;
    return '<div class="sheet-summary">' + esc(room.summary) + '</div>' +
      '<div class="sheet-stats">' +
        '<div class="sheet-stat"><b>' + done + ' / ' + total + '</b><span>오늘 할 일 완료</span></div>' +
        '<div class="sheet-stat"><b>' + (room.parts ? '가동 중' : '휴게') + '</b><span>' + (room.parts ? '4개 파트 중 하나' : '잠깐 쉬는 자리') + '</span></div>' +
      '</div>' +
      '<div class="sheet-sec"><h4>' + (id === 'lounge' ? '쉬기 체크' : '할 일') + '</h4><span>' + pct + '% 완료</span></div>' +
      '<ul class="tasklist" id="sheetTaskList">' +
        (items.length ? items.map((t) => taskRow(id, t)).join('') : '<li class="empty" style="padding:12px 0">아직 할 일이 없어요.</li>') +
      '</ul>' +
      '<form class="addrow" id="sheetAddForm" data-room="' + id + '" autocomplete="off">' +
        '<input class="add-input" id="sheetAddInput" type="text" maxlength="80" placeholder="할 일 추가" aria-label="할 일 추가" />' +
        '<button class="add-btn" type="submit">추가</button>' +
      '</form>';
  }

  function openRoom(id) {
    const room = ROOMS[id];
    openSheet({
      emoji: room.emoji,
      title: room.name,
      meta: room.meta,
      badge: room.badge,
      soft: !!room.soft,
      body: roomSheetBody(id)
    });
  }

  function refreshSheet(id) {
    const list = $('#sheetTaskList');
    if (!list) return;
    const items = state.tasks[id] || [];
    list.innerHTML = items.length ? items.map((t) => taskRow(id, t)).join('') : '<li class="empty" style="padding:12px 0">아직 할 일이 없어요.</li>';
    const { done, total } = countDone(id);
    const pct = total ? Math.round((done / total) * 100) : 0;
    const stat = $$('.sheet-stat b')[0];
    if (stat) stat.textContent = done + ' / ' + total;
    const secSpan = $('.sheet-sec span');
    if (secSpan) secSpan.textContent = pct + '% 완료';
  }

  function openParts() {
    const rows = ['hq', 'meet', 'work', 'event'].map((id) => {
      const r = ROOMS[id];
      const { done, total } = countDone(id);
      return '<button class="sheet-row" data-act="open-room" data-room="' + id + '">' +
        '<span class="row-emoji">' + r.emoji + '</span>' +
        '<span class="row-main"><span class="row-name">' + esc(r.name) + '</span>' +
        '<span class="row-sub">' + esc(r.meta) + ' · 오늘 ' + done + '/' + total + '</span></span>' +
        '<span class="row-arrow">›</span>' +
      '</button>';
    }).join('');
    const totalDone = ['hq', 'meet', 'work', 'event'].reduce((n, id) => n + countDone(id).done, 0);
    openSheet({
      emoji: '🟢',
      title: '4개 파트 가동 중',
      meta: '절미 본부 · 실시간 상태',
      badge: 'LIVE',
      body: '<div class="sheet-summary">지휘실·대회의실·작업실·이벤트·주식, 네 파트가 오늘도 돌아가고 있어요. 방을 고르면 바로 들어가요.</div>' +
        '<div class="sheet-stats">' +
          '<div class="sheet-stat"><b>4</b><span>가동 중인 파트</span></div>' +
          '<div class="sheet-stat"><b>' + totalDone + '개</b><span>오늘 끝낸 일</span></div>' +
        '</div>' +
        '<div class="sheet-sec"><h4>파트 바로 가기</h4></div>' +
        '<div class="sheet-list">' + rows + '</div>' +
        '<p class="sheet-note">☕ 라운지는 파트가 아니라 대표님이 쉬는 자리예요.</p>'
    });
  }

  function openLevel() {
    openSheet({
      emoji: '🩷',
      title: 'Lv.3 절미',
      meta: '대표님 전담 비서',
      badge: 'Lv.3',
      soft: true,
      body: '<div class="sheet-summary">절미는 대표님 한 사람만 보는 개인 비서예요. Lv.3은 메일·일정·도구·응모까지 스스로 판단해서 챙길 수 있는 단계예요.</div>' +
        '<div class="sheet-stats">' +
          '<div class="sheet-stat"><b>Lv.3</b><span>지금 레벨</span></div>' +
          '<div class="sheet-stat"><b>4</b><span>맡은 파트</span></div>' +
        '</div>' +
        '<div class="sheet-sec"><h4>다음 레벨까지</h4><span>68%</span></div>' +
        '<div class="status-bar" style="margin:0 2px 14px"><i style="width:68%"></i></div>' +
        '<div class="sheet-list">' +
          '<div class="sheet-row"><span class="row-emoji">🗂</span><span class="row-main"><span class="row-name">잘하는 일</span><span class="row-sub">메일·일정 정리, 배송 추적, 웹앱 만들기</span></span></div>' +
          '<div class="sheet-row"><span class="row-emoji">🤝</span><span class="row-main"><span class="row-name">조심하는 일</span><span class="row-sub">돈이 나가거나 남에게 닿는 일은 먼저 여쭤요</span></span></div>' +
        '</div>' +
        '<p class="sheet-note">레벨은 함께한 일이 쌓이면 천천히 올라가요.</p>'
    });
  }

  /* ---------- 데이터 조작 ---------- */
  function addTask(room, text) {
    const clean = text.trim();
    if (!clean) return false;
    state.tasks[room].push({ id: uid(), text: clean, done: false });
    save();
    renderMeeting();
    renderStatus();
    refreshSheet(room);
    return true;
  }

  function toggleTask(room, id) {
    const t = (state.tasks[room] || []).find((x) => x.id === id);
    if (!t) return;
    t.done = !t.done;
    if (t.done) logEvent(room, "'" + t.text + "' 완료");
    save();
    renderMeeting();
    renderStatus();
    renderTimeline();
    refreshSheet(room);
  }

  function delTask(room, id) {
    const list = state.tasks[room];
    if (!list) return;
    state.tasks[room] = list.filter((t) => t.id !== id);
    save();
    renderMeeting();
    renderStatus();
    refreshSheet(room);
    toast('할 일을 지웠어요');
  }

  function addTool(name, url, emoji) {
    const cleanName = name.trim();
    let cleanUrl = url.trim();
    if (!cleanName) { toast('도구 이름을 먼저 적어 주세요'); return false; }
    if (!cleanUrl) { toast('주소를 함께 적어 주세요'); return false; }
    if (!/^https?:\/\//i.test(cleanUrl)) cleanUrl = 'https://' + cleanUrl;
    try { new URL(cleanUrl); } catch (e) { toast('주소 형식을 다시 확인해 주세요'); return false; }
    state.tools.unshift({ id: uid(), name: cleanName, url: cleanUrl, emoji: emoji.trim() || '🔧' });
    save();
    renderTools();
    toast('작업실에 도구를 붙였어요');
    return true;
  }

  function addMemo(text) {
    const clean = text.trim();
    if (!clean) return false;
    state.memos.unshift({ id: uid(), text: clean, pinned: false, at: new Date().toISOString() });
    logEvent('memo', '새 메모를 남김');
    save();
    renderMemos();
    renderTimeline();
    return true;
  }

  /* ---------- 이벤트 ---------- */
  document.addEventListener('click', (e) => {
    const tab = e.target.closest('.tab');
    if (tab) { switchTab(tab.dataset.tab); return; }

    const act = e.target.closest('[data-act]');
    if (act) {
      const a = act.dataset.act;
      const room = act.dataset.room;
      const id = act.dataset.id;
      if (a === 'toggle') { toggleTask(room, id); return; }
      if (a === 'del') { delTask(room, id); return; }
      if (a === 'open-room') { openRoom(room); return; }
      if (a === 'pin-memo') {
        const m = state.memos.find((x) => x.id === id);
        if (m) { m.pinned = !m.pinned; save(); renderMemos(); toast(m.pinned ? '메모를 고정했어요' : '고정을 풀었어요'); }
        return;
      }
      if (a === 'del-memo') {
        state.memos = state.memos.filter((x) => x.id !== id);
        save(); renderMemos(); toast('메모를 지웠어요');
        return;
      }
      if (a === 'del-tool') {
        state.tools = state.tools.filter((x) => x.id !== id);
        save(); renderTools(); toast('도구를 지웠어요');
        return;
      }
    }

    if (e.target.closest('[data-close]')) { closeSheet(); return; }

    const pin = e.target.closest('.pin');
    if (pin) { openRoom(pin.dataset.room); return; }

    const chip = e.target.closest('.chip');
    if (chip) {
      if (chip.id === 'motionChip') {
        state.motion = !(state.motion !== false);
        save();
        renderMotion();
        toast(state.motion ? '핀이 다시 둥실둥실 움직여요' : '모션을 잠깐 멈췄어요');
      } else if (chip.id === 'partsChip') {
        openParts();
      } else if (chip.id === 'levelChip') {
        openLevel();
      } else if (chip.id === 'themeChip') {
        toggleTheme();
      }
      return;
    }
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeSheet();
  });

  // 폼 제출 처리
  document.addEventListener('submit', (e) => {
    const form = e.target;
    if (form.id === 'meetForm') {
      e.preventDefault();
      const input = $('#meetInput');
      if (addTask('meet', input.value)) { input.value = ''; toast('할 일을 추가했어요'); }
      else toast('할 일을 적어 주세요');
      return;
    }
    if (form.id === 'sheetAddForm') {
      e.preventDefault();
      const input = $('#sheetAddInput');
      if (addTask(form.dataset.room, input.value)) { input.value = ''; toast('할 일을 추가했어요'); }
      else toast('할 일을 적어 주세요');
      return;
    }
    if (form.id === 'toolForm') {
      e.preventDefault();
      if (addTool($('#toolName').value, $('#toolUrl').value, $('#toolEmoji').value)) {
        $('#toolName').value = ''; $('#toolUrl').value = ''; $('#toolEmoji').value = '';
      }
      return;
    }
    if (form.id === 'memoForm') {
      e.preventDefault();
      const ta = $('#memoInput');
      if (addMemo(ta.value)) { ta.value = ''; $('#memoCount').textContent = '0 / 500'; toast('메모를 저장했어요'); }
      else toast('메모 내용을 적어 주세요');
      return;
    }
  });

  $('#memoInput').addEventListener('input', (e) => {
    $('#memoCount').textContent = e.target.value.length + ' / 500';
  });

  // Ctrl/⌘+Enter 로 메모 저장
  $('#memoInput').addEventListener('keydown', (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      e.preventDefault();
      $('#memoForm').requestSubmit();
    }
  });

  /* ---------- PWA ---------- */
  if ('serviceWorker' in navigator && location.protocol.startsWith('http')) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('sw.js').catch(() => {});
    });
  }

  /* ---------- 시작 ---------- */
  state = load();
  save();
  // 야간 배경은 미리 받아 두어 토글할 때 바로 바뀌게 한다
  if (BG.night.jpg) { const pre = new Image(); pre.src = BG.night.jpg; }
  renderAll();
  window.JeolmiOffice = { state, renderAll, openRoom, openParts, openLevel, closeSheet };
})();
