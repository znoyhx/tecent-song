import * as Phaser from 'phaser';

import { resolveApiUrl } from '../../api/client';
import type { NPCProfile, Scene, SessionSnapshot } from '../../types/game';
import { stageEvents, type HotspotClickPayload, type PhaserStageUpdate } from '../events';
import { Hotspot } from '../objects/Hotspot';
import { NPCSprite } from '../objects/NPCSprite';

type StagePoint = { x: number; y: number };
type ImageSize = { width: number; height: number };

const defaultImageSize: ImageSize = { width: 1024, height: 1024 };

const hotspotSlots: StagePoint[] = [
  { x: 0.18, y: 0.4 },
  { x: 0.42, y: 0.48 },
  { x: 0.68, y: 0.44 },
  { x: 0.82, y: 0.58 },
  { x: 0.28, y: 0.64 },
  { x: 0.56, y: 0.66 },
  { x: 0.76, y: 0.34 },
];

const hotspotPositionMap: Record<string, Record<string, StagePoint>> = {
  scene_front_hall: {
    ledger_desk: { x: 0.82, y: 0.56 },
    old_box: { x: 0.2, y: 0.52 },
    apprentice_watch: { x: 0.1, y: 0.48 },
  },
  scene_account_room: {
    torn_ledger_line: { x: 0.31, y: 0.62 },
    deposit_receipt: { x: 0.72, y: 0.59 },
    locked_inner_drawer: { x: 0.81, y: 0.53 },
    account_ash: { x: 0.12, y: 0.63 },
  },
  scene_fire_yard: {
    ash_pile: { x: 0.46, y: 0.54 },
    char_mark: { x: 0.72, y: 0.48 },
    scorched_box_bottom: { x: 0.72, y: 0.61 },
    fire_bucket: { x: 0.28, y: 0.58 },
  },
  scene_lamp_shelf: {
    oil_jar: { x: 0.18, y: 0.6 },
    rain_tracks: { x: 0.62, y: 0.56 },
    moved_lamp_stand: { x: 0.38, y: 0.58 },
  },
  scene_engraving_room: {
    back_door: { x: 0.2, y: 0.57 },
    carved_board: { x: 0.82, y: 0.58 },
    ink_rag: { x: 0.51, y: 0.59 },
  },
  scene_back_gate: {
    mud_scrape: { x: 0.48, y: 0.62 },
    gate_latch: { x: 0.86, y: 0.46 },
    hidden_thread: { x: 0.37, y: 0.32 },
  },
  scene_rain_alley: {
    search_notice: { x: 0.2, y: 0.43 },
    muddy_hem: { x: 0.5, y: 0.58 },
    late_visitor_memory: { x: 0.68, y: 0.45 },
  },
  scene_city_gate: {
    second_notice: { x: 0.18, y: 0.47 },
    grain_term: { x: 0.52, y: 0.34 },
    outer_wrapper: { x: 0.7, y: 0.55 },
  },
  scene_interrogation_room: {
    sealed_desk: { x: 0.15, y: 0.39 },
    order_conflict_note: { x: 0.84, y: 0.3 },
    temp_record: { x: 0.82, y: 0.49 },
    search_list: { x: 0.16, y: 0.5 },
  },
};

const npcPositionMap: Record<string, Record<string, StagePoint>> = {
  scene_front_hall: {
    npc_owner: { x: 0.58, y: 0.88 },
  },
  scene_account_room: {
    npc_owner: { x: 0.58, y: 0.9 },
  },
  scene_engraving_room: {
    npc_worker: { x: 0.52, y: 0.88 },
  },
  scene_back_gate: {
    npc_worker: { x: 0.5, y: 0.83 },
  },
  scene_rain_alley: {
    npc_scholar: { x: 0.5, y: 0.86 },
  },
  scene_city_gate: {
    npc_scholar: { x: 0.7, y: 0.86 },
  },
  scene_interrogation_room: {
    npc_jinyiwei: { x: 0.5, y: 0.9 },
  },
};

function hashText(value: string): string {
  let hash = 0;
  for (let index = 0; index < value.length; index += 1) {
    hash = (hash * 31 + value.charCodeAt(index)) >>> 0;
  }
  return hash.toString(36);
}

function fitCover(image: Phaser.GameObjects.Image, width: number, height: number): void {
  const scale = Math.max(width / Math.max(image.width, 1), height / Math.max(image.height, 1));
  image.setPosition(width / 2, height / 2).setScale(scale);
}

