export const stageDescriptions: Record<string, string> = {
  intro: '先抓住最表层的异常。',
  investigation: '让证词与物证互相碰撞。',
  reversal: '确认焚毁目标并不只是诗稿。',
  choice: '决定把证据交给谁，或护到哪一步。',
  ending: '查看结局与历史回声。',
};

export function getTrustLabel(value: number): string {
  if (value <= -1) {
    return '防备';
  }
  if (value === 0) {
    return '观望';
  }
  if (value === 1) {
    return '松动';
  }
  if (value === 2) {
    return '信任';
  }
  return '共担风险';
}

export function buildActionNotice(baseText: string, newTitles: string[]): string {
  if (newTitles.length === 0) {
    return baseText;
  }
  return `${baseText} 你获得了：${newTitles.join('、')}。`;
}
