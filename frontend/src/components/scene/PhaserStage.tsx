import { useEffect, useRef } from 'react';
import type * as Phaser from 'phaser';

import { createPhaserGame } from '../../game/phaserGame';
import { stageEvents, type HotspotClickPayload, type NpcClickPayload } from '../../game/events';
import type { SessionSnapshot } from '../../types/game';

type PhaserStageProps = {
  snapshot: SessionSnapshot;
  selectedNpcId: string | null;
  busy: boolean;
  onSelectNpc: (npcId: string) => void;
  onInspect: (sceneId: string, hotspotId: string, clueId?: string | null) => void;
};

export function PhaserStage({ snapshot, selectedNpcId, busy, onSelectNpc, onInspect }: PhaserStageProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const gameRef = useRef<Phaser.Game | null>(null);
  const latestBridgeRef = useRef({ busy, onInspect, onSelectNpc });
  latestBridgeRef.current = { busy, onInspect, onSelectNpc };

  useEffect(() => {
    const container = containerRef.current;
    if (!container || gameRef.current) {
      return undefined;
    }

    const game = createPhaserGame(container, { snapshot, selectedNpcId, busy });
    gameRef.current = game;

    const handleHotspotClicked = (payload: HotspotClickPayload) => {
      const bridge = latestBridgeRef.current;
      if (bridge.busy) {
        return;
      }
      bridge.onInspect(payload.sceneId, payload.hotspotId, payload.clueId ?? null);
    };

    const handleNpcClicked = (payload: NpcClickPayload) => {
      const bridge = latestBridgeRef.current;
      if (bridge.busy) {
        return;
      }
      bridge.onSelectNpc(payload.npcId);
    };

    game.events.on(stageEvents.hotspotClicked, handleHotspotClicked);
    game.events.on(stageEvents.npcClicked, handleNpcClicked);

    return () => {
      game.events.off(stageEvents.hotspotClicked, handleHotspotClicked);
      game.events.off(stageEvents.npcClicked, handleNpcClicked);
      game.destroy(true);
      gameRef.current = null;
    };
  }, []);

  useEffect(() => {
    gameRef.current?.events.emit(stageEvents.snapshotUpdate, { snapshot, selectedNpcId, busy });
  }, [snapshot, selectedNpcId, busy]);

  return (
    <section className="phaser-stage-shell" aria-label="可交互叙事舞台">
      <div ref={containerRef} className="phaser-stage-canvas" />
    </section>
  );
}
