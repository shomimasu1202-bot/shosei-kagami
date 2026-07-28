// 掌星鑑 共通テーマ（配色・五行カラー）。

export const colors = {
  bg: '#0d1b2a',
  card: '#1b2a3a',
  cardAlt: '#22344a',
  accent: '#ffd166',
  text: '#e8eef4',
  subtext: '#c0ccda',
  muted: '#8899aa',
  error: '#ff6b6b',
  good: '#7bd88f', // ◎ 相生
  ok: '#6ec1e4', // ○ 比和
  caution: '#ffa94d', // △ 相剋
};

// 五行のカラー（木火土金水）。
export const elementColors: Record<string, string> = {
  木: '#5fbf77',
  火: '#ff6b6b',
  土: '#e0a458',
  金: '#f2d16b',
  水: '#5aa9e6',
};

export const ELEMENTS = ['木', '火', '土', '金', '水'] as const;

// 相性レベル → 色。
export function levelColor(level: string): string {
  if (level === '◎') return colors.good;
  if (level === '○') return colors.ok;
  return colors.caution;
}
