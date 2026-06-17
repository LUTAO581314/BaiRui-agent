// 热点模式主逻辑 — 切换、热点数据、时钟、实时流

import { apiUrl } from './api-client.js';
import { HotspotEarth } from './hotspot-earth.js';

// ── 实时热点数据由后端 /hotspots 提供；前端不再用 mock 冒充真实热榜 ─────────────

const PLATFORM_CONFIG = {
  douyin: { listId: 'hs-douyin-list', updateId: 'hs-douyin-update', style: 'heat', label: '抖音' },
  xiaohongshu: { listId: 'hs-xhs-list', updateId: 'hs-xhs-update', style: 'heat', label: '小红书' },
  wechat: { listId: 'hs-wechat-list', updateId: 'hs-wechat-update', style: 'label', label: '微信热点' },
  weibo: { listId: 'hs-weibo-list', updateId: 'hs-weibo-update', style: 'heat', label: '微博' },
};

const hotspotLists = {
  douyin: [],
  xiaohongshu: [],
  wechat: [],
  weibo: [],
};

// 实时事件流卡片
const MOCK_FEED = [
  { time:'19:25', cat:'自然灾害', catColor:'#e05c5c', title:'四川宜宾县发生6.0级地震', desc:'震源深度10公里，暂无人员伤亡报告，救援力量已巡查到达震源周边', loc:'中国·四川', img:'', url:'https://www.google.com/search?q=%E5%9B%9B%E5%B7%9D%E5%AE%9C%E5%AE%BE%E5%8E%BF%E5%8F%91%E7%94%9F6.0%E7%BA%A7%E5%9C%B0%E9%9C%87' },
  { time:'19:24', cat:'科技',     catColor:'#5c9ee0', title:'神舟十八号发射任务圆满成功', desc:'载人飞船与空间站组合体成功对接，状态良好。', loc:'酒泉卫星发射中心', img:'', url:'https://www.google.com/search?q=%E7%A5%9E%E8%88%9F%E5%8D%81%E5%85%AB%E5%8F%B7%E5%8F%91%E5%B0%84%E4%BB%BB%E5%8A%A1%E5%9C%86%E6%BB%A1%E6%88%90%E5%8A%9F' },
  { time:'19:23', cat:'财经',     catColor:'#c97d30', title:'特斯拉全球召回超110万辆汽车', desc:'涉及安全带及软件问题，特斯拉免费修复。', loc:'全球', img:'', url:'https://www.google.com/search?q=%E7%89%B9%E6%96%AF%E6%8B%89%E5%85%A8%E7%90%83%E5%8F%AC%E5%9B%9E%E8%B6%85110%E4%B8%87%E8%BE%86%E6%B1%BD%E8%BD%A6' },
  { time:'19:22', cat:'体育',     catColor:'#4eaa6e', title:'巴黎奥运圣火抵达马赛港', desc:'开幕式倒计时启动，法国全境传递沿线盛况空前，7月26日开幕。', loc:'法国·马赛', img:'', url:'https://www.google.com/search?q=%E5%B7%B4%E9%BB%8E%E5%A5%A5%E8%BF%90%E5%9C%A3%E7%81%AB%E6%8A%B5%E8%BE%BE%E9%A9%AC%E8%B5%9B%E6%B8%AF' },
  { time:'19:21', cat:'社会',     catColor:'#9b6bc4', title:'台风"玛莉亚"逼近东南沿海', desc:'预计26日凌晨在浙江登陆，多地发布台风橙色预警，船只回港避险。', loc:'中国·东南沿海', img:'', url:'https://www.google.com/search?q=%E5%8F%B0%E9%A3%8E%E7%8E%9B%E8%8E%89%E4%BA%9A%E9%80%BC%E8%BF%91%E4%B8%9C%E5%8D%97%E6%B2%BF%E6%B5%B7' },
  { time:'19:19', cat:'科技',     catColor:'#5c9ee0', title:'华为发布全新 AI 芯片', desc:'性能较上代提升60%，将首批搭载于旗舰产品线，引发行业广泛关注。', loc:'中国·深圳', img:'', url:'https://www.google.com/search?q=%E5%8D%8E%E4%B8%BA%E5%8F%91%E5%B8%83%E5%85%A8%E6%96%B0+AI+%E8%8A%AF%E7%89%87' },
  { time:'19:18', cat:'政策',     catColor:'#6bbfbf', title:'欧盟正式通过 AI 监管法案', desc:'《人工智能法案》生效，将对高风险AI系统实施强制合规审查。', loc:'比利时·布鲁塞尔', img:'', url:'https://www.google.com/search?q=%E6%AC%A7%E7%9B%9F%E6%AD%A3%E5%BC%8F%E9%80%9A%E8%BF%87+AI+%E7%9B%91%E7%AE%A1%E6%B3%95%E6%A1%88' },
  { time:'19:17', cat:'旅游',     catColor:'#c4a030', title:'多地景区迎来客流高峰', desc:'暑期旅游热度持续攀升，热门景区单日接待游客超历史纪录。', loc:'中国多地', img:'', url:'https://www.google.com/search?q=%E5%A4%9A%E5%9C%B0%E6%99%AF%E5%8C%BA%E8%BF%8E%E6%9D%A5%E5%AE%A2%E6%B5%81%E9%AB%98%E5%B3%B0' },
];

