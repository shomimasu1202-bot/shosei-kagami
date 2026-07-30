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

// フォント（女の子らしい丸文字）。見出し=まるっとポップ、本文=丸ゴシック。
// 容量削減のため2書体のみ（bold は body と同じ書体で、色・サイズで強調）。
export const fonts = {
  title: 'MochiyPopOne_400Regular',
  body: 'ZenMaruGothic_400Regular',
  bold: 'ZenMaruGothic_400Regular',
};

// 五行ごとのカードテーマ（淡い下地＋差し色）。タイプカードの色分けに使う。
export const elementTheme: Record<string, { tint: string; strong: string }> = {
  木: { tint: '#eaf7ef', strong: '#4fae72' },
  火: { tint: '#fdeef1', strong: '#e8637a' },
  土: { tint: '#fbf2e6', strong: '#cf9a4f' },
  金: { tint: '#fdf8e0', strong: '#c9ab2e' },
  水: { tint: '#e9f3fc', strong: '#4f95d6' },
};

// 相性レベル → 色。
export function levelColor(level: string): string {
  if (level === '◎') return colors.good;
  if (level === '○') return colors.ok;
  return colors.caution;
}