function imagePointToCanvas(point: StagePoint, width: number, height: number, sourceSize: ImageSize): StagePoint {
  const sourceWidth = Math.max(sourceSize.width, 1);
  const sourceHeight = Math.max(sourceSize.height, 1);
  const scale = Math.max(width / sourceWidth, height / sourceHeight);
  const renderedWidth = sourceWidth * scale;
  const renderedHeight = sourceHeight * scale;
  return {
    x: (width - renderedWidth) / 2 + point.x * renderedWidth,
    y: (height - renderedHeight) / 2 + point.y * renderedHeight,
  };
}

function resolveSceneImage(scene: Scene): string {
  return resolveApiUrl(
    scene.visual_asset_url,
    scene.visual_asset_id ? `/api/visual/assets/${scene.visual_asset_id}` : '/api/visual/assets/scene_bookshop_front_hall',
  );
}

function resolveNpcImage(npc: NPCProfile): string {
  const directUrl = npc.portraitUrl ?? npc.fallbackPortraitUrl ?? npc.imageUrl ?? npc.avatarUrl;
  if (directUrl) {
    return resolveApiUrl(directUrl);
  }
  if (npc.visual_asset_url) {
    return resolveApiUrl(npc.visual_asset_url);
  }
  if (npc.visual_asset_id) {
    return resolveApiUrl(`/api/visual/assets/${npc.visual_asset_id}`);
  }
  return '';
}

function calibratedHotspotPoint(hotspot: Scene['hotspots'][number]): StagePoint | null {
  const point = hotspot.anchor_point;
  if (!point || hotspot.calibration_status !== 'approved') {
    return null;
  }
  if (point.x < 0 || point.x > 1 || point.y < 0 || point.y > 1) {
    return null;
  }
  return { x: point.x, y: point.y };
}

export class MainScene extends Phaser.Scene {
  private payload?: PhaserStageUpdate;
  private backgroundLayer?: Phaser.GameObjects.Container;
  private ambientLayer?: Phaser.GameObjects.Container;
  private characterLayer?: Phaser.GameObjects.Container;
  private hotspotLayer?: Phaser.GameObjects.Container;
  private transitionLayer?: Phaser.GameObjects.Container;
  private hotspotObjects = new Map<string, Hotspot>();
  private npcObjects = new Map<string, NPCSprite>();
  private previousSceneId = '';
  private previousClueIds = new Set<string>();
  private renderToken = 0;
  private ambientTweenTargets: Phaser.GameObjects.GameObject[] = [];
  private backgroundImageSize: ImageSize = defaultImageSize;

  constructor() {
    super('MainScene');
  }

  create(): void {
    this.backgroundLayer = this.add.container(0, 0).setDepth(0);
    this.ambientLayer = this.add.container(0, 0).setDepth(6);
    this.characterLayer = this.add.container(0, 0).setDepth(12);
    this.hotspotLayer = this.add.container(0, 0).setDepth(20);
    this.transitionLayer = this.add.container(0, 0).setDepth(80);

    this.game.events.on(stageEvents.snapshotUpdate, this.handleSnapshotUpdate, this);
    this.game.events.on(stageEvents.hotspotClicked, this.handleHotspotClicked, this);
    this.scale.on('resize', this.handleResize, this);
    this.events.once('shutdown', this.cleanup, this);
    this.events.once('destroy', this.cleanup, this);

    const initialPayload = this.registry.get('stagePayload') as PhaserStageUpdate | undefined;
    if (initialPayload) {
      this.handleSnapshotUpdate(initialPayload);
    }
  }

  private handleSnapshotUpdate(payload: PhaserStageUpdate): void {
    const nextClueIds = new Set(payload.snapshot.state.discovered_clue_ids);
    const newClueIds = [...nextClueIds].filter((clueId) => !this.previousClueIds.has(clueId));
    const sceneChanged = this.previousSceneId !== '' && this.previousSceneId !== payload.snapshot.scene.scene_id;
    const initialRender = this.previousSceneId === '';

    this.payload = payload;
    this.renderStage(payload);

    if (sceneChanged || initialRender) {
      this.playSceneTransition();
    }
    if (!initialRender && newClueIds.length > 0) {
      this.playClueFeedback(newClueIds);
    }

    this.previousSceneId = payload.snapshot.scene.scene_id;
    this.previousClueIds = nextClueIds;
  }

  private handleResize(): void {
    if (this.payload) {
      this.renderStage(this.payload);
    }
  }

  private handleHotspotClicked(payload: HotspotClickPayload): void {
    const hotspot = this.hotspotObjects.get(payload.hotspotId);
    if (!hotspot) {
      return;
    }
    this.playHotspotFeedback(hotspot.x, hotspot.y);
  }