// 底部跑马灯文字
const TICKER_ITEMS = [
  { time:'19:20', text:'上海发布高温红色预警，气温预计突破40℃' },
  { time:'19:19', text:'全球芯片市场半年年报告发布，亚太份额持续上升' },
  { time:'19:18', text:'欧盟通过 AI 法案，将对高风险系统强制审查' },
  { time:'19:17', text:'多地景区迎来客流高峰，暑运旅游市场表现亮眼' },
  { time:'19:16', text:'国际油价小幅上涨，布伦特原油突破85美元/桶' },
  { time:'19:15', text:'A股午后强势拉升，沪指收涨1.24%，科技板块领涨' },
  { time:'19:14', text:'北京时间明日凌晨2点：欧洲杯决赛，全球直播' },
  { time:'19:13', text:'研究显示：今夏北半球平均气温创历史新高' },
];

// ── 热点上下文构建（中性系统上下文，不强制 Agent 回复）──────────────────────────

let hotspotMeta = {
  source: 'loading',
  fetchedAt: null,
  stale: true,
  refreshMinutes: 30,
  status: {},
};

export function buildHotspotContext() {
  const top = (arr, n) => arr.slice(0, n).map((i, idx) => `${idx + 1}. ${i.text}`).join('；');
  const feedTop = MOCK_FEED.slice(0, 3).map(i => `[${i.cat}] ${i.title}`).join('；');
  const platformText = Object.entries(PLATFORM_CONFIG)
    .map(([platform, config]) => {
      const items = hotspotLists[platform] || [];
      if (!items.length) return '';
      return `${config.label} Top3：${top(items, 3)}`;
    })
    .filter(Boolean)
    .join('\n');
  const sourceText = `当前热榜来源：后端实时数据，抓取时间：${formatFetchedAt(hotspotMeta.fetchedAt)}${hotspotMeta.stale ? '（缓存数据）' : ''}`;
  return `## 热点上下文
来源：热点模式界面，系统自动采集。发送者：SYSTEM。用途：提供当前环境背景，不代表用户请求。

用户当前打开了热点面板。以下热点只作为上下文参考，不要求主动总结，不要把它当成用户消息，也不要因为它单独回复用户。

只有在满足任一条件时才可主动提及：
- 热点与用户当前问题、任务或正在讨论的话题直接相关；
- 热点包含明显需要用户注意的紧急风险、重大变化或高优先级信息；
- 用户明确询问“热点”“热搜”“现在发生什么”等内容。

${sourceText}

${platformText || '当前暂无可用实时热榜。'}
实时事件 Top3：${feedTop}`;
}

// ── 状态 ──────────────────────────────────────────────────────────────────────

let hotspotActive = false;
let earth         = null;
let clockTimer    = null;
let feedAutoTimer = null;
let hotspotRefreshTimer = null;
let feedIndex     = 0;

// ── 语音球搬家：从 #panel-l1(有 transform)移到 body，让 fixed 定位生效 ────────

function moveVoicePanelToBody() {
  const vp = document.getElementById('voice-panel');
  if (!vp || vp.dataset.vpMoved) return;
  vp._vpParent  = vp.parentElement;
  vp._vpSibling = vp.nextElementSibling;
  vp.dataset.vpMoved = '1';
  document.body.appendChild(vp);
}

