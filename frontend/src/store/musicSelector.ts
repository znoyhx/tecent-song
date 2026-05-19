import type { SessionSnapshot } from '../types/game';

const npcTrackMap: Record<string, string> = {
  npc_owner: 'ming_npc_owner_xu',
  npc_worker: 'ming_npc_worker_ashen',
  npc_scholar: 'ming_npc_scholar_guwen',
  npc_jinyiwei: 'ming_npc_jinyiwei_luzheng',
};

const sceneTrackMap: Record<string, string> = {
  scene_front_hall: 'ming_intro_night_fire',
  scene_fire_yard: 'ming_intro_night_fire',
  scene_account_room: 'ming_investigation_threads',
  scene_lamp_shelf: 'ming_investigation_threads',
  scene_engraving_room: 'ming_investigation_threads',
  scene_back_gate: 'ming_investigation_threads',
  scene_rain_alley: 'ming_reversal_grain_record',
  scene_city_gate: 'ming_reversal_grain_record',
  scene_interrogation_room: 'ming_reversal_grain_record',
};

const endingTrackMap: Record<string, string> = {
  ending_truth: 'ending_truth',
  ending_order: 'ending_order',
  ending_survival: 'ending_survival',
  ending_tragedy: 'ending_tragedy',
  ending_hidden: 'ending_hidden',
};

export function selectBgmId(snapshot: SessionSnapshot | null, selectedNpcId: string | null): string {
  if (!snapshot) {
    return 'pre_game_entry';
  }

  const stage = snapshot.state.current_stage;
  const endingId = snapshot.ending?.ending_id;
  if (endingId && endingTrackMap[endingId]) {
    return endingTrackMap[endingId];
  }

  if (stage === 'choice') {
    return 'ming_choice_evidence';
  }
  if (stage === 'reversal') {
    return 'ming_reversal_grain_record';
  }

  if (selectedNpcId && !['choice', 'reversal', 'ending'].includes(stage)) {
    const npcTrack = npcTrackMap[selectedNpcId];
    if (npcTrack) {
      return npcTrack;
    }
  }

  if (snapshot.state.risk_level >= 6 && ['intro', 'investigation'].includes(stage)) {
    return 'ming_reversal_grain_record';
  }

  const sceneTrack = sceneTrackMap[snapshot.state.current_scene_id];
  if (sceneTrack) {
    return sceneTrack;
  }

  if (stage === 'intro') {
    return 'ming_intro_night_fire';
  }
  if (stage === 'investigation') {
    return 'ming_investigation_threads';
  }

  return 'pre_game_entry';
}
