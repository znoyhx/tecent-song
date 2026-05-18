import type { DebugLog, SessionSnapshot } from '../../types/game';

type DemoEvidencePanelProps = {
  snapshot: SessionSnapshot;
};

const secretPattern = /Bearer\s+|Authorization|sk-[A-Za-z0-9_\-]{8,}/g;

const moduleLabels: Record<string, string> = {
  NPCDialogueAgent: '人物对话生成',
  RepairAgent: '合规修复',
  mock_dialogue: '本地对话规则',
  scene_investigate: '场景调查规则',
  history_echo: '历史回声生成',
  ending_resolve: '结局规则判定',
  choice: '最终抉择规则',
};

const safeTermLabels: Record<string, string> = {
  ash_pile: '灰烬堆',
  char_mark: '起火点',
  lamp_shelf: '灯油架',
  ledger_desk: '账册桌',
  old_box: '旧书箱',
  back_door: '后门',
  search_notice: '搜检告示',
  sealed_desk: '案桌封条',
  choice_help_scholar: '暗助顾闻护出残页',
  choice_give_to_lu: '将残页交给陆峥',
  choice_destroy_evidence: '焚尽余稿，先保书坊',
  choice_force_worker: '逼阿沈作证换路',
  choice_reverse_trace: '顺着封口令反查上游',
};

function safeText(value: unknown): string {
  const text = String(value ?? '').replace(secretPattern, '[已隐藏敏感信息]');
  return Object.entries(safeTermLabels).reduce(
    (current, [term, label]) => current.split(term).join(label),
    text,
  );
}

function moduleLabel(log: DebugLog): string {
  return moduleLabels[log.module] ?? '受控后端模块';
}

function boolLabel(value: boolean): string {
  return value ? '是' : '否';
}

export function DemoEvidencePanel({ snapshot }: DemoEvidencePanelProps) {
  const ending = snapshot.ending;
  const logs = [...(snapshot.debug_info.logs ?? [])].slice(-4).reverse();
  const modelMode = snapshot.debug_info.use_mock_ai ? '本地演示模式' : '真实模型请求模式';
  const supervisor = snapshot.debug_info.last_supervisor;
  const supervisorText = supervisor
    ? supervisor.pass
      ? '最近一次监管通过'
      : '最近一次监管已拦截并回退'
    : '尚无监管记录';
  const historyEchoSource = ending
    ? ending.history_echo_ai_used
      ? '真实智能模型润色'
      : '本地中文模板收束'
    : '尚未进入历史回声';

  return (
    <aside className="demo-evidence-panel" aria-label="演示证据面板">
      <div className="demo-evidence-header">
        <p className="meta-label">演示证据</p>
        <strong>智能模型参与边界</strong>
      </div>

      <div className="demo-evidence-grid">
        <span>模型参与</span>
        <strong>{modelMode}</strong>
        <span>本地回退</span>
        <strong>{logs.some((log) => log.fallback_used) || ending?.history_echo_fallback_used ? '已记录' : '未触发'}</strong>
        <span>监管通过</span>
        <strong>{supervisorText}</strong>
        <span>历史回声来源</span>
        <strong>{historyEchoSource}</strong>
        <span>规则判定结局</span>
        <strong>{ending ? ending.title : '尚未判定'}</strong>
      </div>

      <p className="demo-evidence-boundary">结局编号由后端状态、线索、分数和最终抉择规则判定；智能模型只参与人物表达、合规修复或历史回声润色。</p>

      <div className="demo-log-list" aria-label="安全调用摘要">
        {logs.length > 0 ? (
          logs.map((log) => (
            <article key={log.call_id} className="demo-log-card">
              <div>
                <strong>{moduleLabel(log)}</strong>
                <time>{safeText(log.created_at)}</time>
              </div>
              <p>{safeText(log.summary)}</p>
              <ul>
                <li>执行成功：{boolLabel(log.success)}</li>
                <li>本地回退：{boolLabel(log.fallback_used)}</li>
                <li>监管通过：{boolLabel(log.supervisor_pass)}</li>
              </ul>
            </article>
          ))
        ) : (
          <p className="demo-log-empty">尚无调用记录。调查或对话后会显示安全摘要。</p>
        )}
      </div>
    </aside>
  );
}
