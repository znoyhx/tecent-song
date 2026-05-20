import { useEffect, useMemo, useRef } from 'react';
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

  const stageTags = useMemo(
    () => [
      ['朝代', snapshot.dynasty?.name ?? '明代'],
      ['身份', snapshot.player_identity?.display_name ?? snapshot.player_role?.name ?? '书坊学徒'],
      ['地点', snapshot.scene.name],
      ['阶段', snapshot.stage_label],
    ],
    [snapshot.dynasty?.name, snapshot.player_identity?.display_name, snapshot.player_role?.name, snapshot.scene.name, snapshot.stage_label],
  );

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
      <header className="top-hud phaser-stage-hud">
        {stageTags.map(([label, value]) => (
          <div key={label} className="hud-chip">
            <span>{label}</span>
            <strong>{value}</strong>
          </div>
        ))}
        <div className="hud-goal">目标：{snapshot.current_goal}</div>
      </header>
      <div className="scene-corner-caption phaser-stage-caption">
        <strong>{snapshot.scene.name}</strong>
        <span>{snapshot.scene.visual_status === 'generated' ? '已生成场景' : '视觉占位场景'}</span>
      </div>
    </section>
  );
}
