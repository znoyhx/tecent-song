import type { CSSProperties } from 'react';
import { useEffect, useMemo, useState } from 'react';

import { api, resolveApiUrl } from '../../api/client';
import type {
  Dynasty,
  PlayableIdentity,
  PlayerIdentityOption,
  PlayerIdentityRecommendations,
  PlayerIdentityValidationResult,
  ScriptJob,
  ScriptJobStepStatus,
  ScriptPackage,
  VisualAsset,
} from '../../types/game';

type KeywordPageProps = {
  dynasty: Dynasty;
  keywordText: string;
  busy: boolean;
  errorText: string;
  onKeywordTextChange: (value: string) => void;
  onBack: () => void;
  onGenerate: () => void;
};

type ProgressPageProps = {
  job: ScriptJob;
  errorText: string;
  onBack: () => void;
  onOpenOverview: () => void;
};

type OverviewPageProps = {
  job: ScriptJob;
  script: ScriptPackage;
  busy: boolean;
  errorText: string;
  onBack: () => void;
  onStart: (identityPayload: { identity_id?: string; custom_identity_text?: string }) => void;
};

type FixedDemoOverviewPageProps = {
  identities: PlayerIdentityRecommendations;
  busy: boolean;
  errorText: string;
  onBack: () => void;
  onStart: (identityPayload: { identity_id?: string; custom_identity_text?: string }) => void;
};

type RichScriptPackage = ScriptPackage & {
  world?: { dynasty_name?: string; era_name?: string; year_hint?: string; location_region?: string };
  locations?: Array<{ location_id: string; name: string }>;
  npcs?: Array<{ npc_id: string; name: string; public_identity: string }>;
  clues?: Array<{ clue_id: string; title: string }>;
  endings?: Array<{ ending_id: string; title: string }>;
};

const entryBackground = '/generated-ui/concept-entry-bg.png';
const identityPortraitSheet = '/generated-ui/identity-portraits-sheet.png';

const statusText: Record<string, string> = {
  pending: '等待',
  running: '进行中',
  passed: '通过',
  failed: '失败',
  blocked: '阻塞',
  retrying: '重试中',
  queued: '排队中',
  completed: '已完成',
  visual_blocked: '图片阻塞',
};

const identityPositions = [
  { x: '0%', y: '0%' },
  { x: '50%', y: '0%' },
  { x: '100%', y: '0%' },
  { x: '0%', y: '100%' },
  { x: '50%', y: '100%' },
  { x: '100%', y: '100%' },
];

function conceptStyle(extra?: Record<string, string>): CSSProperties {
  return {
    '--concept-bg': `url(${entryBackground})`,
    ...extra,
  } as CSSProperties;
}

function identityStyle(index: number): CSSProperties {
  const position = identityPositions[index % identityPositions.length] ?? identityPositions[0];
  return {
    '--identity-sheet': `url(${identityPortraitSheet})`,
    '--identity-position': `${position.x} ${position.y}`,
  } as CSSProperties;
}

function assetUrl(asset?: VisualAsset | null): string {
  return resolveApiUrl(asset?.url ?? null);
}

function stepClass(status: ScriptJobStepStatus): 'done' | 'active' | 'failed' | 'pending' {
  if (status === 'passed') {
    return 'done';
  }
  if (status === 'running' || status === 'retrying') {
    return 'active';
  }
  if (status === 'failed' || status === 'blocked') {
    return 'failed';
  }
  return 'pending';
}

function visualApprovedCount(assets: VisualAsset[], type: VisualAsset['asset_type']): number {
  return assets.filter((asset) => asset.asset_type === type && asset.quality_gate.status === 'approved').length;
}

function defaultIdentityId(identities: PlayerIdentityRecommendations): string {
  return identities.default_identity || identities.options[0]?.identity_id || '';
}

function identityRankText(rank: PlayerIdentityOption['social_rank'] | PlayableIdentity['social_rank']): string {
  return rank === 'high' ? '高身份' : rank === 'middle' ? '中身份' : '低身份';
}

