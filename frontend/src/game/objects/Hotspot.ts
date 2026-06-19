import * as Phaser from 'phaser';

import { stageEvents, type HotspotClickPayload } from '../events';
import type { SceneHotspot } from '../../types/game';

type HotspotOptions = {
  sceneId: string;
  hotspot: SceneHotspot;
  disabled: boolean;
  hitWidth?: number;
  hitHeight?: number;
  visualWidth?: number;
  visualHeight?: number;
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
  private readonly hitWidth: number;
  private readonly hitHeight: number;
  private readonly visualWidth: number;
  private readonly visualHeight: number;
  private disabled: boolean;
  private hovered = false;
  private destroyed = false;

  constructor(scene: Phaser.Scene, x: number, y: number, options: HotspotOptions) {
    super(scene, x, y);

    this.hotspotId = options.hotspot.hotspot_id;
    this.clueIds = options.hotspot.clue_ids;
    this.disabled = options.disabled;
    this.hitWidth = Math.max(options.hitWidth ?? 132, 96);
    this.hitHeight = Math.max(options.hitHeight ?? 78, 58);
    this.visualWidth = Math.max(options.visualWidth ?? 116, 86);
    this.visualHeight = Math.max(options.visualHeight ?? 62, 48);

    this.halo = scene.add.graphics();
    this.ring = scene.add.graphics();
    this.labelText = scene.add.text(0, -38, options.hotspot.label, {
      color: '#f5dfbd',
      fontFamily: '"KaiTi", "STKaiti", "KaiTi SC", "LXGW WenKai", "FangSong", "Songti SC", serif',
      fontSize: '18px',
      fontStyle: 'bold',
      align: 'center',
      stroke: '#2b160f',
      strokeThickness: 3,
      shadow: { offsetX: 0, offsetY: 2, color: '#000000', blur: 0, stroke: true, fill: true },
      resolution: hotspotTextResolution,
      wordWrap: { width: 156 },
    }).setOrigin(0.5);

    const labelWidth = Math.max(116, this.labelText.width + 28);
    const labelHeight = Math.max(38, this.labelText.height + 14);
    this.labelPlate = scene.add.rectangle(0, -38, labelWidth, labelHeight, 0x140d0b, 0.78);
    this.labelPlate.setStrokeStyle(1, 0xd2a05f, 0.46);
    this.labelPlate.setAlpha(0);
    this.labelText.setAlpha(0);
    this.hitZone = scene.add.zone(0, 0, this.hitWidth, this.hitHeight).setOrigin(0.5);
    this.hitZone.setInteractive({ useHandCursor: true });

    this.add([this.halo, this.ring, this.labelPlate, this.labelText, this.hitZone]);
    this.setSize(this.hitWidth, this.hitHeight);
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
    this.setAlpha(disabled ? 0.5 : 1);
    if (disabled) {
      this.labelPlate.setAlpha(0);
      this.labelText.setAlpha(0);
    }
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
    this.ring.clear();
    if (!active) {
      const width = Math.min(this.visualWidth, 126);
      const height = Math.min(this.visualHeight, 74);
      this.halo.fillStyle(0xd9b16e, 0.14);
      this.halo.fillRoundedRect(-width / 2, -height / 2, width, height, 10);
      this.ring.lineStyle(2, 0xf2d6a8, 0.48);
      this.ring.strokeRoundedRect(-width / 2, -height / 2, width, height, 10);
      this.ring.fillStyle(0xffd7a3, 0.88);
      this.ring.fillCircle(0, 0, 5.5);
      this.labelPlate.setAlpha(0.68);
      this.labelText.setAlpha(1);
      return;
    }

    const width = this.visualWidth;
    const height = this.visualHeight;
    this.halo.fillStyle(0xd9b16e, 0.08);
    this.halo.fillRoundedRect(-width / 2, -height / 2, width, height, 10);
    this.ring.lineStyle(2, 0xf2d6a8, 0.42);
    this.ring.strokeRoundedRect(-width / 2, -height / 2, width, height, 10);
    this.ring.lineStyle(1, 0x6e2d28, 0.3);
    this.ring.strokeRoundedRect(-width / 2 + 4, -height / 2 + 4, width - 8, height - 8, 8);
    this.labelPlate.setAlpha(0.74);
    this.labelText.setAlpha(1);
  }
}
