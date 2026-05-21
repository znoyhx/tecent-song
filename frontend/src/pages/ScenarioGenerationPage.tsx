import type { CSSProperties } from 'react';
import { useEffect, useMemo, useState } from 'react';

import { api } from '../api/client';
import type { GeneratedScenarioPreview } from '../mock/entryFlow';
import type { PlayerIdentityValidationResult } from '../types/game';

type ScenarioGenerationPageProps = {
  backendReady: boolean;
  preview: GeneratedScenarioPreview;
  busy: boolean;
  errorText: string;
  onBack: () => void;
  onEnterEvent: (identityPayload?: { identity_id?: string; custom_identity_text?: string }) => void;
};

const entryBackground = '/generated-ui/concept-entry-bg.png';
const identityPortraitSheet = '/generated-ui/identity-portraits-sheet.png';

const identityVisuals: Record<string, { x: string; y: string }> = {
  bookshop_apprentice: { x: '0%', y: '0%' },
  wandering_detective: { x: '50%', y: '0%' },
  lodging_scholar: { x: '100%', y: '0%' },
  woodcutter: { x: '0%', y: '100%' },
  wandering_physician: { x: '50%', y: '100%' },
  retired_official: { x: '100%', y: '100%' },
};

const coreCast = [
  { name: '人物一', x: '0%', y: '0%' },
  { name: '人物二', x: '50%', y: '0%' },
  { name: '人物三', x: '100%', y: '0%' },
  { name: '人物四', x: '0%', y: '100%' },
];

function conceptStyle(extra?: Record<string, string>): CSSProperties {
  return {
    '--concept-bg': `url(${entryBackground})`,
    ...extra,
  } as CSSProperties;
}

function identityStyle(position?: { x: string; y: string }): CSSProperties {
  return {
    '--identity-sheet': `url(${identityPortraitSheet})`,
    '--identity-position': position ? `${position.x} ${position.y}` : '50% 50%',
  } as CSSProperties;
}

