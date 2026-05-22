import { useEffect, useMemo, useState } from 'react';

import type { Dynasty, PlayableIdentity, ScriptJob, ScriptPackage } from '../../types/game';

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
  onStart: (identityId: string) => void;
};

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
    <main className="entry-page stage15-keyword">
      <section className="stage15-panel narrow">
        <header>
          <p>步骤 2/4</p>
          <h1>{dynasty.name}剧本关键词</h1>
          <span>填写 1-8 个关键词，后端会据此创建真实生成任务。</span>
        </header>

        <label className="stage15-keyword-box">
          <span>关键词</span>
          <textarea
            value={keywordText}
            onChange={(event) => onKeywordTextChange(event.target.value)}
            placeholder="例如：驿站、军报、雨夜、粮草"
            rows={5}
            disabled={busy}
          />
          <small>可用逗号、顿号或换行分隔。请避免“好玩”“刺激”这类过空泛词。</small>
        </label>

        {errorText ? <div className="error-banner cover-error">{errorText}</div> : null}

        <div className="stage15-actions">
          <button type="button" className="secondary-button" onClick={onBack} disabled={busy}>返回</button>
          <button type="button" className="imperial-button" onClick={onGenerate} disabled={busy}>
            <span>{busy ? '提交中...' : '开始生成'}</span>
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
    const timer = window.setInterval(() => setQuoteIndex((current) => (current + 1) % quotes.length), 5000);
    return () => window.clearInterval(timer);
  }, [quotes.length]);

  const failed = job.status === 'failed' || job.status === 'visual_blocked';
  const canOpenOverview = job.status === 'completed' && job.ready_for_overview && job.script_id;
  const quote = quotes[quoteIndex] ?? quotes[0];

  return (
    <main className="entry-page stage15-progress">
      <section className="stage15-panel wide">
        <header>
          <p>步骤 3/4</p>
          <h1>剧本生成流程</h1>
          <span>流程图只读取后端 job 状态，不在前端自增进度。</span>
        </header>

        <div className="stage15-progress-head">
          <strong>{statusText[job.status] ?? job.status}</strong>
          <span>{job.progress}%</span>
          <i style={{ width: `${job.progress}%` }} />
        </div>

        <div className="stage15-step-list">
          {job.steps.map((step) => (
            <article key={step.step_id} className={`stage15-step ${step.status}`}>
              <span>{statusText[step.status] ?? step.status}</span>
              <div>
                <strong>{step.title}</strong>
                <p>{step.message || step.description}</p>
                {step.attempts > 1 ? <em>已尝试 {step.attempts} 次</em> : null}
              </div>
            </article>
          ))}
        </div>

        {quote ? (
          <blockquote className="stage15-quote">
            <p>{quote.text}</p>
            <footer>{quote.author}</footer>
          </blockquote>
        ) : null}

        {job.blocking_issues.length > 0 ? (
          <div className="stage15-issues">
            {job.blocking_issues.map((issue, index) => (
              <p key={`${issue.code ?? 'issue'}-${index}`}>{String(issue.message ?? issue.code ?? '生成受阻')}</p>
            ))}
          </div>
        ) : null}
        {errorText ? <div className="error-banner cover-error">{errorText}</div> : null}

        <div className="stage15-actions">
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
  const [selectedIdentityId, setSelectedIdentityId] = useState(script.playable_identities[0]?.identity_id ?? '');
  const approvedHero = script.visual_assets.find((asset) => asset.asset_type === 'scene' && asset.quality_gate.status === 'approved');

  const rankText: Record<PlayableIdentity['social_rank'], string> = {
    low: '低身份',
    middle: '中身份',
    high: '高身份',
  };

  return (
    <main className="entry-page stage15-overview">
      <section className="stage15-panel wide">
        <header>
          <p>步骤 4/4</p>
          <h1>{script.script_overview.title}</h1>
          <span>{script.script_overview.logline}</span>
        </header>

        <div className="stage15-overview-grid">
          <article className="stage15-overview-card">
            {approvedHero?.url ? <img src={approvedHero.url} alt="生成剧本主场景" /> : null}
            <h2>案件概览</h2>
            <p>{script.script_overview.case_summary}</p>
            <dl>
              <dt>开场地点</dt>
              <dd>{script.script_overview.opening_location}</dd>
              <dt>调查目标</dt>
              <dd>{script.script_overview.public_objective}</dd>
              <dt>关键词</dt>
              <dd>{script.keywords.join('、')}</dd>
            </dl>
          </article>

          <section className="stage15-identities">
            <h2>选择身份</h2>
            {script.playable_identities.map((identity) => (
              <button
                key={identity.identity_id}
                type="button"
                className={selectedIdentityId === identity.identity_id ? 'stage15-identity-card active' : 'stage15-identity-card'}
                onClick={() => setSelectedIdentityId(identity.identity_id)}
                disabled={busy}
              >
                <strong>{identity.display_name}</strong>
                <span>{rankText[identity.social_rank]}</span>
                <p>{identity.description}</p>
                <em>{identity.motive}</em>
              </button>
            ))}
          </section>
        </div>

        {job.status !== 'completed' || !job.ready_for_overview ? (
          <div className="stage15-issues"><p>后端 job 尚未完成，不能进入正式游玩。</p></div>
        ) : null}
        {errorText ? <div className="error-banner cover-error">{errorText}</div> : null}

        <div className="stage15-actions">
          <button type="button" className="secondary-button" onClick={onBack} disabled={busy}>返回流程</button>
          <button
            type="button"
            className="imperial-button"
            onClick={() => onStart(selectedIdentityId)}
            disabled={busy || !selectedIdentityId || job.status !== 'completed' || !job.ready_for_overview}
          >
            <span>{busy ? '进入中...' : '进入生成剧本'}</span>
          </button>
        </div>
      </section>
    </main>
  );
}
