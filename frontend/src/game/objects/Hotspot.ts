import * as Phaser from 'phaser';

import { stageEvents, type HotspotClickPayload } from '../events';
import type { SceneHotspot } from '../../types/game';

type HotspotOptions = {
  sceneId: string;
  hotspot: SceneHotspot;
  disabled: boolean;
};

export class Hotspot extends Phaser.GameObjects.Container {
  readonly hotspotId: string;
  readonly clueIds: string[];

  private readonly halo: Phaser.GameObjects.Graphics;
  private readonly ring: Phaser.GameObjects.Graphics;
  private readonly labelPlate: Phaser.GameObjects.Rectangle;
  private readonly labelText: Phaser.GameObjects.Text;
  private disabled: boolean;
  private destroyed = false;

  constructor(scene: Phaser.Scene, x: number, y: number, options: HotspotOptions) {
    super(scene, x, y);

    this.hotspotId = options.hotspot.hotspot_id;
    this.clueIds = options.hotspot.clue_ids;
    this.disabled = options.disabled;

    this.halo = scene.add.graphics();
    this.ring = scene.add.graphics();
    this.labelPlate = scene.add.rectangle(0, 34, 138, 34, 0x140d0b, 0.72);
    this.labelText = scene.add.text(0, 34, options.hotspot.label, {
      color: '#f5dfbd',
      fontFamily: '"LXGW WenKai", "STKaiti", "KaiTi", serif',
      fontSize: '17px',
      align: 'center',
      wordWrap: { width: 126 },
    }).setOrigin(0.5);

    this.labelPlate.setStrokeStyle(1, 0xd2a05f, 0.32);
    this.add([this.halo, this.ring, this.labelPlate, this.labelText]);
    this.setSize(150, 86);
    this.setDepth(30);
    this.setInteractive(
      new Phaser.Geom.Rectangle(-75, -34, 150, 86),
      Phaser.Geom.Rectangle.Contains,
    );

    this.on('pointerover', () => {
      if (!this.disabled) {
        this.scene.tweens.add({ targets: this, scale: 1.06, duration: 140, ease: 'Sine.easeOut' });
      }
    });
    this.on('pointerout', () => {
      if (!this.disabled) {
        this.scene.tweens.add({ targets: this, scale: 1, duration: 160, ease: 'Sine.easeOut' });
      }
    });
    this.on('pointerdown', () => {
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
      onComplete: () => this.redrawIfAlive(false),
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
    this.halo.fillStyle(active ? 0xe07163 : 0xc9a063, active ? 0.26 : 0.12);
    this.halo.fillCircle(0, 0, active ? 28 : 22);

    this.ring.clear();
    this.ring.lineStyle(active ? 3 : 2, active ? 0xffd1a0 : 0xd2a05f, active ? 0.9 : 0.66);
    this.ring.strokeCircle(0, 0, active ? 22 : 17);
    this.ring.lineStyle(1, 0x7c2b25, 0.86);
    this.ring.strokeCircle(0, 0, 6);
  }
}
