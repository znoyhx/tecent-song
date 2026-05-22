import { useEffect, useMemo, useRef, useState } from 'react';

import { getTrustLabel } from '../../store/gameStore';
import type { Clue, DialogueHighlight, DialogueTurn, NPCProfile, SessionSnapshot } from '../../types/game';

type DialoguePanelProps = {
  snapshot: SessionSnapshot;
  sceneNpcs: NPCProfile[];
  dialogueTurns: DialogueTurn[];
  selectedNpcId: string | null;
  suggestedQuestions: string[];
  highlightClues: DialogueHighlight[];
  redTexts: string[];
  actionNotice: string;
  busy: boolean;
  onSendDialogue: (npcId: string, message: string, presentedClueIds: string[]) => void;
};

function parseLine(actionNotice: string, currentNpc?: NPCProfile): { speaker: string; body: string } {
  const dividerIndex = actionNotice.indexOf('：');
  if (dividerIndex > 0 && dividerIndex < 10) {
    return {
      speaker: actionNotice.slice(0, dividerIndex),
      body: actionNotice.slice(dividerIndex + 1),
    };
  }
  return { speaker: currentNpc?.name ?? '旁白', body: actionNotice };
}

const fallbackQuestions = [
  '昨夜你最后一次见到账页是什么时候？',
  '许掌柜为何如此急着结案？',
  '我想再确认灰烬里的痕迹。',
];

type HighlightTerm = {
  text: string;
  clueId?: string;
  title?: string;
};

const clueTypeLabels: Record<string, string> = {
  document: '文书',
  environment: '现场',
  behavior: '证言',
  evidence: '物证',
  institution: '制度',
  identity: '身份',
};

function clueTypeLabel(clue: Clue): string {
  return clueTypeLabels[clue.type] ?? '线索';
}