export function ScriptKeywordPage({
  dynasty,
  keywordText,
  busy,
  errorText,
  onKeywordTextChange,
  onBack,
  onGenerate,
}: KeywordPageProps) {
  return (
    <main className="concept-entry-page concept-loading-page" style={conceptStyle()}>
      <div className="concept-atmosphere" />
      <section className="concept-generation-modal gilded-panel">
        <p className="concept-step-label">步骤 1/3</p>
        <h1>{dynasty.name}剧本关键词</h1>
        <label className="concept-textarea-shell keyword-page-textarea">
          <span>填写 1-8 个关键词</span>
          <textarea
            value={keywordText}
            onChange={(event) => onKeywordTextChange(event.target.value)}
            placeholder="例如：驿站、军报、雨夜、粮草"
            rows={5}
            disabled={busy}
          />
        </label>
        {errorText ? <div className="error-banner cover-error">{errorText}</div> : null}
        <div className="stage15-actions concept-keyword-actions">
          <button type="button" className="secondary-button" onClick={onBack} disabled={busy}>返回</button>
          <button type="button" className="imperial-button" onClick={onGenerate} disabled={busy}>
            <span>{busy ? '提交中...' : '开始生成'}</span>
          </button>
        </div>
      </section>
    </main>
  );
}

export function FixedDemoOverviewPage({ identities, busy, errorText, onBack, onStart }: FixedDemoOverviewPageProps) {
  const [selectedIdentityId, setSelectedIdentityId] = useState(defaultIdentityId(identities));
  const [customIdentityText, setCustomIdentityText] = useState('');
  const [identityValidation, setIdentityValidation] = useState<PlayerIdentityValidationResult | null>(null);
  const [identityError, setIdentityError] = useState('');
  const [identityBusy, setIdentityBusy] = useState(false);
  const selectedIdentity = identities.options.find((identity) => identity.identity_id === selectedIdentityId) ?? identities.options[0] ?? null;
  const customTrimmed = customIdentityText.trim();
  const customMode = customTrimmed.length > 0;
  const customIdentityValid = customMode && identityValidation?.is_valid && identityValidation.identity?.display_name === customTrimmed;
  const activeIdentityName = customMode ? customTrimmed : selectedIdentity?.display_name ?? '待选择';
  const activeIdentityBackground = customMode
    ? customIdentityValid && identityValidation?.identity
      ? identityValidation.identity.background
      : '将以你填写的身份进入剧本；后端会在开局时再次校验时代与剧情边界。'
    : selectedIdentity?.background ?? '以明代书坊相关身份进入固定 Demo。';
  const activeIdentityNote = customMode
    ? customIdentityValid
      ? '身份校验通过。'
      : '自定义身份未校验或未通过时，开始游戏会交由后端最终校验。'
    : selectedIdentity?.attitude_hint ?? '';
  const summaryPairs = [
    ['时代背景', '明代 · 书坊焚稿案'],
    ['开场地点', '书坊前厅'],
    ['调查目标', '查明火场异状，判断旧稿与封口令之间的关系'],
    ['主要人物', '书坊掌柜徐、刻工阿申、落第书生顾文、低阶锦衣卫陆正'],
    ['身份来源', '后端 /api/player-identities'],
    ['剧本路线', '固定路演 Demo'],
  ];

  useEffect(() => {
    setSelectedIdentityId(defaultIdentityId(identities));
    setCustomIdentityText('');
    setIdentityValidation(null);
    setIdentityError('');
  }, [identities]);

  const handleValidateIdentity = async () => {
    if (!customTrimmed) {
      setIdentityError('请先输入你的自定义身份。');
      setIdentityValidation(null);
      return;
    }
    setIdentityBusy(true);
    setIdentityError('');
    try {
      const result = await api.validatePlayerIdentity({
        dynasty_id: 'ming',
        event_id: 'ming_bookshop_fire',
        custom_identity_text: customTrimmed,
      });
      setIdentityValidation(result);
      if (!result.is_valid) {
        setIdentityError(result.rejection_reason || '这个身份暂时不适合当前剧本。');
      }
    } catch (error) {
      setIdentityValidation(null);
      setIdentityError(error instanceof Error ? error.message : '身份校验失败，请稍后重试。');
    } finally {
      setIdentityBusy(false);
    }
  };

  const handleStart = () => {
    if (customMode) {
      onStart({ custom_identity_text: customTrimmed });
      return;
    }
    onStart({ identity_id: selectedIdentityId });
  };

  return (
    <main className="script-overview-page concept-entry-page concept-overview-page" style={conceptStyle()}>
      <div className="concept-atmosphere" />

      <section className="concept-overview-board fixed-demo-overview gilded-panel" aria-label="明代身份选择与剧本概览">
        <header className="concept-overview-header">
          <button type="button" className="secondary-button concept-back-button" onClick={onBack} disabled={busy}>
            返回朝代
          </button>
          <div className="ornate-heading">
            <span />
            <p>步骤 3/3</p>
            <span />
          </div>
          <h1>书坊焚稿案</h1>
        </header>

        <div className="concept-overview-layout">
          <section className="concept-identity-column" aria-label="身份选择">
            <div className="ornate-heading mini">
              <span />
              <h2>身份选择</h2>
              <span />
            </div>

            <div className="concept-identity-grid fixed-demo-identity-grid">
              {identities.options.map((identity, index) => {
                const active = !customMode && identity.identity_id === selectedIdentityId;
                return (
                  <button
                    key={identity.identity_id}
                    type="button"
                    className={active ? 'concept-identity-card active' : 'concept-identity-card'}
                    style={identityStyle(index)}
                    onClick={() => {
                      setSelectedIdentityId(identity.identity_id);
                      setCustomIdentityText('');
                      setIdentityValidation(null);
                      setIdentityError('');
                    }}
                    disabled={busy || identityBusy}
                  >
                    <span className="identity-check" aria-hidden="true">✓</span>
                    <strong>{identity.display_name}</strong>
                    <small>{identity.description}</small>
                    <em>{identityRankText(identity.social_rank)}</em>
                  </button>
                );
              })}
            </div>

            <div className="concept-custom-identity">
              <input
                value={customIdentityText}
                onChange={(event) => {
                  setCustomIdentityText(event.target.value);
                  setIdentityValidation(null);
                  setIdentityError('');
                }}
                placeholder="输入自定义身份，例如：游方医者"
                disabled={busy || identityBusy}
              />
              <button type="button" className="secondary-button" onClick={handleValidateIdentity} disabled={busy || identityBusy}>
                {identityBusy ? '校验中...' : '校验'}
              </button>
            </div>
            {customMode && customIdentityValid ? <p className="identity-valid-hint">身份校验通过。</p> : null}
            {identityError ? <div className="identity-error">{identityError}</div> : null}
          </section>

          <aside className="concept-brief-column" aria-label="剧本概览">
            <div className="ornate-heading mini">
              <span />
              <h2>剧本概览</h2>
              <span />
            </div>

            <article className="brief-scroll">
              <section className="brief-section">
                <h3>事件背景</h3>
                <p>雨夜之后，书坊一角焦黑，旧书箱、红封纸角与门柱旁的窥探痕迹互相牵连。你需要在掌柜、刻工、落第书生与锦衣卫的说辞之间寻找破绽。</p>
              </section>

              <section className="brief-section">
                <h3>核心人物</h3>
                <div className="core-cast-row">
                  {['徐掌柜', '阿申', '顾文', '陆正'].map((name, index) => (
                    <span key={name} className="core-avatar generated" style={identityStyle(index)} title={name} />
                  ))}
                </div>
              </section>

              <section className="brief-section">
                <h3>调查目标</h3>
                <p>确认火灾是否为意外，找出旧稿被烧、封口压力与各人隐瞒之间的因果链。</p>
              </section>

              <section className="brief-section identity-background-preview concept-background-preview">
                <span>当前身份</span>
                <h3>{activeIdentityName}</h3>
                <p>{activeIdentityBackground}</p>
                {activeIdentityNote ? <p className="identity-motive">{customMode ? activeIdentityNote : `立场：${activeIdentityNote}`}</p> : null}
              </section>

              <div className="concept-summary-grid">
                {summaryPairs.map(([label, value]) => (
                  <article key={label} className="generation-stat-card">
                    <span>{label}</span>
                    <strong>{value}</strong>
                  </article>
                ))}
              </div>
            </article>
          </aside>
        </div>

        {errorText ? <div className="error-banner cover-error">{errorText}</div> : null}

        <div className="script-overview-actions concept-overview-actions">
          <button type="button" className="secondary-button" onClick={onBack} disabled={busy}>返回朝代</button>
          <button
            type="button"
            className="imperial-button"
            onClick={handleStart}
            disabled={busy || identityBusy || (!customMode && !selectedIdentityId)}
          >
            <span>{busy ? '进入中...' : '开始游戏'}</span>
          </button>
        </div>
      </section>
    </main>
  );
}

