import * as Phaser from 'phaser';

import type { PhaserStageUpdate } from './events';
import { MainScene } from './scenes/MainScene';

export function createPhaserGame(container: HTMLElement, initialPayload: PhaserStageUpdate): Phaser.Game {
  return new Phaser.Game({
    type: Phaser.AUTO,
    parent: container,
    width: container.clientWidth || 1280,
    height: container.clientHeight || 720,
    backgroundColor: '#09080b',
    render: {
      antialias: true,
      transparent: true,
    },
    scale: {
      mode: Phaser.Scale.RESIZE,
      autoCenter: Phaser.Scale.CENTER_BOTH,
    },
    loader: {
      imageLoadType: 'HTMLImageElement',
    },
    callbacks: {
      preBoot: (game) => {
        game.registry.set('stagePayload', initialPayload);
      },
    },
    scene: [MainScene],
  });
}
