import { visualAssetUrl } from '../api/client';
import { demoNotes } from '../mock/demoNotes';
import { getDynastyEntryMeta } from '../mock/entryFlow';
import type { Dynasty, HealthResponse } from '../types/game';

type StartPageProps = {
  health: HealthResponse | null;
  backendReady: boolean;
  dynasties: Dynasty[];
  selectedDynastyId: string;
  busy: boolean;
  errorText: string;
  onSelectDynasty: (dynastyId: string) => void;
  onRefreshBackend: () => void;
  onPrepareScenario: () => void;
};

export function StartPage({
  health,
  backendReady,
  dynasties,
  selectedDynastyId,
  busy,
  errorText,
  onSelectDynasty,
  onRefreshBackend,
  onPrepareScenario,
}: StartPageProps) {
  const selectedDynasty = dynasties.find((dynasty) => dynasty.dynasty_id === selectedDynastyId) ?? null;
  const selectedMeta = selectedDynasty ? getDynastyEntryMeta(selectedDynasty) : null;

  return (
    <main
      className="cover-page"
      style={{ backgroundImage: `linear-gradient(90deg, rgba(8, 7, 9, .82), rgba(8, 7, 9, .36)), url(${visualAssetUrl('scene_rain_alley')})` }}
    >
      <div className="cover-rain" />

      <section className="cover-copy">
        <p className="seal-kicker">朝代驱动 · 历史悬疑 · 事件生成</p>
        <h1>史隙</h1>
        <h2>选择一个朝代，生成属于你的历史事件。</h2>
        <p className="cover-text">
          你先决定时代，系统再从朝代知识库、事件语法库与人物关系模板中，生成本局的身份、事件、人物、线索与多结局分支。
        </p>

        <div className="cover-process-strip">
          <span className="process-pill active">1 选择朝代</span>
          <span className="process-pill">2 生成剧本</span>
          <span className="process-pill">3 进入剧情</span>
        </div>

        <article className="system-explain-card">
          <p className="meta-label">系统说明</p>
          <p>
            未选择朝代前，页面不会展示任何具体事件。只有在你确认时代后，系统才会生成对应的身份、事件骨架、关系网络与推理线索。
          </p>
          {!backendReady ? (
            <>
              <small>当前后端未连通，已切换为离线展示模式：你仍可选择朝代并预览剧本生成结果。</small>
              <div className="cover-inline-actions">
                <button type="button" className="secondary-button" onClick={onRefreshBackend} disabled={busy}>
                  {busy ? '正在检测引擎…' : '重新检测引擎'}
                </button>
              </div>
            </>
          ) : null}
        </article>

        <div className="cover-meta-row">
          <span>后端：{health?.display_text ?? '离线展示模式'}</span>
          <span>图片：后端代理与本地缓存</span>
          <span>入口：朝代选择后生成本局事件</span>
        </div>

        {errorText ? <div className="error-banner cover-error">{errorText}</div> : null}
      </section>

      <aside className="cover-selector">
        <div className="selector-block">
          <p className="meta-label">选择朝代</p>
          <div className="mini-card-list dynasty-card-list">
            {dynasties.map((dynasty) => {
              const meta = getDynastyEntryMeta(dynasty);
              const isActive = dynasty.dynasty_id === selectedDynastyId;

              return (
                <button
                  key={dynasty.dynasty_id}
                  type="button"
                  className={isActive ? 'mini-select-card dynasty-select-card active' : 'mini-select-card dynasty-select-card'}
                  onClick={() => onSelectDynasty(dynasty.dynasty_id)}
                  disabled={busy}
                >
                  <div className="dynasty-card-header">
                    <strong>{dynasty.name}</strong>
                    <span className={dynasty.enabled ? 'dynasty-status ready' : 'dynasty-status locked'}>
                      {dynasty.enabled ? '可生成' : '后续开放'}
                    </span>
                  </div>
                  <span>{meta.keywords.join('、')}</span>
                  <small>{meta.description}</small>
                </button>
              );
            })}
          </div>
        </div>

        <div className="selector-block selected-dynasty-panel">
          <p className="meta-label">当前选中</p>
          {selectedDynasty && selectedMeta ? (
            <>
              <h3>{selectedDynasty.name}</h3>
              <p className="selected-dynasty-copy">{selectedMeta.teaser}</p>
              <div className="selected-dynasty-tags">
                {selectedMeta.keywords.map((keyword) => (
                  <span key={keyword}>{keyword}</span>
                ))}
              </div>
              <button
                type="button"
                className="primary-button cover-button"
                onClick={onPrepareScenario}
                disabled={busy || !selectedDynasty.enabled}
              >
                {selectedDynasty.enabled ? (backendReady ? '生成本局剧本' : '生成离线剧本预览') : '该朝代后续开放'}
              </button>
            </>
          ) : (
            <p className="selected-dynasty-empty">先从右侧选择一个朝代，再进入本局事件生成流程。</p>
          )}
        </div>

        <div className="selector-block demo-boundary">
          <p className="meta-label">当前演示边界</p>
          <ul>
            {demoNotes.map((note) => (
              <li key={note}>{note}</li>
            ))}
          </ul>
        </div>
      </aside>
    </main>
  );
}