export function ScriptProgressPage({ job, errorText, onBack, onOpenOverview }: ProgressPageProps) {
  const [quoteIndex, setQuoteIndex] = useState(0);
  const quotes = useMemo(() => {
    const current = job.transitional_quote;
    return [
      current,
      { text: '纸上得来终觉浅，绝知此事要躬行。', author: '陆游' },
      { text: '试玉要烧三日满，辨材须待七年期。', author: '白居易' },
    ].filter(Boolean) as Array<{ text: string; author: string }>;
  }, [job.transitional_quote]);

  useEffect(() => {
    if (quotes.length <= 1) {
      return undefined;
    }
    const timer = window.setInterval(() => setQuoteIndex((current) => (current + 1) % quotes.length), 5000);
    return () => window.clearInterval(timer);
  }, [quotes.length]);

  const failed = job.status === 'failed' || job.status === 'visual_blocked';
  const canOpenOverview = job.status === 'completed' && job.ready_for_overview && job.script_id;
  const quote = quotes[quoteIndex] ?? quotes[0];
  const progressDeg = `${Math.round(Math.max(0, Math.min(100, job.progress)) * 3.6)}deg`;

  return (
    <main className="script-loading-stage concept-entry-page concept-loading-page" style={conceptStyle()}>
      <div className="concept-atmosphere" />

      <section className="concept-generation-modal gilded-panel" aria-live="polite">
        <button type="button" className="modal-close" aria-label="返回入口" onClick={onBack}>×</button>
        <p className="concept-step-label">步骤 2/3</p>
        <h1>剧本生成中</h1>

        <div className="progress-orb" style={{ '--progress-deg': progressDeg } as CSSProperties} aria-label={`生成进度 ${job.progress}%`}>
          <div className="progress-orb-scene" />
          <strong>{job.progress}%</strong>
        </div>

        <div className="generation-step-list script-step-list concept-progress-list">
          {job.steps.map((step) => (
            <article key={step.step_id} className={`generation-step ${stepClass(step.status)}`}>
              <span className="generation-step-dot" />
              <div>
                <strong>{step.title}</strong>
                <p>{step.message || step.description}</p>
                <em>{statusText[step.status] ?? step.status}{step.attempts > 1 ? ` · 第 ${step.attempts} 次` : ''}</em>
              </div>
            </article>
          ))}
        </div>

        <div className="concept-visual-quality" aria-label="图片门禁">
          <span>场景 {job.visual_quality.scene.approved ?? 0}/{job.visual_quality.scene.required ?? 0}</span>
          <span>人物 {job.visual_quality.npc.approved ?? 0}/{job.visual_quality.npc.required ?? 0}</span>
          <span>线索 {job.visual_quality.clue.approved ?? 0}/{job.visual_quality.clue.required ?? 0}</span>
        </div>

        {quote ? (
          <blockquote className="stage15-quote concept-quote">
            <p>{quote.text}</p>
            <footer>{quote.author}</footer>
          </blockquote>
        ) : null}

        {job.blocking_issues.length > 0 ? (
          <div className="stage15-issues concept-issues">
            {job.blocking_issues.map((issue, index) => (
              <p key={`${issue.code ?? 'issue'}-${index}`}>{String(issue.message ?? issue.code ?? '生成受阻')}</p>
            ))}
          </div>
        ) : null}
        {errorText ? <div className="error-banner cover-error">{errorText}</div> : null}

        <div className="stage15-actions concept-progress-actions">
          <button type="button" className="secondary-button" onClick={onBack}>返回入口</button>
          <button type="button" className="imperial-button" onClick={onOpenOverview} disabled={!canOpenOverview}>
            <span>{failed ? '生成未通过' : canOpenOverview ? '查看剧本概览' : '等待后端完成'}</span>
          </button>
        </div>
      </section>
    </main>
  );
}

