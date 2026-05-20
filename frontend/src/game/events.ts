import type { SessionSnapshot } from '../types/game';

export const stageEvents = {
  snapshotUpdate: 'snapshot:update',
  hotspotClicked: 'hotspot:clicked',
  npcClicked: 'npc:clicked',
} as const;

export type PhaserStageUpdate = {
  snapshot: SessionSnapshot;
  selectedNpcId: string | null;
  busy: boolean;
};

export type HotspotClickPayload = {
  sceneId: string;
  hotspotId: string;
  clueId?: string | null;
  label: string;
};

export type NpcClickPayload = {
  npcId: string;
};
