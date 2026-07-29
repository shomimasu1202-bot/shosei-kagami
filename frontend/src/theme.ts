// 掌星鑑 共通テーマ（やわらかいローズピンク基調・女性向け）。

export const colors = {
  bg: '#fff5f8', // ほんのりピンクの生成り
  card: '#ffffff',
  cardAlt: '#fdeaf1', // 入力欄・バーの下地（薄ピンク）
  accent: '#e86a92', // ローズピンク（ボタン・見出し・アクティブ）
  accentSoft: '#f7c6d8', // やわらかいピンク
  onAccent: '#ffffff', // ピンク上の文字
  text: '#5b4550', // 深いモーブ（本文）
  subtext: '#9a818a',
  muted: '#c3aeb6',
  border: '#f4d9e3',
  error: '#e5566b',
  good: '#e86a92', // ◎ 相生（ローズ）
  ok: '#7fb0dd', // ○ 比和（やわらかい水色）
  caution: '#eaa14e', // △ 相剋（アンバー）
};

// 五行のカラー（木火土金水）— 明るい下地でも映えるやわらかい色。
export const elementColors: Record<string, string> = {
  木: '#63c187',
  火: '#f2778f',
  土: '#e6a862',
  金: '#e7c44e',
  水: '#66aee6',
};

export const ELEMENTS = ['木', '火', '土', '金', '水'] as const;

// 相性レベル → 色。
export function levelColor(level: string): string {
  if (level === '◎') return colors.good;
  if (level === '○') return colors.ok;
  return colors.caution;
}
