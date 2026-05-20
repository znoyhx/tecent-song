import { visualAssetUrl } from '../api/client';
import { defaultScenarioKeywordText, getDynastyEntryMeta } from '../mock/entryFlow';
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
      <main
        className="entry-page entry-home-page"
        style={{ backgroundImage: `linear-gradient(90deg, rgba(7, 8, 10, .72), rgba(7, 8, 10, .34)), url(${visualAssetUrl('scene_rain_alley')})` }}
      >
        <div className="cover-rain" />
        <section className="entry-home-lockup" aria-label="史隙首页">
          <p className="seal-kicker">史隙</p>
          <h1>史隙</h1>
          <button type="button" className="primary-button entry-start-button" onClick={onStart}>
            开始游戏
          </button>
        </section>
      </main>
    );
  }

  const selectedDynasty = dynasties.find((dynasty) => dynasty.dynasty_id === selectedDynastyId) ?? null;

  return (
    <main
      className="entry-page entry-setup-page"
      style={{ backgroundImage: `linear-gradient(90deg, rgba(7, 8, 10, .84), rgba(7, 8, 10, .52)), url(${visualAssetUrl('scene_bookshop_front_hall')})` }}
    >
      <div className="cover-rain" />

      <section className="entry-setup-shell" aria-label="开局设置">
        <div className="entry-setup-heading">
          <p className="seal-kicker">开局设置</p>
          <h1>选择朝代</h1>
        </div>

        <div className="entry-setup-grid">
          <section className="entry-dynasty-panel" aria-label="朝代选择">
            <div className="dynasty-card-list entry-dynasty-list">
              {dynasties.map((dynasty) => {
                const meta = getDynastyEntryMeta(dynasty);
                const isActive = dynasty.dynasty_id === selectedDynastyId;

                return (
                  <button
                    key={dynasty.dynasty_id}
                    type="button"
                    className={isActive ? 'entry-dynasty-card active' : 'entry-dynasty-card'}
                    onClick={() => onSelectDynasty(dynasty.dynasty_id)}
                    disabled={busy}
                  >
                    <span>{dynasty.period_label}</span>
                    <strong>{dynasty.name}</strong>
                    <small>{meta.eventName}</small>
                  </button>
                );
              })}
            </div>
          </section>

          <section className="entry-keyword-panel" aria-label="关键词">
            <div>
              <p className="meta-label">关键词</p>
              <h2>{selectedDynasty ? selectedDynasty.name : '未选择朝代'}</h2>
            </div>

            <label className="keyword-input-shell">
              <span>输入关键词</span>
              <textarea
                value={keywordText}
                onChange={(event) => onKeywordTextChange(event.target.value)}
                placeholder="例如：雨夜、书坊、失火、封口令"
                disabled={busy}
                rows={4}
              />
            </label>

            <p className="keyword-default-hint">
              不填写关键词将使用默认关键词：{defaultScenarioKeywordText}
            </p>

            {errorText ? <div className="error-banner cover-error">{errorText}</div> : null}

            <button type="button" className="primary-button setup-generate-button" onClick={onPrepareScenario} disabled={busy}>
              {busy ? '正在生成剧本…' : '生成剧本'}
            </button>
          </section>
        </div>
      </section>
    </main>
  );
}
