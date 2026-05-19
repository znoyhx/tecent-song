export type BgmTrack = {
  bgm_id: string;
  title: string;
  usage: string;
  stage: string | null;
  scene_ids: string[];
  npc_ids: string[];
  ending_id: string | null;
  priority: string;
  asset_url: string;
  fallback_url: string;
  asset_available: boolean;
  generated_path?: string | null;
  status: string;
  task_id?: string | null;
  item_id?: string | null;
  volume: number;
  fade_ms: number;
  duration_seconds: number;
  prompt_summary: string;
  updated_at?: string;
};

export type MusicManifest = {
  version: number;
  updated_at: string;
  provider: string;
  generation_api: string;
  query_api: string;
  model: string;
  tracks: BgmTrack[];
};

export type MusicSettings = {
  enabled: boolean;
  muted: boolean;
  volume: number;
  decided: boolean;
};