  private renderStage(payload: PhaserStageUpdate): void {
    const token = this.renderToken + 1;
    this.renderToken = token;
    this.hotspotObjects.clear();
    this.npcObjects.clear();
    this.ambientTweenTargets.forEach((target) => this.tweens.killTweensOf(target));
    this.ambientTweenTargets = [];
    this.cameras.main.setZoom(1);
    this.clearLayer(this.backgroundLayer);
    this.clearLayer(this.ambientLayer);
    this.clearLayer(this.characterLayer);
    this.clearLayer(this.hotspotLayer);

    this.drawBackground(payload.snapshot.scene, token);
    this.drawAmbience();
    this.drawNpcs(payload.snapshot, payload.selectedNpcId, payload.busy, token);
    this.drawHotspots(payload.snapshot, payload.busy);
  }

  private drawBackground(scene: Scene, token: number): void {
    const width = this.scale.width;
    const height = this.scale.height;
    this.backgroundImageSize = defaultImageSize;
    const fallback = this.add.container(0, 0);
    const base = this.add.rectangle(width / 2, height / 2, width, height, 0x09080b, 1);
    const redShade = this.add.rectangle(width * 0.18, height * 0.72, width * 0.7, height * 0.52, 0x4d1715, 0.26);
    const mistShade = this.add.rectangle(width * 0.82, height * 0.16, width * 0.5, height * 0.42, 0x2d3938, 0.18);
    const fallbackText = this.add.text(width / 2, height * 0.44, '视觉资产暂缺，雨火仍在。', {
      color: '#c9a982',
      fontFamily: '"LXGW WenKai", "STKaiti", "KaiTi", serif',
      fontSize: '20px',
      align: 'center',
    }).setOrigin(0.5);
    fallback.add([base, redShade, mistShade, fallbackText]);
    this.backgroundLayer?.add(fallback);

    const imageUrl = resolveSceneImage(scene);
    if (!imageUrl) {
      return;
    }

    const key = `scene-${scene.scene_id}-${hashText(imageUrl)}`;
    this.loadImageTexture(key, imageUrl, () => {
      if (this.renderToken !== token || !this.backgroundLayer) {
        return;
      }
      this.clearLayer(this.backgroundLayer);
      const image = this.add.image(0, 0, key).setOrigin(0.5);
      this.backgroundImageSize = {
        width: image.width || defaultImageSize.width,
        height: image.height || defaultImageSize.height,
      };
      fitCover(image, width, height);
      const overlay = this.add.rectangle(width / 2, height / 2, width, height, 0x080709, 0.08);
      const lowerShade = this.add.rectangle(width / 2, height * 0.86, width, height * 0.3, 0x080709, 0.18);
      const sideShade = this.add.rectangle(width * 0.52, height / 2, width, height, 0x020202, 0.04);
      this.backgroundLayer.add([image, overlay, sideShade, lowerShade]);
    });
  }

  private drawAmbience(): void {
    const width = this.scale.width;
    const height = this.scale.height;
    const rain = this.add.container(0, 0);
    for (let index = 0; index < 42; index += 1) {
      const line = this.add.rectangle(
        (index * 73) % Math.max(width, 1),
        (index * 41) % Math.max(height, 1),
        1,
        44,
        0xd2dede,
        0.16,
      ).setRotation(-0.42);
      rain.add(line);
    }
    const smoke = this.add.graphics();
    smoke.fillStyle(0xb69578, 0.12);
    smoke.fillEllipse(width * 0.5, height * 0.78, width * 0.82, height * 0.24);
    smoke.fillStyle(0x81342b, 0.16);
    smoke.fillCircle(width * 0.2, height * 0.75, Math.min(width, height) * 0.16);

    this.ambientLayer?.add([rain, smoke]);
    this.ambientTweenTargets = [rain, smoke];
    this.tweens.add({ targets: rain, x: -90, y: 130, duration: 9000, repeat: -1 });
    this.tweens.add({ targets: smoke, alpha: { from: 0.65, to: 1 }, y: -14, duration: 4200, yoyo: true, repeat: -1 });
  }

