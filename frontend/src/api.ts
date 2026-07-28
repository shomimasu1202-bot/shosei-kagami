// 掌星鑑 バックエンド API クライアント。
//
// 開発時のベースURL:
//   - iOS シミュレータ / Web: http://127.0.0.1:8000
//   - Android エミュレータ:   http://10.0.2.2:8000
// 実機テストでは PC の LAN IP（例: http://192.168.x.x:8000）に置き換えること。

import { Platform } from 'react-native';

// 接続先バックエンドのURLを決める。
//  - web: 開いているページと同じホスト（localhost でも PCのLAN IP でもOK）の :8000
//  - Android エミュレータ: 10.0.2.2（ホストPCを指す特別なIP）
//  - iOS シミュレータ等: 127.0.0.1
// 実機(Expo Go)や別PCから使う場合は、開いた URL のホスト名がそのまま使われる。
function resolveApiBase(): string {
  if (
    Platform.OS === 'web' &&
    typeof window !== 'undefined' &&
    window.location &&
    window.location.hostname
  ) {
    return `http://${window.location.hostname}:8000`;
  }
  if (Platform.OS === 'android') return 'http://10.0.2.2:8000';
  return 'http://127.0.0.1:8000';
}

export const API_BASE_URL = resolveApiBase();

// ---- レスポンス型（バックエンドの to_dict に対応）----

export type SectionReading = {
  section_id: string;
  title: string;
  text: string;
};

export type MonthCommander = {
  stem: string;
  phase: string;
  element: string;
  days_since_setsu: number;
};

export type ElementBalance = {
  scores: Record<string, number>;
  total: number;
  percentages: Record<string, number>;
  dominant: string[];
  lacking: string[];
  day_master: string;
  include_hidden_stems: boolean;
  comment: string;
  pillar_count: number;
  month_commander: MonthCommander | null;
};

export type Reading = {
  type_id: string;
  名称: string;
  読み: string;
  五行: string;
  陰陽: string;
  headline: string;
  sections: SectionReading[];
  compatibility_guide: { best: string[]; caution: string[] };
  element_balance: ElementBalance | null;
  year_fortune: {
    reference_year: number;
    astrological_year: number;
    year_ganzhi: string;
    ten_god: string;
  } | null;
};

export type FourPillars = {
  year: {
    year_stem_name: string;
    year_branch_name: string;
    astrological_year: number;
    五行: string;
    陰陽: string;
  };
  month: {
    month_stem_name: string;
    month_branch_name: string;
    solar_term_name: string;
    month_branch_index: number;
    五行: string;
    陰陽: string;
  };
  day: {
    day_stem_name: string;
    day_branch_name: string;
  };
  hour: {
    hour_stem_name: string;
    hour_branch_name: string;
    time_range: string;
    五行: string;
    陰陽: string;
  } | null;
};

export type Compatibility = {
  type_id_a: string;
  名称_a: string;
  type_id_b: string;
  名称_b: string;
  relation: string;
  direction: string;
  level: string;
  comment: string;
};

// ---- 共通リクエスト ----

async function postJson<T>(path: string, body: unknown): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
  } catch (e) {
    throw new Error(
      `サーバーに接続できませんでした（${API_BASE_URL}）。バックエンドが起動しているか、接続先URLをご確認ください。`,
    );
  }
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const j = await res.json();
      if (j?.detail) detail = typeof j.detail === 'string' ? j.detail : JSON.stringify(j.detail);
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return (await res.json()) as T;
}

// birthtime は "HH:MM"（空なら送らない）。
function birthBody(birthdate: string, birthtime?: string) {
  const body: Record<string, string> = { birthdate: birthdate.trim() };
  if (birthtime && birthtime.trim()) body.birthtime = birthtime.trim();
  return body;
}

export function fetchReading(birthdate: string, birthtime?: string): Promise<Reading> {
  return postJson<Reading>('/reading', birthBody(birthdate, birthtime));
}

export function fetchFourPillars(birthdate: string, birthtime?: string): Promise<FourPillars> {
  return postJson<FourPillars>('/four-pillars', birthBody(birthdate, birthtime));
}

export function fetchCompatibility(
  birthdateA: string,
  birthdateB: string,
): Promise<Compatibility> {
  return postJson<Compatibility>('/compatibility', {
    birthdate_a: birthdateA.trim(),
    birthdate_b: birthdateB.trim(),
  });
}
