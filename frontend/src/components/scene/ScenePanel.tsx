import { resolveApiUrl } from '../../api/client';
import type { Scene, SessionSnapshot } from '../../types/game';
import { CharacterPortrait } from './CharacterPortrait';


type ScenePanelProps = {
  snapshot: SessionSnapshot;
  selectedNpcId: string | null;
  busy: boolean;
  onSelectNpc: (npcId: string) => void;
};

function getSceneImage(scene: Scene): string {
  return resolveApiUrl(scene.visual_asset_url, scene.visual_asset_id ? `/api/visual/assets/${scene.visual_asset_id}` : '/api/visual/assets/scene_bookshop_front_hall');
}



export function ScenePanel({ snapshot, selectedNpcId, busy, onSelectNpc }: ScenePanelProps) {
  const scene = snapshot.scene;
  const stageTags = [
    ['朝代', snapshot.dynasty?.name ?? '明代'],
    ['身份', snapshot.player_identity?.display_name ?? snapshot.player_role?.name ?? '书坊学徒'],
    ['地点', scene.name],
    ['阶段', snapshot.stage_label],
  ];

  return (
    <section
      className="vn-backdrop"
      style={{ backgroundImage: `linear-gradient(180deg, rgba(8, 7, 9, .22), rgba(8, 7, 9, .88)), url(${getSceneImage(scene)})` }}
    >
      <div className="vn-rain" />
      <div className="vn-smoke" />

      <header className="top-hud">
        {stageTags.map(([label, value]) => (
          <div key={label} className="hud-chip">
            <span>{label}</span>
            <strong>{value}</strong>
          </div>
        ))}
        <div className="hud-goal">目标：{snapshot.current_goal}</div>
      </header>

      <div className="npc-portrait-layer">
        {snapshot.scene_npcs.length > 0 ? (
          snapshot.scene_npcs.map((npc, index) => (
            <button
              key={npc.npc_id}
              type="button"
              className={npc.npc_id === selectedNpcId ? `npc-portrait-button active pos-${index}` : `npc-portrait-button pos-${index}`}
              onClick={() => onSelectNpc(npc.npc_id)}
              disabled={busy}
            >
              <CharacterPortrait character={npc} active={npc.npc_id === selectedNpcId} />
            </button>
          ))

        ) : (
          <div className="empty-stage-silhouette">
            <span>纸灰在雨里打旋，此处暂无人开口。</span>
          </div>
        )}
      </div>

      <div className="scene-corner-caption">
        <strong>{scene.name}</strong>
        <span>{scene.visual_status === 'generated' ? '已生成场景' : '视觉占位场景'}</span>

      </div>
    </section>
  );
}