  private drawNpcs(snapshot: SessionSnapshot, selectedNpcId: string | null, busy: boolean, token: number): void {
    const width = this.scale.width;
    const height = this.scale.height;
    const count = snapshot.scene_npcs.length;
    if (count === 0) {
      return;
    }

    const maxHeight = Math.min(360, Math.max(220, height * 0.28));
    const maxWidth = Math.min(220, Math.max(148, width / Math.max(count + 5.4, 6.6)));
    const scenePlacements = npcPositionMap[snapshot.scene.scene_id] ?? {};

    snapshot.scene_npcs.forEach((npc, index) => {
      const fallback = count === 1
        ? { x: 0.56, y: 0.86 }
        : { x: 0.32 + (0.42 * index) / Math.max(count - 1, 1), y: 0.86 };
      const placement = scenePlacements[npc.npc_id] ?? fallback;
      const point = imagePointToCanvas(placement, width, height, this.backgroundImageSize);
      const x = Phaser.Math.Clamp(point.x, 44, width - 44);
      const y = Phaser.Math.Clamp(point.y, 120, height - 44);
      const active = npc.npc_id === selectedNpcId;
      const npcObject = new NPCSprite(this, x, y, {
        npc,
        active,
        disabled: busy,
        maxWidth,
        maxHeight,
        integratedScene: true,
      });
      this.npcObjects.set(npc.npc_id, npcObject);
      this.characterLayer?.add(npcObject);
    });
  }

  private drawHotspots(snapshot: SessionSnapshot, busy: boolean): void {
    const width = this.scale.width;
    const height = this.scale.height;
    const scenePositions = hotspotPositionMap[snapshot.scene.scene_id] ?? {};
    snapshot.scene.hotspots.forEach((hotspot, index) => {
      const slot = calibratedHotspotPoint(hotspot) ?? scenePositions[hotspot.hotspot_id] ?? hotspotSlots[index % hotspotSlots.length];
      const rowOffset = Math.floor(index / hotspotSlots.length) * 28;
      const point = imagePointToCanvas(slot, width, height, this.backgroundImageSize);
      const x = Phaser.Math.Clamp(point.x, 42, width - 42);
      const y = Phaser.Math.Clamp(point.y + rowOffset, 104, height - 84);
      const hotspotObject = new Hotspot(this, x, y, {
        sceneId: snapshot.scene.scene_id,
        hotspot,
        disabled: busy,
      });
      this.hotspotObjects.set(hotspot.hotspot_id, hotspotObject);
      this.hotspotLayer?.add(hotspotObject);
    });
  }

  private playSceneTransition(): void {
    const width = this.scale.width;
    const height = this.scale.height;
    const shade = this.add.rectangle(width / 2, height / 2, width, height, 0x050405, 0.92);
    this.transitionLayer?.add(shade);
    this.tweens.add({
      targets: shade,
      alpha: 0,
      duration: 620,
      ease: 'Sine.easeOut',
      onComplete: () => shade.destroy(),
    });
  }

  private playClueFeedback(newClueIds: string[]): void {
    this.cameras.main.shake(120, 0.0016);
    this.hotspotObjects.forEach((hotspot) => {
      if (hotspot.clueIds.some((clueId) => newClueIds.includes(clueId))) {
        hotspot.playDiscoveryPulse();
      }
    });
  }

  private playHotspotFeedback(x: number, y: number): void {
    const glow = this.add.circle(x, y, 28, 0xf2c177, 0.2);
    const ring = this.add.circle(x, y, 18, 0xf2c177, 0);
    ring.setStrokeStyle(2, 0xffd7a3, 0.78);
    this.transitionLayer?.add([glow, ring]);
    this.cameras.main.zoomTo(1.012, 110, 'Sine.easeOut');
    this.time.delayedCall(130, () => {
      this.cameras.main.zoomTo(1, 170, 'Sine.easeInOut');
    });
    this.tweens.add({
      targets: [glow, ring],
      scale: 2.1,
      alpha: 0,
      duration: 300,
      ease: 'Sine.easeOut',
      onComplete: () => {
        glow.destroy();
        ring.destroy();
      },
    });
  }

  private loadImageTexture(key: string, url: string, onLoaded: () => void): void {
    if (this.textures.exists(key)) {
      onLoaded();
      return;
    }
    this.load.once('complete', () => {
      if (this.textures.exists(key)) {
        onLoaded();
      }
    });
    this.load.image(key, url);
    if (!this.load.isLoading()) {
      this.load.start();
    }
  }

  private clearLayer(layer?: Phaser.GameObjects.Container): void {
    layer?.removeAll(true);
  }

  private cleanup(): void {
    this.game.events.off(stageEvents.snapshotUpdate, this.handleSnapshotUpdate, this);
    this.game.events.off(stageEvents.hotspotClicked, this.handleHotspotClicked, this);
    this.scale.off('resize', this.handleResize, this);
  }
}
