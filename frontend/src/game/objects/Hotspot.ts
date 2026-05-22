import * as Phaser from 'phaser';

import { stageEvents, type HotspotClickPayload } from '../events';
import type { SceneHotspot } from '../../types/game';

type HotspotOptions = {
  sceneId: string;
  hotspot: SceneHotspot;
  disabled: boolean;
};

const hotspotTextResolution = typeof window === 'undefined'
  ? 1.5
  : Math.min(Math.max(window.devicePixelRatio || 1, 1.5), 2);

export class Hotspot extends Phaser.GameObjects.Container {
  readonly hotspotId: string;
  readonly clueIds: string[];

  private readonly halo: Phaser.GameObjects.Graphics;
  private readonly ring: Phaser.GameObjects.Graphics;
  private readonly hitZone: Phaser.GameObjects.Zone;
  private readonly labelPlate: Phaser.GameObjects.Rectangle;
  private readonly labelText: Phaser.GameObjects.Text;
  private disabled: boolean;
  private hovered = false;
  private destroyed = false;

  constructor(scene: Phaser.Scene, x: number, y: number, options: HotspotOptions) {
    super(scene, x, y);

    this.hotspotId = options.hotspot.hotspot_id;
    this.clueIds = options.hotspot.clue_ids;
    this.disabled = options.disabled;

    this.halo = scene.add.graphics();
    this.ring = scene.add.graphics();
    this.labelText = scene.add.text(0, -38, options.hotspot.label, {
      color: '#f5dfbd',
      fontFamily: '"KaiTi", "STKaiti", "KaiTi SC", "LXGW WenKai", "FangSong", "Songti SC", serif',
      fontSize: '17px',
      fontStyle: 'bold',
      align: 'center',
      stroke: '#2b160f',
      strokeThickness: 3,
      shadow: { offsetX: 0, offsetY: 2, color: '#000000', blur: 0, stroke: true, fill: true },
      resolution: hotspotTextResolution,
      wordWrap: { width: 126 },
    }).setOrigin(0.5);

    const labelWidth = Math.max(142, this.labelText.width + 28);
    const labelHeight = Math.max(34, this.labelText.height + 12);
    this.labelPlate = scene.add.rectangle(0, -38, labelWidth, labelHeight, 0x140d0b, 0.78);
    this.labelPlate.setStrokeStyle(1, 0xd2a05f, 0.46);
    const hitRadius = 28;
    const hitPadding = 10;
    const hitTop = Math.min(-hitRadius, this.labelPlate.y - labelHeight / 2) - hitPadding;
    const hitBottom = Math.max(hitRadius, this.labelPlate.y + labelHeight / 2) + hitPadding;
    const hitWidth = Math.max(labelWidth, hitRadius * 2) + hitPadding * 2;
    const hitHeight = hitBottom - hitTop;
    const hitY = (hitTop + hitBottom) / 2;
    this.hitZone = scene.add.zone(0, hitY, hitWidth, hitHeight).setOrigin(0.5);
    this.hitZone.setInteractive({ useHandCursor: true });

    this.add([this.halo, this.ring, this.labelPlate, this.labelText, this.hitZone]);
    this.setSize(hitWidth, hitHeight);
    this.setDepth(30);

    this.hitZone.on('pointerover', () => this.setHoverState(true));
    this.hitZone.on('pointerout', () => this.setHoverState(false));
    this.hitZone.on('pointerdown', () => {
      if (this.disabled) {
        return;
      }
      const payload: HotspotClickPayload = {
        sceneId: options.sceneId,
        hotspotId: options.hotspot.hotspot_id,
        clueId: options.hotspot.clue_ids[0] ?? null,
        label: options.hotspot.label,
      };
      this.scene.game.events.emit(stageEvents.hotspotClicked, payload);
    });
    this.once('destroy', () => {
      this.destroyed = true;
    });

    this.redraw(false);
    this.setDisabled(options.disabled);
    scene.add.existing(this);
  }

  setDisabled(disabled: boolean): void {
    this.disabled = disabled;
    if (disabled) {
      this.hovered = false;
      this.scene.tweens.killTweensOf(this);
      this.setScale(1);
      this.redraw(false);
      this.hitZone.disableInteractive();
    } else if (!this.hitZone.input?.enabled) {
      this.hitZone.setInteractive({ useHandCursor: true });
    }
    this.setAlpha(disabled ? 0.58 : 1);
    this.labelText.setAlpha(disabled ? 0.7 : 1);
  }

  playDiscoveryPulse(): void {
    if (this.destroyed) {
      return;
    }
    this.redraw(true);
    this.scene.tweens.add({
      targets: this,
      scale: { from: 1.08, to: 1 },
      duration: 360,
      ease: 'Back.easeOut',
      onComplete: () => this.redrawIfAlive(this.hovered),
    });
  }

  private setHoverState(hovered: boolean): void {
    if (this.disabled || this.destroyed || this.hovered === hovered) {
      return;
    }
    this.hovered = hovered;
    this.redraw(hovered);
    this.scene.tweens.killTweensOf(this);
    this.scene.tweens.add({
      targets: this,
      scale: hovered ? 1.06 : 1,
      duration: hovered ? 140 : 160,
      ease: 'Sine.easeOut',
    });
  }

  private redrawIfAlive(active: boolean): void {
    if (this.destroyed || !this.active) {
      return;
    }
    this.redraw(active);
  }

  private redraw(active: boolean): void {
    if (this.destroyed) {
      return;
    }
    this.halo.clear();
    this.halo.fillStyle(active ? 0xe07163 : 0xc9a063, active ? 0.22 : 0.1);
    this.halo.fillCircle(0, 0, active ? 24 : 18);

    this.ring.clear();
    this.ring.lineStyle(active ? 3 : 2, active ? 0xffd1a0 : 0xd2a05f, active ? 0.88 : 0.62);
    this.ring.strokeCircle(0, 0, active ? 19 : 14);
    this.ring.lineStyle(1, 0x7c2b25, 0.86);
    this.ring.strokeCircle(0, 0, 5);
  }
}