export function ScenarioGenerationPage({
  backendReady,
  preview,
  busy,
  errorText,
  onBack,
  onEnterEvent,
}: ScenarioGenerationPageProps) {
  const [resolvedStepCount, setResolvedStepCount] = useState(1);
  const [selectedIdentityId, setSelectedIdentityId] = useState(preview.identityRecommendations.default_identity);
  const [customIdentityText, setCustomIdentityText] = useState('');
  const [identityValidation, setIdentityValidation] = useState<PlayerIdentityValidationResult | null>(null);
  const [identityError, setIdentityError] = useState('');
  const [identityBusy, setIdentityBusy] = useState(false);

  useEffect(() => {
    setResolvedStepCount(1);
    setSelectedIdentityId(preview.identityRecommendations.default_identity);
    setCustomIdentityText('');
    setIdentityValidation(null);
    setIdentityError('');
    const timer = window.setInterval(() => {
      setResolvedStepCount((current) => {
        if (current >= preview.generationSteps.length) {
          window.clearInterval(timer);
          return current;
        }
        return current + 1;
      });
    }, 420);

    return () => window.clearInterval(timer);
  }, [preview]);

  const generationDone = resolvedStepCount >= preview.generationSteps.length;
  const identityOptions = preview.identityRecommendations.options;
  const selectedIdentity = identityOptions.find((option) => option.identity_id === selectedIdentityId) ?? identityOptions[0] ?? null;
  const customTrimmed = customIdentityText.trim();
  const customMode = customTrimmed.length > 0;
  const customIdentityValid = customMode && identityValidation?.is_valid && identityValidation.identity?.display_name === customTrimmed;
  const activeBackground = customMode && customIdentityValid && identityValidation?.identity
    ? identityValidation.identity.background
    : selectedIdentity?.background ?? '';
  const activeIdentityName = customMode
    ? customTrimmed
    : selectedIdentity?.display_name ?? '书坊学徒';
  const progressPercent = Math.min(99, Math.max(12, Math.round((resolvedStepCount / preview.generationSteps.length) * 100)));
  const rankLabelMap = {
    low: '低身份',
    middle: '中身份',
    high: '高身份',
  } as const;
  const summaryPairs = useMemo(
    () => [
      ['朝代', preview.dynastyName],
      ['关键词', preview.keywordText],
      ['事件', preview.eventName],
      ['核心矛盾', preview.coreConflict],
      ['主要人物', `${preview.npcCount} 人`],
      ['线索数量', `${preview.clueCount} 条`],
      ['结局数量', `${preview.endingCount} 个`],
    ],
    [preview],
  );

  const enterButtonLabel = busy
    ? '正在载入剧情...'
    : identityBusy
      ? '正在校验身份...'
      : '开始游戏';
  const enterDisabled = busy || identityBusy || !generationDone;

  const handleValidateIdentity = async () => {
    if (!customTrimmed) {
      setIdentityError('请先输入你的自定义身份。');
      setIdentityValidation(null);
      return;
    }
    if (!backendReady) {
      setIdentityError('当前无法连接身份校验，仍可直接开始游戏。');
      setIdentityValidation(null);
      return;
    }
    setIdentityBusy(true);
    setIdentityError('');
    try {
      const result = await api.validatePlayerIdentity({
        dynasty_id: preview.dynastyId,
        event_id: preview.eventId,
        custom_identity_text: customTrimmed,
      });
      setIdentityValidation(result);
      if (!result.is_valid) {
        setIdentityError(result.rejection_reason || '这个身份暂时不适合当前剧本，可以换成书生、樵夫、游方探事人一类身份。');
      }
    } catch (error) {
      setIdentityValidation(null);
      setIdentityError(error instanceof Error ? error.message : '身份校验失败，请稍后重试。');
    } finally {
      setIdentityBusy(false);
    }
  };

  const handleEnterEvent = () => {
    if (customMode) {
      onEnterEvent({ custom_identity_text: customTrimmed });
      return;
    }
    onEnterEvent({ identity_id: selectedIdentity?.identity_id ?? preview.identityRecommendations.default_identity });
  };

  if (!generationDone) {
    return (
      <main
        className="script-loading-stage concept-entry-page concept-loading-page"
        style={conceptStyle({
          '--progress-deg': `${Math.round(progressPercent * 3.6)}deg`,
        })}
      >
        <div className="concept-atmosphere" />

        <section className="concept-generation-modal gilded-panel" aria-live="polite">
          <button type="button" className="modal-close" aria-label="返回" onClick={onBack} disabled={busy}>
            ×
          </button>
          <p className="concept-step-label">步骤 2/3</p>
          <h1>剧本生成中</h1>

          <div className="progress-orb" aria-label={`生成进度 ${progressPercent}%`}>
            <div className="progress-orb-scene" />
            <strong>{progressPercent}%</strong>
          </div>

          <div className="generation-step-list script-step-list concept-progress-list">
            {preview.generationSteps.map((step, index) => {
              const state = index + 1 < resolvedStepCount ? 'done' : index + 1 === resolvedStepCount ? 'active' : 'pending';
              return (
                <article key={step.id} className={`generation-step ${state}`}>
                  <span className="generation-step-dot" />
                  <div>
                    <strong>{step.title}</strong>
                    <p>{step.detail}</p>
                  </div>
                </article>
              );
            })}
          </div>

          <p className="generation-whisper">AI 生成中，请稍候...</p>
        </section>
      </main>
    );
  }

  return (
    <main
      className="script-overview-page concept-entry-page concept-overview-page"
      style={conceptStyle()}
    >
      <div className="concept-atmosphere" />

      <section className="concept-overview-board gilded-panel" aria-label="身份选择与剧本概览">
        <header className="concept-overview-header">
          <button type="button" className="secondary-button concept-back-button" onClick={onBack} disabled={busy}>
            重新选择
          </button>
          <div className="ornate-heading">
            <span />
            <p>步骤 3/3</p>
            <span />
          </div>
          <h1>{preview.eventName}</h1>
        </header>

        <div className="concept-overview-layout">
          <section className="concept-identity-column" aria-label="身份选择">
            <div className="ornate-heading mini">
              <span />
              <h2>身份选择</h2>
              <span />
            </div>

            <div className="concept-identity-grid">
              {identityOptions.map((option) => {
                const active = !customMode && option.identity_id === selectedIdentityId;
                const portraitPosition = identityVisuals[option.identity_id];
                return (
                  <button
                    key={option.identity_id}
                    type="button"
                    className={active ? 'concept-identity-card active' : 'concept-identity-card'}
                    style={identityStyle(portraitPosition)}
                    onClick={() => {
                      setSelectedIdentityId(option.identity_id);
                      setCustomIdentityText('');
                      setIdentityValidation(null);
                      setIdentityError('');
                    }}
                    disabled={busy || identityBusy}
                  >
                    <span className="identity-portrait" aria-hidden="true" />
                    <span className="identity-check" aria-hidden="true">✓</span>
                    <strong>{option.display_name}</strong>
                    <small>{option.description}</small>
                    <em>{rankLabelMap[option.social_rank]}</em>
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
                placeholder="输入自定义身份"
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
                <p>{preview.eventSummary}</p>
              </section>

              <section className="brief-section">
                <h3>核心人物</h3>
                <div className="core-cast-row">
                  {coreCast.map((member) => (
                    <span
                      key={member.name}
                      className="core-avatar generated"
                      style={identityStyle({ x: member.x, y: member.y })}
                      title={member.name}
                    />
                  ))}
                  <span className="core-avatar more">...</span>
                </div>
              </section>

              <section className="brief-section">
                <h3>调查目标</h3>
                <p>{preview.coreConflict}</p>
              </section>

              <section className="brief-section identity-background-preview concept-background-preview">
                <span>当前身份</span>
                <h3>{activeIdentityName}</h3>
                <p>{customMode && !customIdentityValid ? '将以你填写的身份进入剧本，开局后由剧情系统接管人物立场。' : activeBackground}</p>
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
          <button type="button" className="imperial-button" onClick={handleEnterEvent} disabled={enterDisabled}>
            <span>{enterButtonLabel}</span>
          </button>
        </div>
      </section>
    </main>
  );
}