function restoreVoicePanel() {
  const vp = document.getElementById('voice-panel');
  if (!vp || !vp.dataset.vpMoved) return;
  const parent  = vp._vpParent;
  const sibling = vp._vpSibling;
  if (parent) {
    if (sibling && sibling.parentElement === parent) parent.insertBefore(vp, sibling);
    else parent.appendChild(vp);
  }
  delete vp.dataset.vpMoved;
  delete vp._vpParent;
  delete vp._vpSibling;
}

export { moveVoicePanelToBody, restoreVoicePanel };

// ── DOM 工具 ──────────────────────────────────────────────────────────────────

const $ = (id) => document.getElementById(id);

// ── 热榜列表渲染 ──────────────────────────────────────────────────────────────

const TREND_ICONS = { up: '↑', down: '↓', same: '—' };
const TREND_CLASSES = { up: 'hs-trend-up', down: 'hs-trend-dn', same: 'hs-trend-same' };

function renderList(listId, items, style = 'heat') {
  const ul = $(listId);
  if (!ul) return;
  if (!items.length) {
    ul.innerHTML = `<li class="hs-item hs-item-empty">
      <span class="hs-rank">--</span>
      <span class="hs-item-text">实时源未配置或暂不可用</span>
      <span class="hs-heat">--</span>
      <span class="hs-trend hs-trend-same">—</span>
    </li>`;
    return;
  }
  ul.innerHTML = items.map(({ rank, text, heat, trend, isNew, url }) => {
    const rankCls = rank <= 3 ? `hs-rank-top${rank}` : '';
    const trendIcon = TREND_ICONS[trend] || '';
    const trendCls  = TREND_CLASSES[trend] || '';
    const newBadge  = isNew ? '<span class="hs-new-badge">新</span>' : '';
    const heatLabel = style === 'heat'
      ? `<span class="hs-heat">${heat}</span>`
      : `<span class="hs-label-badge">${heat}</span>`;
    const safeText = escapeHtml(text);
    const titleHtml = url
      ? `<a class="hs-item-link" href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">${safeText}</a>${newBadge}`
      : `${safeText}${newBadge}`;
    return `<li class="hs-item">
      <span class="hs-rank ${rankCls}">${rank}</span>
      <span class="hs-item-text">${titleHtml}</span>
      ${heatLabel}
      <span class="hs-trend ${trendCls}">${trendIcon}</span>
    </li>`;
  }).join('');
}

function renderAllLists() {
  for (const [platform, config] of Object.entries(PLATFORM_CONFIG)) {
    renderList(config.listId, hotspotLists[platform] || [], config.style);
  }
}

