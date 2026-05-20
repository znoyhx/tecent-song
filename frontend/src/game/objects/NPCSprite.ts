import * as Phaser from 'phaser';

import { stageEvents, type NpcClickPayload } from '../events';
import type { NPCProfile } from '../../types/game';

type NpcSpriteOptions = {
  npc: NPCProfile;
  imageKey?: string;
  active: boolean;
  disabled: boolean;
  maxWidth: number;
  maxHeight: number;
};

export class NPCSprite extends Phaser.GameObjects.Container {
  readonly npcId: string;

  private readonly npc: NPCProfile;
  private readonly glow: Phaser.GameObjects.Graphics;
  private portrait?: Phaser.GameObjects.Image;
  private disabled: boolean;
  private selected: boolean;
  private maxWidth: number;
  private maxHeight: number;

  constructor(scene: Phaser.Scene, x: number, y: number, options: NpcSpriteOptions) {
    super(scene, x, y);

    this.npc = options.npc;
    this.npcId = options.npc.npc_id;
    this.disabled = options.disabled;
    this.selected = options.active;
    this.maxWidth = options.maxWidth;
    this.maxHeight = options.maxHeight;
    this.glow = scene.add.graphics();
    this.add(this.glow);

    this.setSize(this.maxWidth, this.maxHeight);
    this.setDepth(options.active ? 22 : 18);
    this.setInteractive(
      new Phaser.Geom.Rectangle(-this.maxWidth / 2, -this.maxHeight, this.maxWidth, this.maxHeight),
      Phaser.Geom.Rectangle.Contains,
    );
    this.on('pointerdown', () => {
      if (this.disabled) {
        return;
      }
      const payload: NpcClickPayload = { npcId: this.npcId };
      this.scene.game.events.emit(stageEvents.npcClicked, payload);
    });

    if (options.imageKey) {
      this.setImageKey(options.imageKey);
    } else {
      this.drawFallback();
    }
    this.setActiveState(options.active);
    this.setDisabled(options.disabled);
    scene.add.existing(this);
  }

  setImageKey(imageKey: string): void {
    this.removePortrait();
    const image = this.scene.add.image(0, 0, imageKey).setOrigin(0.5, 1);
    const scale = Math.min(this.maxWidth / Math.max(image.width, 1), this.maxHeight / Math.max(image.height, 1));
    image.setScale(scale);
    image.setTint(0xf3dfc4);
    const namePlate = this.scene.add.text(0, 8, this.npc.name, {
      color: '#fff0d2',
      fontFamily: '"LXGW WenKai", "STKaiti", "KaiTi", serif',
      fontSize: '18px',
      align: 'center',
      backgroundColor: 'rgba(24, 14, 12, 0.72)',
      padding: { x: 14, y: 6 },
    }).setOrigin(0.5, 1);
    this.portrait = image;
    this.addAt(image, 1);
    this.add(namePlate);
    this.setActiveState(this.selected);
  }

  setActiveState(active: boolean): void {
    this.selected = active;
    this.setDepth(active ? 22 : 18);
    this.glow.clear();
    this.glow.fillStyle(active ? 0xd69d5f : 0x000000, active ? 0.2 : 0.08);
    this.glow.fillEllipse(0, -this.maxHeight * 0.34, this.maxWidth * (active ? 0.88 : 0.68), this.maxHeight * 0.82);
    this.glow.lineStyle(active ? 3 : 1, active ? 0xffd5a8 : 0x6d4a34, active ? 0.62 : 0.24);
    this.glow.strokeEllipse(0, -this.maxHeight * 0.35, this.maxWidth * (active ? 0.9 : 0.7), this.maxHeight * 0.84);
    this.setAlpha(active ? 1 : 0.78);
    if (this.portrait) {
      this.portrait.clearTint();
      if (!active) {
        this.portrait.setTint(0xb99c7a);
      }
    }
  }

  setDisabled(disabled: boolean): void {
    this.disabled = disabled;
    this.setAlpha(disabled ? 0.52 : this.selected ? 1 : 0.78);
  }

  private drawFallback(): void {
    this.removePortrait();
    const body = this.scene.add.graphics();
    body.fillStyle(0x120f10, 0.9);
    body.fillEllipse(0, -this.maxHeight * 0.48, this.maxWidth * 0.38, this.maxHeight * 0.7);
    body.fillStyle(0x1e1714, 0.96);
    body.fillRoundedRect(-this.maxWidth * 0.26, -this.maxHeight * 0.58, this.maxWidth * 0.52, this.maxHeight * 0.52, 70);
    body.fillStyle(0x0b0909, 1);
    body.fillCircle(0, -this.maxHeight * 0.78, this.maxWidth * 0.12);
    body.lineStyle(2, 0xc9a063, 0.18);
    body.strokeEllipse(0, -this.maxHeight * 0.48, this.maxWidth * 0.42, this.maxHeight * 0.72);

    const nameSeal = this.scene.add.text(0, -this.maxHeight * 0.54, this.npc.name, {
      color: '#d8bd92',
      fontFamily: '"LXGW WenKai", "STKaiti", "KaiTi", serif',
      fontSize: '28px',
      align: 'center',
    }).setOrigin(0.5);

    const namePlate = this.scene.add.text(0, 8, this.npc.name, {
      color: '#fff0d2',
      fontFamily: '"LXGW WenKai", "STKaiti", "KaiTi", serif',
      fontSize: '18px',
      align: 'center',
      backgroundColor: 'rgba(24, 14, 12, 0.72)',
      padding: { x: 14, y: 6 },
    }).setOrigin(0.5, 1);

    this.add([body, nameSeal, namePlate]);
  }

  private removePortrait(): void {
    if (this.portrait) {
      this.portrait.destroy();
      this.portrait = undefined;
    }
    this.removeBetween(1, this.length, true);
  }
}
