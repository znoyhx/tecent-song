import type { Dynasty, PlayerIdentityRecommendations, PlayerRole } from '../types/game';

export type DynastyEntryMeta = {
  dynastyId: string;
  keywords: string[];
  teaser: string;
  description: string;
  coverAssetId: string;
  eventId: string;
  eventName: string;
  eventSummary: string;
  coreConflict: string;
  npcCount: number;
  clueCount: number;
  endingCount: number;
};

export type ScenarioGenerationStep = {
  id: string;
  title: string;
  detail: string;
};

export type GeneratedScenarioPreview = {
  dynastyId: string;
  dynastyName: string;
  dynastyPeriod: string;
  roleId: string;
  roleName: string;
  roleSummary: string;
  eventId: string;
  eventName: string;
  eventSummary: string;
  coreConflict: string;
  npcCount: number;
  clueCount: number;
  endingCount: number;
  teaser: string;
  coverAssetId: string;
  generationSteps: ScenarioGenerationStep[];
  identityRecommendations: PlayerIdentityRecommendations;
};

const generationSteps: ScenarioGenerationStep[] = [
  {
    id: 'retrieve-knowledge',
    title: '检索朝代知识库',
    detail: '读取制度、风物、风险词与视觉语义，锁定当前时代的叙事边界。',
  },
  {
    id: 'generate-role',
    title: '生成玩家身份',
    detail: '根据朝代社会结构抽取可行动身份，为推理与风险尺度定下立场。',
  },
  {
    id: 'build-event',
    title: '构建事件骨架',
    detail: '把地点、火种、传闻与禁忌组织成一条可调查的开局事件链。',
  },
  {
    id: 'link-npcs',
    title: '生成 NPC 关系',
    detail: '分配立场、隐情与关系张力，让证词冲突能够持续推进。',
  },
  {
    id: 'assign-clues',
    title: '分配关键线索',
    detail: '将物证、口供、误导信息与可组合线索投放到各阶段场景。',
  },
  {
    id: 'prepare-endings',
    title: '准备多结局分支',
    detail: '根据真相、秩序、求生与牺牲权重生成不同收束出口。',
  },
];

const fallbackDynasties: Dynasty[] = [
  {
    dynasty_id: 'ming',
    name: '明代',
    enabled: true,
    period_label: '洪武至崇祯间的书坊疑案演示',
    core_mood: '文祸、书坊、锦衣卫、暗线侦缉',
    allowed_roles: ['role_ming_bookshop_apprentice'],
    forbidden_terms: ['清代辫发', '玻璃窗', '电灯'],
    visual_keywords: ['雨夜', '纸灰', '火光', '书坊'],
  },
  {
    dynasty_id: 'song',
    name: '北宋',
    enabled: false,
    period_label: '边患与驿站流言原型',
    core_mood: '驿站、军报、边患、市井疑云',
    allowed_roles: [],
    forbidden_terms: ['火枪', '近代军服'],
    visual_keywords: ['驿路', '军报', '汴梁', '夜巡'],
  },
  {
    dynasty_id: 'tang',
    name: '晚唐',
    enabled: false,
    period_label: '藩镇与粮仓密信原型',
    core_mood: '藩镇、流民、粮仓、乱世密信',
    allowed_roles: [],
    forbidden_terms: ['霓虹', '现代街景'],
    visual_keywords: ['粮仓', '乱世', '密信', '长街'],
  },
];

const fallbackRoles: Record<string, PlayerRole> = {
  ming: {
    role_id: 'role_ming_bookshop_apprentice',
    dynasty_id: 'ming',
    name: '书坊学徒',
    enabled: true,
    social_position: '你依附于书坊生计，能接触账册、纸张与刻版残片，也最容易被卷入封口。',
    permissions: ['出入前厅与后院', '整理纸稿', '接触残页'],
    limitations: ['无权直接对抗官面人物', '容易成为替罪羊'],
  },
};

const fallbackIdentityRecommendations: PlayerIdentityRecommendations = {
  default_identity: 'bookshop_apprentice',
  options: [
    {
      identity_id: 'bookshop_apprentice',
      display_name: '书坊学徒',
      description: '熟悉书坊日常，也最容易被卷入嫌疑。',
      social_rank: 'low',
      relation_to_case: '你本就在书坊守夜，能接触纸稿、账册和后院火场。',
      attitude_hint: '多数 NPC 会把你当作可驱使的小人物，轻慢中带着试探。',
      background: '你是书坊里打杂守夜的学徒，熟悉纸张、刻版和前后院动线。雨夜火起后，掌柜与差役都把目光投向你，你必须先在疑影中自证清白。',
      tags: ['书坊', '守夜', '低身份', '可调查'],
      is_default: true,
    },
    {
      identity_id: 'wandering_detective',
      display_name: '游方探事人',
      description: '擅长查访人情，但身份容易惹人防备。',
      social_rank: 'middle',
      relation_to_case: '你为一桩旧稿纠纷来到书坊附近，恰逢雨夜失火。',
      attitude_hint: 'NPC 会半信半疑，愿听你追问，却会防着你把事情闹大。',
      background: '你以替商旅查访失物和旧案为生，随身带着磨旧的问事札。雨夜途经书坊，本想打听一卷旧稿去向，却被火光和封门差役留在现场。',
      tags: ['探事', '查访', '中身份'],
      is_default: false,
    },
    {
      identity_id: 'lodging_scholar',
      display_name: '寄居书生',
      description: '识字懂文书，容易接近士人与稿件。',
      social_rank: 'middle',
      relation_to_case: '你在城中借读，曾与书坊往来抄校文稿。',
      attitude_hint: '士人愿与你多说几句，官面人物仍会怀疑你的立场。',
      background: '你是寄居城中的书生，靠抄校文稿换些盘缠。因曾替书坊核过纸样，雨夜被叫来辨认残稿，却在封门声中发现自己也脱不开干系。',
      tags: ['读书人', '文书', '中身份'],
      is_default: false,
    },
    {
      identity_id: 'woodcutter',
      display_name: '近郊樵夫',
      description: '从后巷送柴入城，行动不起眼却常被轻视。',
      social_rank: 'low',
      relation_to_case: '你夜里给书坊送柴，正好经过后门与雨巷。',
      attitude_hint: 'NPC 可能轻慢、敷衍或怀疑你图利，证据足够时才会动摇。',
      background: '你是近郊樵夫，入城送柴时常从书坊后巷经过。雨夜你本想把湿柴卸在檐下避雨，却撞见后院火起，粗布衣衫反让旁人先疑你偷摸。',
      tags: ['樵夫', '低身份', '后巷'],
      is_default: false,
    },
  ],
};

