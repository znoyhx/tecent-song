import { useEffect, useMemo, useState } from 'react';

import { resolveApiUrl } from '../../api/client';

import type { NPCProfile } from '../../types/game';

type CharacterPortraitProps = {
  character: NPCProfile;
  active: boolean;
};

type PortraitState = 'idle' | 'generating' | 'ready' | 'fallback';

function fallbackTone(character: NPCProfile): string {
  if (character.npc_id.includes('jinyiwei')) {
    return 'stern';
  }
  if (character.npc_id.includes('worker')) {
    return 'young';
  }
  if (character.npc_id.includes('scholar')) {
    return 'scholar';
  }
  return 'owner';
}

export function buildPortraitPrompt(character: NPCProfile): string {
  const dynasty = character.dynasty ?? '明代';
  const role = character.role ?? character.public_identity;
  const temperament = character.temperament ?? character.speaking_style ?? character.emotion_state;
  return `中国古代历史题材视觉小说角色半身立绘，朝代：${dynasty}，身份：${role}，人物气质：${temperament}，低饱和国风，电影感光影，半身像，正面或三分之二侧身，背景透明或极简暗色背景，适合网页叙事游戏 UI，不要现代服饰，不要现代物品，不要文字，不要水印`;
}

export function CharacterPortrait({ character, active }: CharacterPortraitProps) {
  const initialUrl = useMemo(() => {
    const directUrl = character.portraitUrl ?? character.imageUrl ?? character.avatarUrl;
    if (directUrl) {
      return resolveApiUrl(directUrl);
    }
    if (character.visual_asset_url) {
      return resolveApiUrl(character.visual_asset_url);
    }
    if (character.visual_asset_id) {
      return resolveApiUrl(`/api/visual/assets/${character.visual_asset_id}`);
    }
    return '';
  }, [character.avatarUrl, character.imageUrl, character.portraitUrl, character.visual_asset_id, character.visual_asset_url]);


  const [portraitUrl, setPortraitUrl] = useState(initialUrl);
  const [status, setStatus] = useState<PortraitState>(initialUrl ? 'ready' : 'idle');
  const [imageFailed, setImageFailed] = useState(false);

  useEffect(() => {
    setPortraitUrl(initialUrl);
    setImageFailed(false);
    setStatus(initialUrl ? 'ready' : 'idle');
  }, [initialUrl, character.npc_id]);



  const showImage = Boolean(portraitUrl && !imageFailed);
  const tone = fallbackTone(character);

  return (
    <div className={active ? `character-portrait active tone-${tone}` : `character-portrait tone-${tone}`} aria-label={`${character.name}立绘`}>
      {showImage ? (
        <img
          src={portraitUrl}
          alt={`${character.name}立绘`}
          className="character-portrait-image"
          onError={() => {
            setImageFailed(true);
            setStatus('fallback');
          }}
        />
      ) : (
        <div className="default-character-silhouette" data-name={character.name}>
          {status === 'generating' ? <span className="portrait-loading">正在生成角色立绘...</span> : null}
          <div className="silhouette-head" />
          <div className="silhouette-body" />
          <div className="silhouette-sleeve left" />
          <div className="silhouette-sleeve right" />
        </div>
      )}
      <span className="npc-nameplate">{character.name}</span>
    </div>
  );
}
