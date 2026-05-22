import { resolveApiUrl } from '../../api/client';
import type { Scene, SessionSnapshot } from '../../types/game';
import type { CSSProperties } from 'react';


type ScenePanelProps = {
  snapshot: SessionSnapshot;
  selectedNpcId: string | null;
  busy: boolean;
  onSelectNpc: (npcId: string) => void;
};

function getSceneImage(scene: Scene): string {
  return resolveApiUrl(scene.visual_asset_url, scene.visual_asset_id ? `/api/visual/assets/${scene.visual_asset_id}` : '/api/visual/assets/scene_bookshop_front_hall');
}

const integratedNpcPositions: Record<string, Record<string, { left: string; top: string }>> = {
  scene_front_hall: { npc_owner: { left: '58%', top: '76%' } },
  scene_account_room: { npc_owner: { left: '58%', top: '78%' } },
  scene_engraving_room: { npc_worker: { left: '52%', top: '76%' } },
  scene_back_gate: { npc_worker: { left: '50%', top: '74%' } },
  scene_rain_alley: { npc_scholar: { left: '50%', top: '76%' } },
  scene_city_gate: { npc_scholar: { left: '70%', top: '76%' } },
  scene_interrogation_room: { npc_jinyiwei: { left: '50%', top: '78%' } },
};

function getNpcMarkerStyle(sceneId: string, npcId: string, index: number, count: number): CSSProperties {
  const mapped = integratedNpcPositions[sceneId]?.[npcId];
  if (mapped) {
    return mapped;
  }
  const span = count <= 1 ? 0 : 34;
  const left = count <= 1 ? 58 : 42 + (span * index) / Math.max(count - 1, 1);
  return { left: `${left}%`, top: '68%' };
}



export function ScenePanel({ snapshot, selectedNpcId, busy, onSelectNpc }: ScenePanelProps) {
  const scene = snapshot.scene;

  return (
    <section
      className="vn-backdrop"
      style={{ backgroundImage: `linear-gradient(180deg, rgba(8, 7, 9, .08), rgba(8, 7, 9, .42)), url(${getSceneImage(scene)})` }}
    >
      <div className="vn-rain" />
      <div className="vn-smoke" />

      <div className="integrated-npc-layer">
        {snapshot.scene_npcs.length > 0 ? (
          snapshot.scene_npcs.map((npc, index) => (
            <button
              key={npc.npc_id}
              type="button"
              className={npc.npc_id === selectedNpcId ? 'integrated-npc-button active' : 'integrated-npc-button'}
              style={getNpcMarkerStyle(scene.scene_id, npc.npc_id, index, snapshot.scene_npcs.length)}
              onClick={() => onSelectNpc(npc.npc_id)}
              disabled={busy}
            >
              <span>{npc.name}</span>
            </button>
          ))

        ) : (
          <div className="empty-stage-silhouette">
            <span>纸灰在雨里打旋，此处暂无人开口。</span>
          </div>
        )}
      </div>

    </section>
  );
}
