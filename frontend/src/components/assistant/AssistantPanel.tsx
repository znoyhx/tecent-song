import { useMemo, useState } from 'react';

import { api } from '../../api/client';
import type { SessionSnapshot } from '../../types/game';

type AssistantMessage = {
  role: 'player' | 'assistant' | 'system';
  text: string;
  focus?: string[];
};

type AssistantPanelProps = {
  snapshot: SessionSnapshot;
  compact?: boolean;
};

const starterQuestions = [
  '目前哪条线索最值得复查？',
  '谁的说法和物证冲突最大？',
  '我接下来该去哪个地点？',
];

export function AssistantPanel({ snapshot, compact = false }: AssistantPanelProps) {
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState<AssistantMessage[]>([
    {
      role: 'system',
      text: '助手只会依据当前已发现线索给出提示，不会替你决定结局。',
    },
  ]);
  const [busy, setBusy] = useState(false);

  const discoveredSummary = useMemo(() => {
    if (snapshot.clues.length === 0) {
      return '尚未发现线索';
    }
    return snapshot.clues.slice(-4).map((clue) => clue.title).join('、');
  }, [snapshot.clues]);

  const sendQuestion = async (content: string) => {
    const trimmed = content.trim();
    if (!trimmed || busy) {
      return;
    }
    setBusy(true);
    setQuestion('');
    setMessages((current) => [...current, { role: 'player', text: trimmed }]);
    try {
      const result = await api.askAssistant({ session_id: snapshot.session_id, question: trimmed });
      setMessages((current) => [
        ...current,
        {
          role: 'assistant',
          text: result.answer,
          focus: result.suggested_focus,
        },
      ]);
    } catch (error) {
      const message = error instanceof Error ? error.message : '智能助手暂时无法回应。';
      setMessages((current) => [
        ...current,
        {
          role: 'system',
          text: message,
        },
      ]);
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className={compact ? 'assistant-panel compact' : 'assistant-panel'} aria-label="智能助手">
      <header className="assistant-panel-head">
        <p className="meta-label">智能助手</p>
        <h3>只看当前案卷的提示</h3>
        <span>当前地点：{snapshot.scene.name} · 已发现：{discoveredSummary}</span>
      </header>

      <div className="assistant-message-list">
        {messages.map((message, index) => (
          <article key={`${message.role}-${index}`} className={`assistant-message ${message.role}`}>
            <p>{message.text}</p>
            {message.focus && message.focus.length > 0 ? (
              <div className="assistant-focus-list">
                {message.focus.map((item) => <span key={item}>{item}</span>)}
              </div>
            ) : null}
          </article>
        ))}
      </div>

      <div className="assistant-starters" aria-label="助手推荐问题">
        {starterQuestions.map((item) => (
          <button key={item} type="button" onClick={() => void sendQuestion(item)} disabled={busy}>
            {item}
          </button>
        ))}
      </div>

      <form
        className="assistant-input-row"
        onSubmit={(event) => {
          event.preventDefault();
          void sendQuestion(question);
        }}
      >
        <textarea
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="问助手当前证据链，不要让它替你下结论。"
          rows={compact ? 2 : 3}
          disabled={busy}
        />
        <button type="submit" className="primary-button" disabled={busy || !question.trim()}>
          {busy ? '思索中' : '询问'}
        </button>
      </form>
    </section>
  );
}
