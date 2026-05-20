import { useEffect, useMemo, useState } from 'react';

import { api, visualAssetUrl } from '../api/client';
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
    ? '正在载入剧情…'
    : identityBusy
      ? '正在校验身份…'
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
        className="script-loading-stage"
        style={{ backgroundImage: `linear-gradient(90deg, rgba(7, 8, 10, .9), rgba(7, 8, 10, .58)), url(${visualAssetUrl(preview.coverAssetId)})` }}
      >
        <div className="cover-rain" />
        <section className="script-progress-card" aria-live="polite">
          <p className="seal-kicker">剧本生成</p>
          <h1>正在构建本局事件</h1>
          <div className="generation-step-list script-step-list">
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
        </section>
      </main>
    );
  }

  return (
    <main
      className="script-overview-page"
      style={{ backgroundImage: `linear-gradient(90deg, rgba(7, 8, 10, .86), rgba(7, 8, 10, .48)), url(${visualAssetUrl(preview.coverAssetId)})` }}
    >
      <div className="cover-rain" />

      <section className="script-overview-shell" aria-label="剧本概览">
        <header className="script-overview-header">
          <div>
            <p className="seal-kicker">剧本概览</p>
            <h1>{preview.eventName}</h1>
          </div>
          <button type="button" className="secondary-button" onClick={onBack} disabled={busy}>
            重新选择
          </button>
        </header>

        <div className="script-overview-grid">
          <section className="script-case-panel" aria-label="事件概览">
            <p className="script-summary-text">{preview.eventSummary}</p>
            <div className="generation-summary-grid script-summary-grid">
              {summaryPairs.map(([label, value]) => (
                <article key={label} className="generation-stat-card">
                  <span>{label}</span>
                  <strong>{value}</strong>
                </article>
              ))}
            </div>
            <article className="scenario-brief-card script-role-brief">
              <p className="meta-label">初始立场</p>
              <p>{preview.roleSummary}</p>
            </article>
          </section>

          <section className="identity-panel script-identity-panel" aria-label="你的身份">
            <div className="identity-panel-header">
              <div>
                <p className="meta-label">你的身份</p>
                <h3>{activeIdentityName}</h3>
              </div>
              {selectedIdentity?.is_default && !customMode ? <span className="identity-default-badge">默认身份</span> : null}
            </div>

            <div className="identity-option-list">
              {identityOptions.map((option) => {
                const active = !customMode && option.identity_id === selectedIdentityId;
                return (
                  <button
                    key={option.identity_id}
                    type="button"
                    className={active ? 'identity-option active' : 'identity-option'}
                    onClick={() => {
                      setSelectedIdentityId(option.identity_id);
                      setCustomIdentityText('');
                      setIdentityValidation(null);
                      setIdentityError('');
                    }}
                    disabled={busy || identityBusy}
                  >
                    <span className="identity-option-title">
                      <strong>{option.display_name}</strong>
                      <em>{rankLabelMap[option.social_rank]}</em>
                      {option.is_default ? <b>默认</b> : null}
                    </span>
                    <small>{option.description}</small>
                  </button>
                );
              })}
            </div>

            <div className="identity-custom-row">
              <input
                value={customIdentityText}
                onChange={(event) => {
                  setCustomIdentityText(event.target.value);
                  setIdentityValidation(null);
                  setIdentityError('');
                }}
                placeholder="也可以输入自定义身份"
                disabled={busy || identityBusy}
              />
              <button type="button" className="secondary-button" onClick={handleValidateIdentity} disabled={busy || identityBusy}>
                {identityBusy ? '校验中…' : '校验身份'}
              </button>
            </div>

            {customMode && customIdentityValid ? <p className="identity-valid-hint">身份校验通过。</p> : null}
            {identityError ? <div className="identity-error">{identityError}</div> : null}

            <div className="identity-background-preview">
              <span>身份背景预览</span>
              <p>{customMode && !customIdentityValid ? '将以你填写的身份进入剧本，开局后由剧情系统接管人物立场。' : activeBackground}</p>
            </div>
          </section>
        </div>

        {errorText ? <div className="error-banner cover-error">{errorText}</div> : null}

        <div className="generation-actions script-overview-actions">
          <button type="button" className="primary-button" onClick={handleEnterEvent} disabled={enterDisabled}>
            {enterButtonLabel}
          </button>
        </div>
      </section>
    </main>
  );
}
