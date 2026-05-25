import type { CSSProperties } from 'react';

import { resolveApiUrl } from '../api/client';
import type { Dynasty, GeneratedScriptDemo } from '../types/game';

type StartPageProps = {
  mode: 'home' | 'setup';
  dynasties: Dynasty[];
  selectedDynastyId: string;
  keywordText: string;
  busy: boolean;
  errorText: string;
  savedDemos: GeneratedScriptDemo[];
  savedDemosLoaded: boolean;
  savedDemosError: string;
  onStart: () => void;
  onSelectDynasty: (dynastyId: string) => void;
  onKeywordTextChange: (value: string) => void;
  onPrepareScenario: () => void;
  onOpenSavedDemo: (scriptId: string) => void;
};

const entryBackground = '/generated-ui/concept-entry-bg.png';
const dynastyCardSheet = '/generated-ui/dynasty-cards-sheet.png';

const dynastyLabels: Record<string, { mark: string; route: string; hint: string; sheetX: string; accent: string }> = {
  ming: { mark: '明', route: '固定 Demo', hint: '直入书坊焚稿案。', sheetX: '100%', accent: '#d7a965' },
  song: { mark: '宋', route: 'AI 生成', hint: '填入关键词生成北宋案件。', sheetX: '50%', accent: '#caa66a' },
  tang: { mark: '唐', route: 'AI 生成', hint: '填入关键词生成晚唐案件。', sheetX: '0%', accent: '#b88a51' },
  late_tang: { mark: '唐', route: 'AI 生成', hint: '填入关键词生成晚唐案件。', sheetX: '0%', accent: '#b88a51' },
};

const flowItems = ['开始游戏', '选择朝代 / 关键词', '剧本生成', '身份选择与概览', '开始游戏'];

function conceptStyle(): CSSProperties {
  return { '--concept-bg': `url(${entryBackground})` } as CSSProperties;
}

function dynastyStyle(dynastyId: string): CSSProperties {
  const meta = dynastyLabels[dynastyId];
  return {
    '--dynasty-sheet': `url(${dynastyCardSheet})`,
    '--dynasty-position': meta ? `${meta.sheetX} 50%` : '50% 50%',
    '--dynasty-accent': meta?.accent ?? '#c99b58',
  } as CSSProperties;
}

function keywordCount(value: string): number {
  return value
    .replace(/\n/g, '、')
    .split(/[、，,；;]/)
    .map((item) => item.trim())
    .filter(Boolean).length;
}

function FlowStrip({ activeIndex }: { activeIndex: number }) {
  return (
    <nav className="concept-flow-strip" aria-label="主流程">
      {flowItems.map((item, index) => (
        <span key={`${item}-${index}`} className={index <= activeIndex ? 'flow-node active' : 'flow-node'}>
          {item}
          {index < flowItems.length - 1 ? <i aria-hidden="true" /> : null}
        </span>
      ))}
    </nav>
  );
}