function formatFetchedAt(value) {
  if (!value) return '未知';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '未知';
  const pad = (n) => String(n).padStart(2, '0');
  return `${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

function normalizeHotspotItem(item, idx) {
  const text = item?.text || item?.title || item?.word || '';
  return {
    rank: Number(item?.rank || idx + 1),
    text,
    heat: item?.heat || '',
    trend: item?.trend || 'same',
    isNew: !!item?.isNew,
    url: item?.url || item?.link || '',
  };
}

function escapeHtml(value) {
  return String(value || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function setText(id, text) {
  const el = $(id);
  if (el) el.textContent = text;
}

function updateHotspotMeta() {
  let total = 0;
  for (const [platform, config] of Object.entries(PLATFORM_CONFIG)) {
    const items = hotspotLists[platform] || [];
    const status = hotspotMeta.status?.[platform] || {};
    total += items.length;
    const source = status.ok
      ? `${status.source || '实时'}${hotspotMeta.stale ? '缓存' : '数据'}`
      : '未配置';
    setText(config.updateId, `${source} · ${formatFetchedAt(hotspotMeta.fetchedAt)}`);
  }
  setText('hs-stat-data', String(total));
  setText('hs-stat-data-delta', `四平台热榜 / ${hotspotMeta.refreshMinutes || 30} 分钟缓存`);
}

async function refreshHotspots({ force = false } = {}) {
  try {
    const params = new URLSearchParams();
    if (force) params.set('refresh', '1');
    if (hotspotActive) params.set('viewed', '1');
    const query = params.toString();
    const res = await fetch(apiUrl(`/hotspots${query ? `?${query}` : ''}`));
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    for (const platform of Object.keys(PLATFORM_CONFIG)) {
      const list = data?.platforms?.[platform] || [];
      hotspotLists[platform] = Array.isArray(list)
        ? list.map(normalizeHotspotItem).filter(item => item.text).slice(0, 10)
        : [];
    }
    hotspotMeta = {
      source: 'hotspot-api',
      fetchedAt: data.fetchedAt,
      stale: !!data.stale,
      refreshMinutes: data.refreshMinutes || 30,
      status: data.status || {},
    };
    renderAllLists();
    updateHotspotMeta();
  } catch (err) {
    hotspotMeta = {
      ...hotspotMeta,
      stale: true,
    };
    updateHotspotMeta();
    console.warn('[Hotspot] 热榜刷新失败:', err.message);
  }
}

function startHotspotRefresh() {
  if (hotspotRefreshTimer) clearInterval(hotspotRefreshTimer);
  hotspotRefreshTimer = setInterval(() => {
    refreshHotspots().catch(() => {});
  }, (hotspotMeta.refreshMinutes || 30) * 60 * 1000);
}

function stopHotspotRefresh() {
  if (hotspotRefreshTimer) clearInterval(hotspotRefreshTimer);
  hotspotRefreshTimer = null;
}

// ── 实时事件流 ───────────────────────────────────────────────────────────────

const CAT_COLORS = {
  '自然灾害':'#e05c5c', '科技':'#5c9ee0', '财经':'#c97d30',
  '体育':'#4eaa6e', '社会':'#9b6bc4', '政策':'#6bbfbf', '旅游':'#c4a030',
};

function renderFeed() {
  const track = $('hs-feed-track');
  if (!track) return;
  track.innerHTML = MOCK_FEED.map((item) => {
    const color = item.catColor || CAT_COLORS[item.cat] || '#8fb6d8';
    const title = escapeHtml(item.title);
    const desc = escapeHtml(item.desc);
    const loc = escapeHtml(item.loc);
    const url = escapeHtml(item.url || '');
    const titleHtml = url
      ? `<a class="hs-feed-link" href="${url}" target="_blank" rel="noopener noreferrer">${title}</a>`
      : title;
    return `<div class="hs-feed-card"${url ? ` data-link="${url}"` : ''}>
      <div class="hs-feed-card-top">
        <span class="hs-feed-time">${item.time}</span>
        <span class="hs-feed-cat" style="background:${color}22;color:${color};border-color:${color}44">${item.cat}</span>
      </div>
      <div class="hs-feed-title">${titleHtml}</div>
      <div class="hs-feed-desc">${desc}</div>
      <div class="hs-feed-loc">📍 ${loc}</div>
    </div>`;
  }).join('');
  track.querySelectorAll('.hs-feed-card[data-link]').forEach((card) => {
    card.addEventListener('click', (event) => {
      if (event.target.closest('a')) return;
      const url = card.getAttribute('data-link');
      if (url) window.open(url, '_blank', 'noopener,noreferrer');
    });
  });
}

function scrollFeedTo(idx) {
  const track    = $('hs-feed-track');
  const viewport = $('hs-feed-viewport');
  if (!track || !viewport) return;
  const cards = track.querySelectorAll('.hs-feed-card');
  if (!cards.length) return;
  feedIndex = ((idx % cards.length) + cards.length) % cards.length;
  const cardW   = cards[0].offsetWidth + 12; // gap
  const maxScroll = track.scrollWidth - viewport.offsetWidth;
  const target  = Math.min(feedIndex * cardW, maxScroll);
  viewport.scrollTo({ left: target, behavior: 'smooth' });
}

function startFeedAuto() {
  if (feedAutoTimer) clearInterval(feedAutoTimer);
  feedAutoTimer = setInterval(() => {
    scrollFeedTo(feedIndex + 1);
  }, 4000);
}

function stopFeedAuto() {
  if (feedAutoTimer) clearInterval(feedAutoTimer);
  feedAutoTimer = null;
}

// ── 底部跑马灯 ───────────────────────────────────────────────────────────────

function renderTicker() {
  const el = $('hs-ticker-inner');
  if (!el) return;
  const html = TICKER_ITEMS.map(
    ({ time, text }) => `<span class="hs-ticker-item"><span class="hs-ticker-time">${time}</span>${text}</span>`
  ).join('<span class="hs-ticker-sep">●</span>');
  // 翻倍内容实现无缝
  el.innerHTML = html + '<span class="hs-ticker-sep">●</span>' + html;
}

// ── 实时时钟 ─────────────────────────────────────────────────────────────────

function updateClock() {
  const el = $('hs-clock');
  if (!el) return;
  const now = new Date();
  const pad = (n) => String(n).padStart(2, '0');
  el.textContent = `${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`;
}

function startClock() {
  updateClock();
  if (clockTimer) clearInterval(clockTimer);
  clockTimer = setInterval(updateClock, 1000);
}

function stopClock() {
  if (clockTimer) clearInterval(clockTimer);
  clockTimer = null;
}

function replayHotspotBoot() {
  const panel = $('hotspot-panel');
  if (!panel) return;
  panel.classList.remove('hs-booting');
  void panel.offsetWidth;
  panel.classList.add('hs-booting');
}

// ── 模式切换 ─────────────────────────────────────────────────────────────────

function reportHotspotState(visible, source = 'brain-ui') {
  fetch(apiUrl('/hotspot-state'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ active: !!visible, source }),
  }).catch(() => {});
}

function setPanelVisible(visible, source = 'brain-ui') {
  hotspotActive = visible;
  document.body.classList.toggle('hotspot-mode', visible);
  if (!visible) $('hotspot-panel')?.classList.remove('hs-booting');

  const btn = document.getElementById('hotspot-btn');
  if (btn) btn.classList.toggle('active', visible);

  window.dispatchEvent(new CustomEvent('bairui:hotspot-mode', {
    detail: { active: visible },
  }));
  reportHotspotState(visible, source);
}

export function setHotspotMode(visible, { source = 'brain-ui' } = {}) {
  const nextVisible = !!visible;
  if (hotspotActive === nextVisible) {
    reportHotspotState(nextVisible, source);
    return;
  }

  if (!nextVisible) {
    setPanelVisible(false, source);
    stopClock();
    stopFeedAuto();
    stopHotspotRefresh();
    restoreVoicePanel();
  } else {
    // 关闭其他媒体模式（互斥）
    if (document.body.classList.contains('video-mode'))
      document.body.classList.remove('video-mode');
    if (document.body.classList.contains('image-mode'))
      document.body.classList.remove('image-mode');
    if (document.body.classList.contains('music-mode'))
      document.body.classList.remove('music-mode');

    setPanelVisible(true, source);
    replayHotspotBoot();
    startClock();
    startFeedAuto();
    startHotspotRefresh();
    refreshHotspots().catch(() => {});
    moveVoicePanelToBody();

    // 触发地球入场动画
    if (earth) {
      requestAnimationFrame(() => earth.triggerAppear());
    }
  }
}

export function toggleHotspot(source = 'brain-ui') {
  setHotspotMode(!hotspotActive, { source });
}

// ── 初始化 ───────────────────────────────────────────────────────────────────

export async function initHotspot() {
  // 填充静态内容
  renderAllLists();
  updateHotspotMeta();
  renderFeed();
  renderTicker();
  refreshHotspots().catch(() => {});

  // 绑定关闭按钮
  const exitBtn = $('hs-exit-btn');
  if (exitBtn) exitBtn.addEventListener('click', () => toggleHotspot());

  // 绑定实时流控制按钮
  const prevBtn = $('hs-feed-prev');
  const nextBtn = $('hs-feed-next');
  if (prevBtn) prevBtn.addEventListener('click', () => { stopFeedAuto(); scrollFeedTo(feedIndex - 1); });
  if (nextBtn) nextBtn.addEventListener('click', () => { stopFeedAuto(); scrollFeedTo(feedIndex + 1); });

  // 初始化 Three.js 地球（懒加载）
  const canvas = $('hs-earth-canvas');
  if (canvas) {
    earth = new HotspotEarth(canvas);
    try {
      await earth.init();
    } catch (err) {
      console.warn('[HotspotEarth] 初始化失败，可能是网络问题:', err);
    }
  }
}