export function ScriptOverviewPage({ job, script, busy, errorText, onBack, onStart }: OverviewPageProps) {
  const [selectedIdentityId, setSelectedIdentityId] = useState(
    script.playable_identities.find((identity) => identity.is_default)?.identity_id ?? script.playable_identities[0]?.identity_id ?? '',
  );
  const [customIdentityText, setCustomIdentityText] = useState('');
  const [identityValidation, setIdentityValidation] = useState<PlayerIdentityValidationResult | null>(null);
  const [identityError, setIdentityError] = useState('');
  const [identityBusy, setIdentityBusy] = useState(false);
  const richScript = script as RichScriptPackage;
  const approvedHero = script.visual_assets.find((asset) => asset.asset_type === 'scene' && asset.quality_gate.status === 'approved');
  const npcAssets = script.visual_assets.filter((asset) => asset.asset_type === 'npc' && asset.quality_gate.status === 'approved');
  const selectedIdentity = script.playable_identities.find((identity) => identity.identity_id === selectedIdentityId) ?? script.playable_identities[0] ?? null;
  const customTrimmed = customIdentityText.trim();
  const customMode = customTrimmed.length > 0;
  const customIdentityValid = customMode && identityValidation?.is_valid && identityValidation.identity?.display_name === customTrimmed;
  const activeIdentityName = customMode ? customTrimmed : selectedIdentity?.display_name ?? '待选择';
  const activeIdentityBackground = customMode
    ? customIdentityValid && identityValidation?.identity
      ? identityValidation.identity.background
      : '将以你填写的身份进入生成剧本；后端会在开局时校验时代、权限与剧情边界。'
    : selectedIdentity?.background ?? script.script_overview.player_briefing;
  const activeIdentityNote = customMode
    ? customIdentityValid
      ? '身份校验通过。'
      : '自定义身份未校验或未通过时，开始游戏会交由后端最终校验。'
    : selectedIdentity?.motive ?? '';

  useEffect(() => {
    setSelectedIdentityId(script.playable_identities.find((identity) => identity.is_default)?.identity_id ?? script.playable_identities[0]?.identity_id ?? '');
    setCustomIdentityText('');
    setIdentityValidation(null);
    setIdentityError('');
  }, [script.script_id, script.playable_identities]);

  const handleValidateIdentity = async () => {
    if (!customTrimmed) {
      setIdentityError('请先输入你的自定义身份。');
      setIdentityValidation(null);
      return;
    }
    setIdentityBusy(true);
    setIdentityError('');
    try {
      const result = await api.validateGeneratedIdentity(script.script_id, {
        identity_id: selectedIdentityId,
        custom_identity_text: customTrimmed,
      });
      setIdentityValidation(result);
      if (!result.is_valid) {
        setIdentityError(result.rejection_reason || '这个身份暂时不适合当前生成剧本。');
      }
    } catch (error) {
      setIdentityValidation(null);
      setIdentityError(error instanceof Error ? error.message : '身份校验失败，请稍后重试。');
    } finally {
      setIdentityBusy(false);
    }
  };

  const handleStart = () => {
    if (customMode) {
      onStart({ identity_id: selectedIdentityId, custom_identity_text: customTrimmed });
      return;
    }
    onStart({ identity_id: selectedIdentityId });
  };

  const cast = richScript.npcs?.length
    ? richScript.npcs.slice(0, 4).map((npc) => ({ id: npc.npc_id, name: npc.name }))
    : script.script_overview.major_npcs.slice(0, 4).map((name) => ({ id: name, name }));

  const summaryPairs = [
    ['时代背景', [richScript.world?.dynasty_name, richScript.world?.era_name, richScript.world?.year_hint].filter(Boolean).join(' · ') || script.dynasty_id],
    ['开场地点', script.script_overview.opening_location],
    ['关键词', script.keywords.join('、')],
    ['地点数量', `${richScript.locations?.length ?? script.script_overview.major_locations.length} 处`],
    ['核心人物', `${richScript.npcs?.length ?? script.script_overview.major_npcs.length} 人`],
    ['关键线索', `${richScript.clues?.length ?? visualApprovedCount(script.visual_assets, 'clue')} 条`],
    ['结局数量', `${richScript.endings?.length ?? 0} 个`],
    ['图片门禁', `场景 ${visualApprovedCount(script.visual_assets, 'scene')} / 人物 ${visualApprovedCount(script.visual_assets, 'npc')} / 线索 ${visualApprovedCount(script.visual_assets, 'clue')}`],
  ];

  return (
    <main className="script-overview-page concept-entry-page concept-overview-page" style={conceptStyle()}>
      <div className="concept-atmosphere" />

      <section className="concept-overview-board gilded-panel" aria-label="身份选择与剧本概览">
        <header className="concept-overview-header">
          <button type="button" className="secondary-button concept-back-button" onClick={onBack} disabled={busy}>
            返回流程
          </button>
          <div className="ornate-heading">
            <span />
            <p>步骤 3/3</p>
            <span />
          </div>
          <h1>{script.script_overview.title}</h1>
        </header>

        <div className="concept-overview-layout">
          <section className="concept-identity-column" aria-label="身份选择">
            <div className="ornate-heading mini">
              <span />
              <h2>身份选择</h2>
              <span />
            </div>

            <div className="concept-identity-grid">
              {script.playable_identities.map((identity, index) => {
                const active = !customMode && identity.identity_id === selectedIdentityId;
                return (
                  <button
                    key={identity.identity_id}
                    type="button"
                    className={active ? 'concept-identity-card active' : 'concept-identity-card'}
                    style={identityStyle(index)}
                    onClick={() => {
                      setSelectedIdentityId(identity.identity_id);
                      setCustomIdentityText('');
                      setIdentityValidation(null);
                      setIdentityError('');
                    }}
                    disabled={busy || identityBusy}
                  >
                    <span className="identity-check" aria-hidden="true">✓</span>
                    <strong>{identity.display_name}</strong>
                    <small>{identity.description}</small>
                    <em>{identityRankText(identity.social_rank)}</em>
                  </button>
                );
              })}
            </div>

            <div className="concept-custom-identity">
              <input
                value={customIdentityText}
                onChange={(event) => {
                  setCustomIdentityText(event.target.value);
                  setIdentityValidation(null);
                  setIdentityError('');
                }}
                placeholder="输入自定义身份，例如：游方医者"
                disabled={busy || identityBusy}
              />
              <button type="button" className="secondary-button" onClick={handleValidateIdentity} disabled={busy || identityBusy}>
                {identityBusy ? '校验中...' : '校验'}
              </button>
            </div>
            {customMode && customIdentityValid ? <p className="identity-valid-hint">身份校验通过。</p> : null}
            {identityError ? <div className="identity-error">{identityError}</div> : null}
          </section>

          <aside className="concept-brief-column" aria-label="剧本概览">
            <div className="ornate-heading mini">
              <span />
              <h2>剧本概览</h2>
              <span />
            </div>

            <article className="brief-scroll">
              {assetUrl(approvedHero) ? (
                <img className="concept-hero-preview" src={assetUrl(approvedHero)} alt="生成剧本主场景" />
              ) : null}

              <section className="brief-section">
                <h3>事件背景</h3>
                <p>{script.script_overview.case_summary}</p>
              </section>

              <section className="brief-section">
                <h3>核心人物</h3>
                <div className="core-cast-row">
                  {cast.map((member, index) => {
                    const url = assetUrl(npcAssets[index]);
                    return url ? (
                      <span key={member.id} className="core-avatar" title={member.name}>
                        <img src={url} alt={member.name} />
                      </span>
                    ) : (
                      <span key={member.id} className="core-avatar generated" style={identityStyle(index)} title={member.name} />
                    );
                  })}
                  {cast.length < (richScript.npcs?.length ?? script.script_overview.major_npcs.length) ? <span className="core-avatar more">...</span> : null}
                </div>
              </section>

              <section className="brief-section">
                <h3>调查目标</h3>
                <p>{script.script_overview.public_objective}</p>
              </section>

              <section className="brief-section identity-background-preview concept-background-preview">
                <span>当前身份</span>
                <h3>{activeIdentityName}</h3>
                <p>{activeIdentityBackground}</p>
                {activeIdentityNote ? <p className="identity-motive">{customMode ? activeIdentityNote : `动机：${activeIdentityNote}`}</p> : null}
              </section>

              <div className="concept-summary-grid">
                {summaryPairs.map(([label, value]) => (
                  <article key={label} className="generation-stat-card">
                    <span>{label}</span>
                    <strong>{value}</strong>
                  </article>
                ))}
              </div>
            </article>
          </aside>
        </div>

        {job.status !== 'completed' || !job.ready_for_overview ? (
          <div className="stage15-issues concept-issues"><p>后端 job 尚未完成，不能进入正式游玩。</p></div>
        ) : null}
        {errorText ? <div className="error-banner cover-error">{errorText}</div> : null}

        <div className="script-overview-actions concept-overview-actions">
          <button type="button" className="secondary-button" onClick={onBack} disabled={busy}>返回流程</button>
          <button
            type="button"
            className="imperial-button"
            onClick={handleStart}
            disabled={busy || identityBusy || (!customMode && !selectedIdentityId) || job.status !== 'completed' || !job.ready_for_overview}
          >
            <span>{busy ? '进入中...' : '开始游戏'}</span>
          </button>
        </div>
      </section>
    </main>
  );
}