export function StartPage({
  mode,
  dynasties,
  selectedDynastyId,
  keywordText,
  busy,
  errorText,
  savedDemos,
  savedDemosLoaded,
  savedDemosError,
  onStart,
  onSelectDynasty,
  onKeywordTextChange,
  onPrepareScenario,
  onOpenSavedDemo,
}: StartPageProps) {
  const effectiveSelectedDynastyId = selectedDynastyId || dynasties.find((dynasty) => dynasty.enabled)?.dynasty_id || '';
  const activeDynasty = dynasties.find((dynasty) => dynasty.dynasty_id === effectiveSelectedDynastyId) ?? null;
  const activeMeta = activeDynasty
    ? dynastyLabels[activeDynasty.dynasty_id] ?? {
      mark: activeDynasty.name.replace(/代$/, '').slice(-1) || activeDynasty.name.slice(0, 1),
      route: '入口',
      hint: activeDynasty.core_mood,
      sheetX: '50%',
      accent: '#c99b58',
    }
    : null;
  const isGeneratedRoute = Boolean(activeDynasty && activeDynasty.dynasty_id !== 'ming');
  const count = keywordCount(keywordText);
  const savedDemoCountText = !savedDemosLoaded
    ? '读取中'
    : savedDemosError
      ? '暂时无法读取'
      : `${savedDemos.length} 个可直接游玩`;

  if (mode === 'home') {
    return (
      <main className="concept-entry-page concept-home-page" style={conceptStyle()}>
        <div className="concept-atmosphere" />
        <header className="concept-page-title">
          <span className="title-rule" />
          <div>
            <h1>历史悬疑 · AI 剧本游戏</h1>
            <p>主流程 UI 概念演示</p>
          </div>
          <span className="title-rule" />
        </header>

        <section className="concept-home-stage" aria-label="登陆页">
          <div className="concept-home-card gilded-panel">
            <div className="home-content">
              <span className="home-seal">录</span>
              <h2>探古寻真</h2>
              <p>穿越时空 · 破解谜局 · 寻找真相</p>
              <button type="button" className="imperial-button entry-start-button" onClick={onStart}>
                <span>开始游戏</span>
              </button>
            </div>
          </div>
        </section>

        <FlowStrip activeIndex={0} />
      </main>
    );
  }

  return (
    <main className="concept-entry-page concept-setup-page" style={conceptStyle()}>
      <div className="concept-atmosphere" />
      <header className="concept-page-title compact">
        <span className="title-rule" />
        <div>
          <h1>选择朝代 / 关键词</h1>
          <p>步骤 1/3 · 明代直达固定 Demo，北宋与晚唐进入真实 AI 生成</p>
        </div>
        <span className="title-rule" />
      </header>

      <section className="concept-setup-board" aria-label="朝代选择界面">
        <div className="concept-phone-panel gilded-panel">
          <div className="ornate-heading">
            <span />
            <h2>选择朝代</h2>
            <span />
          </div>

          <div className="concept-dynasty-rail">
            {dynasties.map((dynasty) => {
              const meta = dynastyLabels[dynasty.dynasty_id] ?? {
                mark: dynasty.name.replace(/代$/, '').slice(-1) || dynasty.name.slice(0, 1),
                route: '入口',
                hint: dynasty.core_mood,
                sheetX: '50%',
                accent: '#c99b58',
              };
              const active = effectiveSelectedDynastyId === dynasty.dynasty_id;
              return (
                <button
                  key={dynasty.dynasty_id}
                  type="button"
                  className={active ? 'concept-dynasty-card active' : 'concept-dynasty-card'}
                  style={dynastyStyle(dynasty.dynasty_id)}
                  onClick={() => onSelectDynasty(dynasty.dynasty_id)}
                  disabled={busy || !dynasty.enabled}
                >
                  <span className="dynasty-card-image" aria-hidden="true" />
                  <span className="dynasty-card-glow" aria-hidden="true" />
                  <strong>{meta.mark}</strong>
                  <span className="dynasty-card-era">{dynasty.period_label}</span>
                  <small>{dynasty.name} · {dynasty.core_mood}</small>
                  <em>{meta.route}</em>
                </button>
              );
            })}
          </div>
        </div>

        <aside className="concept-phone-panel keyword-scroll-panel gilded-panel">
          <div className="ornate-heading">
            <span />
            <h2>关键词</h2>
            <span />
          </div>

          <section className="selected-dynasty-emblem" style={dynastyStyle(activeDynasty?.dynasty_id ?? 'song')}>
            <span>{activeMeta?.mark ?? '？'}</span>
            <div>
              <p>当前入口</p>
              <h2>{activeDynasty ? activeDynasty.name : '尚未选择'}</h2>
            </div>
          </section>

          <p className="setup-teaser">
            {activeDynasty
              ? activeDynasty.dynasty_id === 'ming'
                ? '明代为稳定路演剧本，将直接进入书坊焚稿案。'
                : activeMeta?.hint
              : '先选择朝代，再填写 1-8 个关键词。'}
          </p>

          <div className="keyword-token-row" aria-label="关键词示例">
            {['雨夜', '密信', '书坊', '火痕', '旧案'].map((token) => <span key={token}>{token}</span>)}
          </div>

          <label className="concept-textarea-shell">
            <span>{isGeneratedRoute ? `关键词（${count}/8）` : '关键词（明代 Demo 可不填）'}</span>
            <textarea
              value={keywordText}
              onChange={(event) => onKeywordTextChange(event.target.value)}
              placeholder="例如：驿站、军报、雨夜、粮草"
              rows={5}
              disabled={busy || !isGeneratedRoute}
            />
          </label>

          {errorText ? <div className="error-banner cover-error">{errorText}</div> : null}

          <button type="button" className="imperial-button setup-generate-button" onClick={onPrepareScenario} disabled={busy || !activeDynasty}>
            <span>{busy ? '处理中...' : activeDynasty?.dynasty_id === 'ming' ? '开始游戏' : '下一步'}</span>
          </button>
        </aside>
      </section>

      <section className="saved-demo-strip gilded-panel" aria-label="已保存生成 Demo">
        <div className="saved-demo-heading">
          <span>已生成 Demo</span>
          <strong>{savedDemoCountText}</strong>
        </div>
        <div className="saved-demo-list">
          {savedDemos.length > 0 ? savedDemos.slice(0, 6).map((demo) => {
            const thumbnailUrl = resolveApiUrl(demo.thumbnail_url);
            return (
              <button
                key={demo.script_id}
                type="button"
                className="saved-demo-card"
                onClick={() => onOpenSavedDemo(demo.script_id)}
                disabled={busy || !demo.playable}
              >
                {thumbnailUrl ? <img src={thumbnailUrl} alt={`${demo.title} 主场景`} /> : <span className="saved-demo-thumb-fallback">{demo.dynasty_id === 'song' ? '宋' : '唐'}</span>}
                <span className="saved-demo-card-copy">
                  <strong>{demo.title}</strong>
                  <small>{demo.keywords.join('、')}</small>
                  <em>{demo.counts.locations} 景 · {demo.counts.clues} 线索 · {demo.counts.endings} 结局</em>
                </span>
              </button>
            );
          }) : (
            <div className="saved-demo-empty" role="status">
              <strong>{savedDemosError || (savedDemosLoaded ? '暂无合格 Demo' : '正在读取 Demo')}</strong>
              <span>{savedDemosLoaded ? '完成生成后显示' : '同步中'}</span>
            </div>
          )}
        </div>
      </section>

      <FlowStrip activeIndex={1} />
    </main>
  );
}
