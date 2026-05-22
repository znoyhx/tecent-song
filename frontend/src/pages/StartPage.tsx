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

const dynastyLabels: Record<string, { mark: string; route: string; hint: string }> = {
  ming: { mark: '明', route: '固定 Demo', hint: '直接进入书坊焚稿案。' },
  song: { mark: '宋', route: 'AI 生成', hint: '填写关键词后生成北宋剧本。' },
  tang: { mark: '唐', route: 'AI 生成', hint: '填写关键词后生成晚唐剧本。' },
  late_tang: { mark: '唐', route: 'AI 生成', hint: '填写关键词后生成晚唐剧本。' },
};

export function StartPage({
  mode,
  dynasties,
  selectedDynastyId,
  busy,
  errorText,
  onStart,
  onSelectDynasty,
  onPrepareScenario,
}: StartPageProps) {
  if (mode === 'home') {
    return (
      <main className="entry-page stage15-home">
        <section className="stage15-hero">
          <p>史隙</p>
          <h1>历史悬疑剧本游戏</h1>
          <span>明代固定 Demo 稳定可玩；北宋与晚唐进入真实 AI 剧本生成。</span>
          <button type="button" className="imperial-button" onClick={onStart}>
            <span>开始游戏</span>
          </button>
        </section>
      </main>
    );
  }

  return (
    <main className="entry-page stage15-setup">
      <section className="stage15-panel">
        <header>
          <p>步骤 1/4</p>
          <h1>选择朝代入口</h1>
          <span>明代直达固定 Demo；北宋与晚唐需要先填写关键词。</span>
        </header>

        <div className="stage15-dynasty-grid">
          {dynasties.map((dynasty) => {
            const meta = dynastyLabels[dynasty.dynasty_id] ?? { mark: dynasty.name.slice(0, 1), route: '入口', hint: dynasty.core_mood };
            const active = selectedDynastyId === dynasty.dynasty_id;
            return (
              <button
                key={dynasty.dynasty_id}
                type="button"
                className={active ? 'stage15-dynasty-card active' : 'stage15-dynasty-card'}
                onClick={() => onSelectDynasty(dynasty.dynasty_id)}
                disabled={busy}
              >
                <strong>{meta.mark}</strong>
                <span>{dynasty.name}</span>
                <em>{meta.route}</em>
                <small>{meta.hint}</small>
              </button>
            );
          })}
        </div>

        {errorText ? <div className="error-banner cover-error">{errorText}</div> : null}

        <div className="stage15-actions">
          <button type="button" className="imperial-button" onClick={onPrepareScenario} disabled={busy}>
            <span>{busy ? '处理中...' : '继续'}</span>
          </button>
        </div>
      </section>
    </main>
  );
}
