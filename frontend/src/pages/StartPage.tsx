import type { CSSProperties } from 'react';

import type { Dynasty } from '../types/game';

type StartPageProps = {
  mode: 'home' | 'setup';
  dynasties: Dynasty[];
  selectedDynastyId: string;
  keywordText: string;
  busy: boolean;
  errorText: string;
  onStart: () => void;
  onSelectDynasty: (dynastyId: string) => void;
  onKeywordTextChange: (value: string) => void;
  onPrepareScenario: () => void;
};

type DynastyVisualMeta = {
  shortName: string;
  sheetPosition: string;
  accent: string;
};

const entryBackground = '/generated-ui/concept-entry-bg.png';
const dynastyCardsSheet = '/generated-ui/dynasty-cards-sheet.png';

const dynastyVisuals: Record<string, DynastyVisualMeta> = {
  ming: {
    shortName: '明',
    sheetPosition: '100% 50%',
    accent: '#d8a45f',
  },
  song: {
    shortName: '宋',
    sheetPosition: '50% 50%',
    accent: '#b9c49e',
  },
  tang: {
    shortName: '唐',
    sheetPosition: '0% 50%',
    accent: '#c18a56',
  },
};

const fallbackDynastyVisual: DynastyVisualMeta = {
  shortName: '疑',
  sheetPosition: '0% 50%',
  accent: '#c9a063',
};

function conceptStyle(extra?: Record<string, string>): CSSProperties {
  return {
    '--concept-bg': `url(${entryBackground})`,
    ...extra,
  } as CSSProperties;
}

function getDynastyVisual(dynasty: Dynasty): DynastyVisualMeta {
  return dynastyVisuals[dynasty.dynasty_id] ?? fallbackDynastyVisual;
}

export function StartPage({
  mode,
  dynasties,
  selectedDynastyId,
  keywordText,
  busy,
  errorText,
  onStart,
  onSelectDynasty,
  onKeywordTextChange,
  onPrepareScenario,
}: StartPageProps) {
  if (mode === 'home') {
    return (
      <main className="entry-page concept-entry-page concept-home-page" style={conceptStyle()}>
        <div className="concept-atmosphere" />

        <header className="concept-page-title" aria-label="游戏标题">
          <span className="title-rule" />
          <div>
            <h1>历史悬疑 · AI 剧本游戏</h1>
            <p>选择时代，生成你的悬疑剧本</p>
          </div>
          <span className="title-rule" />
        </header>

        <section className="concept-home-stage" aria-label="登录页">
          <div className="concept-home-card gilded-panel">
            <div className="home-content">
              <h2>探古寻真</h2>
              <p>穿越时空 · 破解迷局 · 寻找真相</p>
              <button type="button" className="imperial-button entry-start-button" onClick={onStart}>
                <span>开始游戏</span>
              </button>
            </div>
          </div>
        </section>

        <nav className="concept-flow-strip" aria-label="主流程">
          <span className="flow-node active">开始游戏</span>
          <i />
          <span className="flow-node">选择朝代</span>
          <i />
          <span className="flow-node">剧本生成</span>
          <i />
          <span className="flow-node">身份选择</span>
        </nav>
      </main>
    );
  }

  const selectedDynasty = dynasties.find((dynasty) => dynasty.dynasty_id === selectedDynastyId) ?? null;
  const displayDynasty = selectedDynasty ?? dynasties.find((dynasty) => dynasty.enabled) ?? dynasties[0] ?? null;
  const displayVisual = displayDynasty ? getDynastyVisual(displayDynasty) : fallbackDynastyVisual;

  return (
    <main
      className="entry-page concept-entry-page concept-setup-page"
      style={conceptStyle()}
    >
      <div className="concept-atmosphere" />

      <header className="concept-page-title compact" aria-label="选择朝代标题">
        <span className="title-rule" />
        <div>
          <p>步骤 1/3</p>
          <h1>选择朝代</h1>
        </div>
        <span className="title-rule" />
      </header>

      <section className="concept-setup-board" aria-label="开局设置">
        <div className="concept-phone-panel gilded-panel dynasty-selector-panel">
          <div className="ornate-heading">
            <span />
            <h2>选择朝代</h2>
            <span />
          </div>

          <div className="concept-dynasty-rail">
            {dynasties.map((dynasty) => {
              const visual = getDynastyVisual(dynasty);
              const isActive = dynasty.dynasty_id === selectedDynastyId;

                return (
                  <button
                    key={dynasty.dynasty_id}
                    type="button"
                    className={isActive ? 'concept-dynasty-card active' : 'concept-dynasty-card'}
                    style={conceptStyle({
                      '--dynasty-sheet': `url(${dynastyCardsSheet})`,
                      '--dynasty-position': visual.sheetPosition,
                      '--dynasty-accent': visual.accent,
                    })}
                    onClick={() => onSelectDynasty(dynasty.dynasty_id)}
                    disabled={busy}
                  >
                  <span className="dynasty-card-image" aria-hidden="true" />
                  <span className="dynasty-card-glow" aria-hidden="true" />
                  <span className="dynasty-card-era">{dynasty.enabled ? '历史语境待生成' : '后续时代预览'}</span>
                  <strong>{visual.shortName}</strong>
                  <small>{dynasty.enabled ? '可生成剧本' : '后续开放'}</small>
                  <em>{dynasty.enabled ? '正篇开放' : '预览'}</em>
                </button>
              );
            })}
          </div>
        </div>

        <aside className="concept-phone-panel gilded-panel keyword-scroll-panel" aria-label="关键词">
          <div className="selected-dynasty-emblem" style={{ '--dynasty-accent': displayVisual.accent } as CSSProperties}>
            <div>
              <p>朝代</p>
              <h2>{displayDynasty ? displayDynasty.name : '未选择朝代'}</h2>
            </div>
          </div>

          <p className="setup-teaser">先选择故事发生的时代。具体事件、人物关系、关键词与开局目标会在下一步生成。</p>

          <div className="keyword-token-row" aria-label="推荐关键词">
            {['时代制度', '地点氛围', '人物关系', '核心冲突'].map((keyword) => (
              <span key={keyword}>{keyword}</span>
            ))}
          </div>

          <label className="concept-textarea-shell">
            <span>输入故事关键词（可选）</span>
            <textarea
              value={keywordText}
              onChange={(event) => onKeywordTextChange(event.target.value)}
              placeholder={`可选：输入你想要的主题词。不填写则使用默认生成策略。`}
              disabled={busy}
              rows={4}
            />
          </label>

          {errorText ? <div className="error-banner cover-error">{errorText}</div> : null}

          <button type="button" className="imperial-button setup-generate-button" onClick={onPrepareScenario} disabled={busy}>
            <span>{busy ? '正在生成剧本...' : '下一步'}</span>
          </button>
        </aside>
      </section>
    </main>
  );
}
