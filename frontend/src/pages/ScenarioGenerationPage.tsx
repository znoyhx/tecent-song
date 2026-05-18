import { useEffect, useMemo, useState } from 'react';

import { api, visualAssetUrl } from '../api/client';
import type { GeneratedScenarioPreview } from '../mock/entryFlow';
import type { HealthResponse, PlayerIdentityValidationResult } from '../types/game';

type ScenarioGenerationPageProps = {
  health: HealthResponse | null;
  backendReady: boolean;
  preview: GeneratedScenarioPreview;
  busy: boolean;
  errorText: string;
  onBack: () => void;
  onRefreshBackend: () => void;
  onEnterEvent: (identityPayload?: { identity_id?: string; custom_identity_text?: string }) => void;
};

export function ScenarioGenerationPage({
  health,
  backendReady,
  preview,
  busy,
  errorText,
  onBack,
  onRefreshBackend,
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
  const activeIdentityName = customMode && customIdentityValid && identityValidation?.identity
    ? identityValidation.identity.display_name
    : selectedIdentity?.display_name ?? '书坊学徒';
  const rankLabelMap = {
    low: '低身份',
    middle: '中身份',
    high: '高身份',
  } as const;
  const statusTitle = generationDone ? '本局事件已生成' : '本局事件生成中';
  const summaryPairs = useMemo(
    () => [
      ['朝代', preview.dynastyName],
      ['身份', preview.roleName],
      ['事件', preview.eventName],
      ['核心矛盾', preview.coreConflict],
      ['主要 NPC', `${preview.npcCount} 人`],
      ['线索数量', `${preview.clueCount} 条`],
      ['结局数量', `${preview.endingCount} 个`],
    ],
    [preview],
  );

  const badgeClassName = generationDone
    ? backendReady
      ? 'generation-badge ready'
      : 'generation-badge waiting'
    : 'generation-badge pending';
  const badgeText = generationDone ? (backendReady ? '可进入' : '等待后端') : '处理中';
  const enterButtonLabel = busy
    ? '正在载入剧情…'
    : identityBusy
      ? '正在校验身份…'
    : generationDone
      ? backendReady
        ? '开始游戏'
        : '启动后端服务后可进入剧情'
      : '等待剧本生成完成';
  const enterDisabled = busy || identityBusy || !generationDone || !backendReady || (customMode && !customIdentityValid);

  const handleValidateIdentity = async () => {
    if (!customTrimmed) {
      setIdentityError('请先输入你的自定义身份。');
      setIdentityValidation(null);
      return;
    }
    if (!backendReady) {
      setIdentityError('当前后端未连通，暂时不能校验自定义身份。');
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
        setIdentityError(result.rejection_reason || '这个身份暂时不适合当前剧本，请换成时代内可存在、不会压过主线的身份，例如书生、樵夫、游方探事人。');
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
      if (!customIdentityValid) {
        setIdentityError('自定义身份需要先校验通过，才能开始游戏。');
        return;
      }
      onEnterEvent({ custom_identity_text: customTrimmed });
      return;
    }
    onEnterEvent({ identity_id: selectedIdentity?.identity_id ?? preview.identityRecommendations.default_identity });
  };

  return (
    <main
      className="cover-page generation-page"
      style={{ backgroundImage: `linear-gradient(90deg, rgba(8, 7, 9, .86), rgba(8, 7, 9, .38)), url(${visualAssetUrl(preview.coverAssetId)})` }}
    >
      <div className="cover-rain" />

      <section className="cover-copy generation-copy">
        <p className="seal-kicker">剧本生成确认</p>
        <h1>史隙</h1>
        <h2>{statusTitle}</h2>
        <p className="cover-text">
          系统已根据所选朝代，从朝代知识库、事件语法库和 NPC 关系模板中整理出本局剧本原型。确认后即可进入正式剧情页面。
        </p>

        <div className="cover-process-strip">
          <span className="process-pill complete">1 选择朝代</span>
          <span className="process-pill active">2 生成剧本</span>
          <span className="process-pill">3 进入剧情</span>
        </div>

        <div className="generation-summary-grid">
          {summaryPairs.map(([label, value]) => (
            <article key={label} className="generation-stat-card">
              <span>{label}</span>
              <strong>{value}</strong>
            </article>
          ))}
        </div>

        <article className="system-explain-card scenario-brief-card">
          <p className="meta-label">事件简介</p>
          <p>{preview.eventSummary}</p>
          <small>{preview.roleSummary}</small>
          {!backendReady ? <small>当前为离线剧本预览模式。启动后端服务后即可真正进入可玩的剧情环节。</small> : null}
        </article>

        <section className="identity-panel" aria-label="你的身份">
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
                  <small>{option.attitude_hint}</small>
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
              placeholder="也可以输入自定义身份，例如爱喝水的侦探"
              disabled={busy || identityBusy}
            />
            <button type="button" className="secondary-button" onClick={handleValidateIdentity} disabled={busy || identityBusy || !backendReady}>
              {identityBusy ? '校验中…' : '校验身份'}
            </button>
          </div>

          {customMode && customIdentityValid ? <p className="identity-valid-hint">身份校验通过，可以开始游戏。</p> : null}
          {identityError ? <div className="identity-error">{identityError}</div> : null}

          <div className="identity-background-preview">
            <span>身份背景预览</span>
            <p>{activeBackground}</p>
          </div>
        </section>

        {errorText ? <div className="error-banner cover-error">{errorText}</div> : null}

        <div className="generation-actions">
          <button type="button" className="secondary-button" onClick={onBack} disabled={busy}>
            重新选择朝代
          </button>
          {!backendReady ? (
            <button type="button" className="secondary-button" onClick={onRefreshBackend} disabled={busy}>
              {busy ? '正在检测引擎…' : '重新检测引擎'}
            </button>
          ) : null}
          <button type="button" className="primary-button" onClick={handleEnterEvent} disabled={enterDisabled}>
            {enterButtonLabel}
          </button>
        </div>
      </section>

      <aside className="cover-selector generation-selector">
        <div className="selector-block generation-progress-panel">
          <div className="generation-panel-header">
            <div>
              <p className="meta-label">生成流程</p>
              <h3>{generationDone ? '生成完成' : '正在构建本局事件'}</h3>
            </div>
            <span className={badgeClassName}>{badgeText}</span>
          </div>

          <div className="generation-step-list">
            {preview.generationSteps.map((step, index) => {
              const state = index + 1 < resolvedStepCount ? 'done' : index + 1 === resolvedStepCount && !generationDone ? 'active' : generationDone ? 'done' : 'pending';
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
        </div>

        <div className="selector-block">
          <p className="meta-label">生成说明</p>
          <p className="selected-dynasty-copy">{preview.teaser}</p>
          <div className="cover-meta-row compact-meta-row">
            <span>朝代：{preview.dynastyName}</span>
            <span>时期：{preview.dynastyPeriod}</span>
            <span>后端：{health?.status === 'ok' ? '引擎已连通' : '离线预览中'}</span>
          </div>
        </div>
      </aside>
    </main>
  );
}
