import { resolveApiUrl, visualAssetUrl } from '../../api/client';
import type { EndingResult } from '../../types/game';

type EndingPanelProps = {
  ending: EndingResult;
  endingCatalog: Array<{ ending_id: string; title: string }>;
  onRestart: () => void;
};

const npcNameMap: Record<string, string> = {
  npc_owner: '许掌柜',
  npc_worker: '阿沈',
  npc_scholar: '顾闻',
  npc_jinyiwei: '陆峥',
};

export function EndingPanel({ ending, endingCatalog, onRestart }: EndingPanelProps) {
  const backdrop = resolveApiUrl(ending.visual_asset_url, visualAssetUrl('scene_interrogation_room'));
  const title = ending.title || '结局已定';
  const summary = ending.summary || '这场书坊焚稿案已有结果。';
  const endingText = ending.ending_text || '众人的去向已经随你的选择落定。';
  const historyEcho = ending.history_echo || '火案的表层结果已经落定，但书坊、封口令与粮册背后的时代压力并未因此消失。';
  const npcFates = Object.entries(ending.npc_fates ?? {});

  return (

    <main className="ending-screen" style={{ backgroundImage: `linear-gradient(90deg, rgba(8, 6, 7, .9), rgba(8, 6, 7, .45)), url(${backdrop})` }}>
      <section className="ending-scroll">
        <p className="seal-kicker">终章 · 历史回声</p>
        <h1>{title}</h1>
        <p className="ending-summary">{summary}</p>

        <article className="ending-text-block main-ending-text">
          <h3>结局正文</h3>
          <p>{endingText}</p>
        </article>

        <article className="ending-text-block history-echo">
          <h3>历史回声</h3>
          <p>{historyEcho}</p>

          <p className="detail-note">{ending.history_echo_ai_used ? '历史回声由真实智能模型润色。' : '历史回声使用本地中文模板收束。'}</p>

          {ending.history_echo_sources && ending.history_echo_sources.length > 0 ? (
            <ul className="echo-source-list">
              {ending.history_echo_sources.slice(0, 5).map((source) => <li key={source}>{source}</li>)}
            </ul>
          ) : null}
        </article>

        <article className="ending-text-block">
          <h3>众人去向</h3>
          {npcFates.length > 0 ? (
            <ul>
              {npcFates.map(([npcId, fate]) => (
                <li key={npcId}><strong>{npcNameMap[npcId] ?? '案中人物'}：</strong>{String(fate)}</li>
              ))}
            </ul>
          ) : (
            <p>众人去向已随结局落定。</p>
          )}

        </article>


        <div className="ending-catalog">
          {endingCatalog.map((item) => (
            <span key={item.ending_id} className={item.ending_id === ending.ending_id ? 'ending-chip active' : 'ending-chip'}>
              {item.title}
            </span>
          ))}
        </div>

        <button type="button" className="primary-button" onClick={onRestart}>
          重新开始
        </button>
      </section>
    </main>
  );
}
