export const createPersonCardPanel = () => `
<div class="person-card-panel" id="person-card-panel" aria-live="polite">
  <div class="pc-card">
    <button class="pc-exit-btn" id="pc-exit-btn" type="button" title="关闭实体卡片">x</button>
    <div class="pc-hero" id="pc-hero">
      <img id="pc-hero-img" alt="" />
      <div class="pc-hero-fallback" id="pc-hero-fallback">体</div>
    </div>
    <div class="pc-header">
      <div class="pc-head-copy">
        <div class="pc-kicker">实体档案</div>
        <div class="pc-name" id="pc-name">实体卡片</div>
        <div class="pc-title" id="pc-title">等待选择对象</div>
      </div>
    </div>
    <div class="pc-summary" id="pc-summary">选择知识图谱节点后，bairui 会在这里显示对象摘要、来源、关联记录和可执行动作。</div>
    <div class="pc-section">
      <div class="pc-section-title">识别点</div>
      <ul class="pc-known-list" id="pc-known-list"></ul>
    </div>
    <div class="pc-tags" id="pc-tags"></div>
    <div class="pc-footer">
      <span class="pc-source" id="pc-source">来源：待机</span>
      <span class="pc-updated" id="pc-updated">--</span>
    </div>
  </div>
</div>
`;