export function DialoguePanel({
  snapshot,
  sceneNpcs,
  dialogueTurns,
  selectedNpcId,
  suggestedQuestions,
  highlightClues,
  redTexts,
  actionNotice,
  busy,
  onSendDialogue,
}: DialoguePanelProps) {
  const [message, setMessage] = useState('');
  const [selectedEvidenceIds, setSelectedEvidenceIds] = useState<string[]>([]);
  const [evidenceOpen, setEvidenceOpen] = useState(false);
  const [evidenceQuery, setEvidenceQuery] = useState('');
  const [evidenceType, setEvidenceType] = useState('all');
  const evidencePresenterRef = useRef<HTMLDivElement | null>(null);

  const currentNpc = useMemo(
    () => sceneNpcs.find((item) => item.npc_id === selectedNpcId) ?? sceneNpcs[0],
    [sceneNpcs, selectedNpcId],
  );

  const recentTurns = useMemo(() => {
    if (!currentNpc) {
      return [];
    }
    return dialogueTurns.filter((turn) => turn.npc_id === currentNpc.npc_id).slice(-2);
  }, [currentNpc, dialogueTurns]);

  const currentLine = parseLine(actionNotice, currentNpc);
  const currentTrust = currentNpc ? snapshot.state.npc_trust[currentNpc.npc_id] ?? currentNpc.initial_trust : 0;
  const highlightTerms = useMemo(() => {
    const terms: HighlightTerm[] = [];
    highlightClues.forEach((item) => {
      const text = item.highlight_text.trim();
      if (text && !terms.some((term) => term.text === text)) {
        terms.push({ text, clueId: item.clue_id, title: item.display_text });
      }
    });
    redTexts.forEach((item) => {
      const text = item.trim();
      if (text && !terms.some((term) => term.text === text)) {
        terms.push({ text });
      }
    });
    return terms.sort((left, right) => right.text.length - left.text.length);
  }, [highlightClues, redTexts]);
  const replySuggestions = (suggestedQuestions.length > 0 ? suggestedQuestions : fallbackQuestions).slice(0, 3);
  const recentEvidence = snapshot.clues.slice(-5).reverse();
  const presentedEvidenceIds = useMemo(
    () => new Set(dialogueTurns.flatMap((turn) => turn.presented_clue_ids)),
    [dialogueTurns],
  );
  const clueTypes = useMemo(() => Array.from(new Set(snapshot.clues.map((clue) => clue.type))), [snapshot.clues]);
  const selectedEvidence = useMemo(
    () => selectedEvidenceIds
      .map((clueId) => snapshot.clues.find((clue) => clue.clue_id === clueId))
      .filter((clue): clue is Clue => Boolean(clue)),
    [selectedEvidenceIds, snapshot.clues],
  );
  const filteredEvidence = useMemo(() => {
    const query = evidenceQuery.trim().toLowerCase();
    return snapshot.clues.filter((clue) => {
      const matchesType = evidenceType === 'all' || clue.type === evidenceType;
      const searchable = `${clue.title} ${clue.display_text} ${clue.highlight_text}`.toLowerCase();
      const matchesQuery = !query || searchable.includes(query);
      return matchesType && matchesQuery;
    });
  }, [evidenceQuery, evidenceType, snapshot.clues]);

  useEffect(() => {
    setSelectedEvidenceIds((current) => current.filter((clueId) => snapshot.clues.some((clue) => clue.clue_id === clueId)));
  }, [snapshot.clues]);

  useEffect(() => {
    if (!evidenceOpen) {
      return undefined;
    }

    const handlePointerDown = (event: PointerEvent) => {
      const target = event.target;
      if (target instanceof Node && evidencePresenterRef.current?.contains(target)) {
        return;
      }
      setEvidenceOpen(false);
    };

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setEvidenceOpen(false);
      }
    };

    document.addEventListener('pointerdown', handlePointerDown);
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('pointerdown', handlePointerDown);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [evidenceOpen]);

  const toggleEvidence = (clueId: string) => {
    setSelectedEvidenceIds((current) => (
      current.includes(clueId) ? current.filter((item) => item !== clueId) : [...current, clueId].slice(-3)
    ));
  };

  const handleSend = (nextMessage?: string) => {
    if (!currentNpc) {
      return;
    }
    const content = (nextMessage ?? message).trim() || (selectedEvidenceIds.length > 0 ? '请看这几条证据。' : '');
    if (!content) {
      return;
    }
    onSendDialogue(currentNpc.npc_id, content, selectedEvidenceIds);
    setMessage('');
    setSelectedEvidenceIds([]);
    setEvidenceOpen(false);
  };

  return (
    <section className={evidenceOpen ? 'dialogue-box evidence-open' : 'dialogue-box'} aria-label="当前对话">
      <div className="dialogue-line-head">
        <div className="speaker-nameplate">{currentLine.speaker}</div>
        {currentNpc ? (
          <div className="dialogue-speaker-meta">
            <span>{currentNpc.public_identity}</span>
            <span>信任：{getTrustLabel(currentTrust)}（{currentTrust}）</span>
          </div>
        ) : null}
      </div>

      <div className="dialogue-main-text">
        <p>{renderHighlightedText(currentLine.body, highlightTerms)}</p>
      </div>

      <div className="evidence-presenter" ref={evidencePresenterRef}>
        <div className="evidence-summary-row">
          <button
            type="button"
            className={evidenceOpen ? 'evidence-drawer-toggle active' : 'evidence-drawer-toggle'}
            onClick={() => setEvidenceOpen((open) => !open)}
            disabled={busy || !currentNpc || snapshot.clues.length === 0}
          >
            出示线索
          </button>
          <div className="selected-evidence-strip" aria-label="当前选择的证据">
            {selectedEvidence.length > 0 ? selectedEvidence.map((clue) => (
              <button key={clue.clue_id} type="button" className="selected-evidence-chip" onClick={() => toggleEvidence(clue.clue_id)} disabled={busy}>
                {clue.title} ×
              </button>
            )) : <span>未选择线索</span>}
          </div>
        </div>

        {recentEvidence.length > 0 ? (
          <div className="evidence-quick-row" aria-label="最近关键线索">
            {recentEvidence.map((clue) => (
              <button
                key={clue.clue_id}
                type="button"
                className={[
                  'quick-evidence-chip',
                  selectedEvidenceIds.includes(clue.clue_id) ? 'active' : '',
                  presentedEvidenceIds.has(clue.clue_id) ? 'presented' : '',
                ].filter(Boolean).join(' ')}
                onClick={() => toggleEvidence(clue.clue_id)}
                disabled={busy || !currentNpc}
              >
                {clue.title}
              </button>
            ))}
          </div>
        ) : null}

        {evidenceOpen ? (
          <div className="evidence-drawer" aria-label="证据选择面板">
            <div className="evidence-filter-row">
              <input
                type="search"
                value={evidenceQuery}
                onChange={(event) => setEvidenceQuery(event.target.value)}
                placeholder="搜索线索"
                disabled={busy}
              />
              <select value={evidenceType} onChange={(event) => setEvidenceType(event.target.value)} disabled={busy}>
                <option value="all">全部类型</option>
                {clueTypes.map((type) => <option key={type} value={type}>{clueTypeLabels[type] ?? type}</option>)}
              </select>
            </div>
            <div className="evidence-option-list">
              {filteredEvidence.length > 0 ? filteredEvidence.map((clue) => (
                <button
                  key={clue.clue_id}
                  type="button"
                  className={[
                    'evidence-option',
                    selectedEvidenceIds.includes(clue.clue_id) ? 'active' : '',
                    presentedEvidenceIds.has(clue.clue_id) ? 'presented' : '',
                  ].filter(Boolean).join(' ')}
                  onClick={() => toggleEvidence(clue.clue_id)}
                  disabled={busy}
                >
                  <strong>
                    {clue.title}
                    {presentedEvidenceIds.has(clue.clue_id) ? <em>已出示</em> : null}
                  </strong>
                  <span>{clueTypeLabel(clue)} · {clue.highlight_text}</span>
                </button>
              )) : <div className="evidence-empty">没有匹配的线索。</div>}
            </div>
          </div>
        ) : null}

        <div className="suggested-row" aria-label="推荐回复">
          {replySuggestions.map((question) => (
            <button key={question} type="button" className="suggested-button" onClick={() => handleSend(question)} disabled={busy || !currentNpc}>
              {question}
            </button>
          ))}
        </div>

        <div className="question-row dialogue-input-row">
          <textarea
            value={message}
            onChange={(event) => setMessage(event.target.value)}
            placeholder="低声追问，例如：昨夜是谁先到火场？"
            rows={2}
            disabled={busy || !currentNpc}
          />
          <button type="button" className="primary-button ask-button" onClick={() => handleSend()} disabled={busy || !currentNpc}>
            {selectedEvidenceIds.length > 0 ? '出示并追问' : '继续追问'}
          </button>
        </div>
      </div>

      {recentTurns.length > 0 ? (
        <details className="dialogue-history-peek">
          <summary>查看最近对话</summary>
          <div className="dialogue-memory">
            {recentTurns.map((turn) => (
              <article key={turn.turn_id}>
                <span>你：{turn.player_message}</span>
                <strong>{turn.npc_name}：{turn.npc_response}</strong>
              </article>
            ))}
          </div>
        </details>
      ) : null}
    </section>
  );
}

function renderHighlightedText(text: string, terms: HighlightTerm[]) {
  if (terms.length === 0) {
    return text;
  }

  const nodes: Array<string | HighlightTerm> = [];
  let remaining = text;
  while (remaining.length > 0) {
    let matchIndex = -1;
    let matchTerm: HighlightTerm | null = null;
    for (const term of terms) {
      const index = remaining.indexOf(term.text);
      if (index < 0) {
        continue;
      }
      if (matchTerm === null || index < matchIndex || (index === matchIndex && term.text.length > matchTerm.text.length)) {
        matchIndex = index;
        matchTerm = term;
      }
    }

    if (matchTerm === null) {
      nodes.push(remaining);
      break;
    }
    if (matchIndex > 0) {
      nodes.push(remaining.slice(0, matchIndex));
    }
    nodes.push(matchTerm);
    remaining = remaining.slice(matchIndex + matchTerm.text.length);
  }

  return nodes.map((node, index) => {
    if (typeof node === 'string') {
      return <span key={`${node}-${index}`}>{node}</span>;
    }
    return (
      <span key={`${node.text}-${index}`} className="dialogue-red-text" title={node.title}>
        {node.text}
      </span>
    );
  });
}