const entryCatalog: Record<string, DynastyEntryMeta> = {
  ming: {
    dynastyId: 'ming',
    keywords: ['文祸', '书坊', '锦衣卫', '暗线侦缉'],
    teaser: '文祸阴影压住灯火，书坊里每一页残稿都可能通向更深的封口令。',
    description: '适合展示“制度压迫 + 书坊案卷 + 人物证词冲突”的悬疑生成效果。',
    coverAssetId: 'scene_bookshop_front_hall',
    eventId: 'ming_bookshop_fire',
    eventName: '雨夜焚稿案',
    eventSummary: '雨夜火起于书坊后院，玩家从被怀疑的守夜学徒开始自证，逐步追出粮册抄录、封口令、城门搜检和众人各自隐瞒的证据链。',
    coreConflict: '文祸风险、权力侦缉、保命与留证',
    npcCount: 4,
    clueCount: 35,
    endingCount: 5,
  },
  song: {
    dynastyId: 'song',
    keywords: ['驿站', '军报', '边患', '市井疑云'],
    teaser: '军报迟滞、商旅杂讯与边患阴影交织，适合展开一条更偏情报流转的疑案。',
    description: '当前作为朝代选择展示，完整可玩链路将于后续开放。',
    coverAssetId: 'scene_rain_alley',
    eventId: 'song_post_station_case',
    eventName: '驿站失牍案',
    eventSummary: '一封原该送往边镇的军报在驿站夜里失踪，沿路消息开始互相抵触。',
    coreConflict: '边患情报、官私传递、消息真伪',
    npcCount: 4,
    clueCount: 12,
    endingCount: 4,
  },
  tang: {
    dynastyId: 'tang',
    keywords: ['藩镇', '流民', '粮仓', '乱世密信'],
    teaser: '乱世秩序松动时，粮仓、密信与流民消息会把每个选择都推向更危险的边缘。',
    description: '当前作为朝代选择展示，完整可玩链路将于后续开放。',
    coverAssetId: 'scene_rain_alley',
    eventId: 'tang_granary_letter_case',
    eventName: '粮仓密信案',
    eventSummary: '粮仓短缺与匿名密信同时出现，地方势力开始争抢叙事主动权。',
    coreConflict: '乱世秩序、军粮流向、真假消息',
    npcCount: 5,
    clueCount: 14,
    endingCount: 4,
  },
};

function fallbackMeta(dynasty: Dynasty): DynastyEntryMeta {
  return {
    dynastyId: dynasty.dynasty_id,
    keywords: dynasty.visual_keywords.length > 0 ? dynasty.visual_keywords.slice(0, 4) : [dynasty.core_mood],
    teaser: dynasty.core_mood,
    description: '系统将根据该朝代的制度、风物与人物模板生成事件原型。',
    coverAssetId: 'scene_rain_alley',
    eventId: `${dynasty.dynasty_id}_generated_event`,
    eventName: `${dynasty.name}疑案原型`,
    eventSummary: '正在根据朝代信息生成事件骨架。',
    coreConflict: '待生成',
    npcCount: 4,
    clueCount: 10,
    endingCount: 4,
  };
}

export function getFallbackDynasties(): Dynasty[] {
  return fallbackDynasties.map((dynasty) => ({ ...dynasty }));
}

export function getFallbackRoleForDynasty(dynastyId: string): PlayerRole | null {
  const role = fallbackRoles[dynastyId];
  return role ? { ...role } : null;
}

export function getFallbackIdentityRecommendations(): PlayerIdentityRecommendations {
  return {
    default_identity: fallbackIdentityRecommendations.default_identity,
    options: fallbackIdentityRecommendations.options.map((option) => ({ ...option, tags: [...option.tags] })),
  };
}

export function getDynastyEntryMeta(dynasty: Dynasty): DynastyEntryMeta {
  return entryCatalog[dynasty.dynasty_id] ?? fallbackMeta(dynasty);
}

export function buildScenarioPreview(
  dynasty: Dynasty,
  role: PlayerRole,
  identityRecommendations: PlayerIdentityRecommendations = getFallbackIdentityRecommendations(),
): GeneratedScenarioPreview {
  const meta = getDynastyEntryMeta(dynasty);
  return {
    dynastyId: dynasty.dynasty_id,
    dynastyName: dynasty.name,
    dynastyPeriod: dynasty.period_label,
    roleId: role.role_id,
    roleName: role.name,
    roleSummary: role.social_position,
    eventId: meta.eventId,
    eventName: meta.eventName,
    eventSummary: meta.eventSummary,
    coreConflict: meta.coreConflict,
    npcCount: meta.npcCount,
    clueCount: meta.clueCount,
    endingCount: meta.endingCount,
    teaser: meta.teaser,
    coverAssetId: meta.coverAssetId,
    generationSteps,
    identityRecommendations,
  };
}
