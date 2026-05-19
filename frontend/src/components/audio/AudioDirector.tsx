import { useEffect, useMemo, useRef, useState } from 'react';

import { resolveApiUrl } from '../../api/client';
import { selectBgmId } from '../../store/musicSelector';
import type { SessionSnapshot } from '../../types/game';
import type { BgmTrack, MusicManifest, MusicSettings } from '../../types/music';

type AudioDirectorProps = {
  snapshot: SessionSnapshot | null;
  selectedNpcId: string | null;
};

const storageKey = 'historyGameMusicSettings';

const defaultSettings: MusicSettings = {
  enabled: true,
  muted: false,
  volume: 0.48,
  decided: true,
};

function readSettings(): MusicSettings {
  if (typeof window === 'undefined') {
    return defaultSettings;
  }
  try {
    window.localStorage.getItem(storageKey);
    return {
      enabled: true,
      muted: false,
      volume: defaultSettings.volume,
      decided: true,
    };
  } catch {
    return defaultSettings;
  }
}

function clampVolume(value: number): number {
  return Math.max(0, Math.min(0.75, value));
}

function effectiveVolume(track: BgmTrack, masterVolume: number): number {
  return clampVolume(masterVolume * (track.volume / 0.35));
}

function stopAudio(audio: HTMLAudioElement | null) {
  if (!audio) {
    return;
  }
  audio.pause();
  audio.src = '';
  audio.load();
}

export function AudioDirector({ snapshot, selectedNpcId }: AudioDirectorProps) {
  const [manifest, setManifest] = useState<MusicManifest | null>(null);
  const [settings] = useState(readSettings);
  const [hasGesture, setHasGesture] = useState(false);
  const activeAudioRef = useRef<HTMLAudioElement | null>(null);
  const currentTrackIdRef = useRef('');
  const fadeTimerRef = useRef<number | null>(null);
  const delayedSwitchRef = useRef<number | null>(null);
  const lastSwitchAtRef = useRef(0);

  const targetBgmId = useMemo(() => selectBgmId(snapshot, selectedNpcId), [snapshot, selectedNpcId]);
  const currentTrack = useMemo(
    () => manifest?.tracks.find((track) => track.bgm_id === targetBgmId) ?? null,
    [manifest, targetBgmId],
  );
  const playableFallbackTrack = useMemo(
    () => manifest?.tracks.find((track) => track.bgm_id === 'pre_game_entry' && track.asset_available) ?? null,
    [manifest],
  );
  const sourceTrack = currentTrack?.asset_available ? currentTrack : playableFallbackTrack ?? currentTrack;

  useEffect(() => {
    try {
      window.localStorage.setItem(storageKey, JSON.stringify(settings));
    } catch {
      // localStorage 不可用时，只影响下次打开页面的音乐记忆。
    }
  }, [settings]);

  useEffect(() => {
    let cancelled = false;
    fetch(resolveApiUrl('/api/music/manifest'))
      .then((response) => {
        if (!response.ok) {
          throw new Error('manifest');
        }
        return response.json() as Promise<MusicManifest>;
      })
      .then((payload) => {
        if (!cancelled) {
          setManifest(payload);
        }
      })
      .catch(() => {
        // 音乐失败不能打断游戏；隐藏导演保持静默。
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    const unlock = () => {
      setHasGesture(true);
    };
    window.addEventListener('pointerdown', unlock, { once: true, capture: true });
    window.addEventListener('keydown', unlock, { once: true, capture: true });
    return () => {
      window.removeEventListener('pointerdown', unlock, { capture: true });
      window.removeEventListener('keydown', unlock, { capture: true });
    };
  }, []);

  useEffect(() => {
    return () => {
      if (fadeTimerRef.current) {
        window.clearInterval(fadeTimerRef.current);
      }
      if (delayedSwitchRef.current) {
        window.clearTimeout(delayedSwitchRef.current);
      }
      stopAudio(activeAudioRef.current);
    };
  }, []);

  useEffect(() => {
    if (delayedSwitchRef.current) {
      window.clearTimeout(delayedSwitchRef.current);
      delayedSwitchRef.current = null;
    }

    const fadeOutAndPause = () => {
      const audio = activeAudioRef.current;
      if (!audio) {
        return;
      }
      if (fadeTimerRef.current) {
        window.clearInterval(fadeTimerRef.current);
      }
      const startVolume = audio.volume;
      const startedAt = performance.now();
      fadeTimerRef.current = window.setInterval(() => {
        const progress = Math.min(1, (performance.now() - startedAt) / 420);
        audio.volume = startVolume * (1 - progress);
        if (progress >= 1) {
          if (fadeTimerRef.current) {
            window.clearInterval(fadeTimerRef.current);
          }
          audio.pause();
        }
      }, 40);
    };

    if (!sourceTrack || !settings.enabled || settings.muted || !hasGesture) {
      fadeOutAndPause();
      return;
    }

    const currentAudio = activeAudioRef.current;
    const nextVolume = effectiveVolume(sourceTrack, settings.volume);
    if (currentTrackIdRef.current === sourceTrack.bgm_id && currentAudio) {
      currentAudio.volume = nextVolume;
      return;
    }

    const switchTrack = () => {
      const sourceWasFallback = !sourceTrack.asset_available;
      const nextAudio = new Audio(resolveApiUrl(sourceWasFallback ? sourceTrack.fallback_url : sourceTrack.asset_url));
      nextAudio.loop = true;
      nextAudio.preload = 'auto';
      nextAudio.volume = 0;
      let fallbackLoaded = sourceWasFallback;
      nextAudio.addEventListener('error', () => {
        if (!fallbackLoaded) {
          fallbackLoaded = true;
          nextAudio.src = resolveApiUrl(sourceTrack.fallback_url);
          nextAudio.load();
          void nextAudio.play().catch(() => undefined);
          return;
        }
      });

      void nextAudio.play().catch(() => undefined);

      const previousAudio = activeAudioRef.current;
      activeAudioRef.current = nextAudio;
      currentTrackIdRef.current = sourceTrack.bgm_id;
      lastSwitchAtRef.current = Date.now();

      if (fadeTimerRef.current) {
        window.clearInterval(fadeTimerRef.current);
      }
      const previousStartVolume = previousAudio?.volume ?? 0;
      const fadeMs = Math.max(1200, Math.min(2500, sourceTrack.fade_ms || 1800));
      const startedAt = performance.now();
      fadeTimerRef.current = window.setInterval(() => {
        const progress = Math.min(1, (performance.now() - startedAt) / fadeMs);
        nextAudio.volume = nextVolume * progress;
        if (previousAudio) {
          previousAudio.volume = previousStartVolume * (1 - progress);
        }
        if (progress >= 1) {
          if (fadeTimerRef.current) {
            window.clearInterval(fadeTimerRef.current);
          }
          stopAudio(previousAudio);
        }
      }, 50);
    };

    const elapsed = Date.now() - lastSwitchAtRef.current;
    const isNpcTrack = targetBgmId.startsWith('ming_npc_');
    if (isNpcTrack && currentTrackIdRef.current && elapsed < 1800) {
      delayedSwitchRef.current = window.setTimeout(switchTrack, 1800 - elapsed);
      return;
    }
    switchTrack();
  }, [sourceTrack, hasGesture, settings.enabled, settings.muted, settings.volume, targetBgmId]);

  return null;
}
