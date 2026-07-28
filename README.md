# 掌星鑑（しょうせいかがみ）

[![CI](https://github.com/shomimasu1202-bot/shosei-kagami/actions/workflows/ci.yml/badge.svg)](https://github.com/shomimasu1202-bot/shosei-kagami/actions/workflows/ci.yml)

生年月日から性格タイプを診断する占いアプリ。
外部の有料AIは使わず、公有である干支・五行を土台にした**純粋な計算ロジック**で
掌星鑑オリジナルの10タイプを決定的に算出する。

- **フロントエンド**: React Native (Expo / TypeScript) — `frontend/`
- **バックエンド**: Python / FastAPI — `backend/`
- git はルート（`shosei-kagami/`）で一元管理するモノレポ構成。

## リポジトリ構成

```
shosei-kagami/          ← git リポジトリ（モノレポ）
├── README.md
├── .gitignore
├── backend/            ← Python (FastAPI)
│   ├── app/
│   │   ├── main.py             FastAPI アプリ
│   │   └── engine/             計算エンジン
│   │       ├── ganzhi.py         日柱（日干支）算出       [Phase 1]
│   │       ├── five_elements.py  五行・陰陽の判定         [Phase 1]
│   │       ├── type_table.py     10タイプ確定表と写像     [Phase 1]
│   │       ├── solar.py          太陽黄経・節気の算出     [Phase 2]
│   │       ├── pillars.py        年月日柱・時柱・四柱      [Phase 2 / 3]
│   │       ├── reading.py        鑑定文の生成             [Phase 2.5]
│   │       ├── compatibility.py  相性（五行の相生相剋）   [Phase 2.6]
│   │       ├── hidden_stems.py   蔵干テーブル             [Phase 2.7]
│   │       ├── getsuritsu_bunya.py 月律分野蔵干（司令）    [Phase 2.7+]
│   │       └── element_balance.py 三柱の五行バランス      [Phase 2.7]
│   ├── tests/          ユニットテスト
│   ├── scripts/sample.py  サンプル出力
│   └── requirements.txt
└── frontend/           ← React Native (Expo / TypeScript)
    ├── App.tsx          タブ shell（鑑定／四柱／相性）
    └── src/
        ├── api.ts        バックエンド API クライアント
        ├── theme.ts      配色・五行カラー
        ├── components/   共通UI（入力・カード・五行バー）
        └── screens/      ReadingScreen / FourPillarsScreen / CompatibilityScreen
```

## Phase 1 のスコープ

含める: 日柱（日干支）算出 → 日干の五行・陰陽 → 掌星鑑オリジナル10タイプへの写像。
含めない（後続）: 年柱・月柱（立春・節入り処理）、手相・血液型・鑑定文生成。

### 10タイプ対応表（確定・改変禁止）

| 日干 | type_id | 名称 | 読み | 五行 | 陰陽 |
|------|---------|------|------|------|------|
| 甲 | you     | 葉 | よう   | 木 | 陽 |
| 乙 | fuji    | 藤 | ふじ   | 木 | 陰 |
| 丙 | asahi   | 旭 | あさひ | 火 | 陽 |
| 丁 | hotaru  | 蛍 | ほたる | 火 | 陰 |
| 戊 | mine    | 嶺 | みね   | 土 | 陽 |
| 己 | sono    | 苑 | その   | 土 | 陰 |
| 庚 | rin     | 鈴 | りん   | 金 | 陽 |
| 辛 | gyoku   | 玉 | ぎょく | 金 | 陰 |
| 壬 | minato  | 湊 | みなと | 水 | 陽 |
| 癸 | shizuku | 雫 | しずく | 水 | 陰 |

### 日柱計算の較正（アンカー）

- アンカー: **2000-01-07 = 甲子**（60干支サイクルの先頭）
- 経過日数の `mod 60` で日干支を決定（連続カウント）
- 換算式 `日干=(JDN+9)%10 / 日支=(JDN+1)%12` と、
  古典的基準日 **1900-01-01 = 甲戌** の2点で相互に整合することを確認済み
- 詳細は [`backend/app/engine/ganzhi.py`](backend/app/engine/ganzhi.py) の冒頭コメント参照

## Phase 2 のスコープ（年柱・月柱／立春・節入り）

生年月日（＋任意で出生時刻）から **年柱・月柱** を算出する。四柱推命の年月は暦日ではなく
**太陽黄経**で切り替わるため、天文計算を自前で実装している（外部の重いライブラリに非依存）。

### 年柱（立春基準）

- 年は元日でも旧正月でもなく **立春（太陽黄経 315°、約2月4日）** で切り替わる。
- `年干=(立春基準年−4)%10 / 年支=(立春基準年−4)%12`（西暦4年=甲子）。
- 検算: 1984=甲子、2024=甲辰、2000=庚辰。

### 月柱（節入り基準 + 五虎遁）

- 月は 12 の「節」（立春・啓蟄・清明…）で切り替わる。月支は太陽黄経から直接:
  `k=floor(((L−315)%360)/30)`（0=寅…11=丑）、`月支=(k+2)%12`。
- 月干は五虎遁（年干から）: `寅月干=((年干%5)*2+2)%10`、`月干=(寅月干+k)%10`。

### 節気の算出と精度

- Meeus『Astronomical Algorithms』ch.25 の低精度式で太陽の視黄経を計算（[`solar.py`](backend/app/engine/solar.py)）。
- タイムゾーンは **JST (UTC+9) 固定**（tzdata 非依存）。ΔT は Espenak–Meeus 多項式で補正。
- 精度は約 **±数分**。国立天文台の暦要項に対し、テスト範囲の節気で**日付は一致**する
  （例: 2021 立春 = 2/3、2024 立春 = 2/4）。
- **限界**: 節入り／立春の瞬間の前後 数分〜十数分に生まれた場合、月柱・年柱が
  入れ替わり得る。厳密な鑑定には正確な出生時刻が必要。
- **時刻の扱い**: 出生時刻が不明（date のみ）の場合は **正午 (JST 12:00) を仮定**する。

### 含めないもの（後続）

- 時柱（Phase 3）、手相・血液型。

## Phase 2.5 のスコープ（鑑定文の生成）

外部AIを使わず、計算結果から**決定的に**鑑定文を組み立てる（[`reading.py`](backend/app/engine/reading.py)）。
全文が掌星鑑オリジナルで、既存ブランドの鑑定文・言い回しは不使用。

- **文体**: 優しく寄り添う敬体（です・ます）。
- **セクション**: 基本性格・強み・課題／恋愛・結婚／仕事・適職・金運／対人関係・相性。
- **3層合成モデル**（セクションごとに連結）:
  1. タイプ固有文（日干10タイプ × 3節）… 最も個別的
  2. 五行の味付け（木火土金水 × 3節）… 五行ファミリーの共通テーマ
  3. 陰陽の味付け（陽/陰 × 3節）… 極性のニュアンス
- 同じ日干（＝同じタイプ）なら鑑定文も同一。決定的で、都度課金なし。
- API: `POST /reading` → `{ type_id, 名称, 五行, 陰陽, headline, sections:[{title,text}...] }`

将来的に年柱・月柱の五行や三柱バランスを味付け層へ差し込めるよう、
味付けを独立した部品として分離してある（拡張ポイント）。

## Phase 2.6 のスコープ（相性）

公有である**五行の相生・相剋**を土台に、日干10タイプ同士の相性を決定的に算出する
（[`compatibility.py`](backend/app/engine/compatibility.py)）。

- 相生: 木→火→土→金→水→木、相剋: 木→土→水→火→金→木。
- A から見た B との関係は5通り（比和／相生2向き／相剋2向き）で、`◎ ○ △` のレベルと
  コメントを返す。陰陽の異同でニュアンスを添える。
- **1人の鑑定文**には「対人関係・相性」セクションと `compatibility_guide`
  （好相性=相生／要注意=相剋のタイプ名）を含む。
- **2人の相性診断**: `POST /compatibility`（`birthdate_a`/`birthdate_b`）。

## Phase 2.7 のスコープ（三柱の五行バランス／蔵干対応の本格版）

日干（タイプ）だけでは同じ日干の人は全員同じ鑑定文になる。そこで
**三柱（年・月・日）の五行分布**を集計し、鑑定文に反映して
**生年月日全体で内容が変わる**ようにした（[`element_balance.py`](backend/app/engine/element_balance.py)）。

- **蔵干（地支に隠れた天干）を含めた重み付き集計**（[`hidden_stems.py`](backend/app/engine/hidden_stems.py)、淵海子平系の標準表）:
  - 天干（年月日）= 各3点、地支の蔵干 = 本気3・中気2・余気1点（定数で調整可）。
  - `scores`（重み付き）／`percentages`（合計100）／`dominant`（強調される持ち味）／
    `lacking`（本当に欠けた五行＝補うとよい面）／`day_master`（本人の五行）を返す。
  - `include_hidden_stems=False` で可視のみ（天干＋地支本気、各1、合計6）の簡易版も選べる。
- 蔵干を数えると、可視のみでは「欠け」に見えた五行が実は巡っている、といった
  より正確な分布になる（例: 庚午/庚辰/庚戌 → 金42%・土31%…、欠けなし）。
- 鑑定文に動的な「**五行バランス**」セクション（基本性格の直後）と構造化データ
  `element_balance` を追加。同じ日干でも年月日で内容が変わる（個別化）。
- API: `POST /five-element-balance`。`POST /reading` にも `element_balance` を同梱。

### 月律分野蔵干（司令）による精密化 [Phase 2.7+]

月支（月令）だけは、蔵干のどれが「**司令**」かが**節入りからの経過日数**で変わる
（[`getsuritsu_bunya.py`](backend/app/engine/getsuritsu_bunya.py)、人元司令分野・各月30日正規化）。

- 生誕日の節入りからの日数で司令天干（余気→中気→本気）を判定し、司令を重く数える。
- **同じ月生まれでも前半／後半で分布が変わる**（例: 寅月 → 2/6 は戊[土]司令、
  2/13 は丙[火]司令で火42%、2/25 は甲[木]司令で木35%）。
- `element_balance.month_commander` に司令天干・役割・五行・節入りからの日数を格納。
- `use_getsuritsu_bunya=False` で無効化（月支も固定蔵干の役割重みに）できる。
- ※ さらに厳密には司令以外の蔵干も日数比で連続配分する流派もある（拡張余地）。

## Phase 3 のスコープ（時柱／四柱）

出生時刻から**時柱（時干支）**を算出し、四柱（八字）を完成させる（[`pillars.py`](backend/app/engine/pillars.py)）。

- **時支**: 2時間ごとの十二時辰（子=23:00-01:00 …）。`時支=((hour+1)//2)%12`。
- **時干**: 五鼠遁（日上起時）で日干から導く。`子時干=(日干%5)*2%10`、`時干=(子時干+時支)%10`。
- **設計上の確定事項**:
  - **論点A（子刻）＝ 23時で翌日**: 23時以降は翌日の日干で日柱・時柱を出す
    （`late_night_boundary=True` を上位関数の既定に）。年柱・月柱は太陽位置で決まるため移動しない。
  - **論点B（時刻精度）＝ JSTそのまま**: 経度・均時差補正なし（真太陽時補正は拡張余地）。
  - **論点C（四柱バランス）＝ 時刻があれば四柱**: 時干＋時支（蔵干）を五行バランスに加算。
    時刻不明（date のみ）なら三柱のまま（`element_balance.pillar_count` が 3/4）。
- API: `POST /hour-pillar`（時刻必須）、`POST /four-pillars`（時刻無ければ hour=null）。
  `POST /five-element-balance`・`POST /reading` も時刻があれば四柱で集計。

## バックエンド セットアップ

```bash
cd backend
py -m venv venv
venv\Scripts\python.exe -m pip install -r requirements.txt
```

### テスト実行

```bash
cd backend
venv\Scripts\python.exe -m pytest
```

### API サーバー起動

```bash
cd backend
venv\Scripts\uvicorn.exe app.main:app --reload
```

- `POST /type` … `{"birthdate": "YYYY-MM-DD"}` → 掌星鑑タイプ
- `POST /day-pillar` … 日柱
- `POST /five-element-profile` … 五行・陰陽
- `POST /year-pillar` … 年柱（`{"birthdate","birthtime?"}`、立春基準）
- `POST /month-pillar` … 月柱（節入り基準）
- `POST /three-pillars` … 年柱・月柱・日柱まとめ
- `POST /hour-pillar` … 時柱（`birthtime` 必須）
- `POST /four-pillars` … 年・月・日・時（時刻無ければ hour=null）
- `POST /five-element-balance` … 三柱／四柱の五行バランス（時刻があれば四柱）
- `POST /reading` … 鑑定文（5セクション＋相性ガイド＋五行バランス。`birthtime` があれば四柱）
- `POST /compatibility` … 2人の相性（`{"birthdate_a","birthdate_b"}`）
- `GET /type?birthdate=YYYY-MM-DD` … ブラウザ確認用
- `GET /health` … ヘルスチェック
- Swagger UI: http://127.0.0.1:8000/docs

### サンプル出力

```bash
cd backend
venv\Scripts\python.exe -m scripts.sample 1990-04-15
```

## フロントエンド（React Native / Expo）

3画面をタブで切り替える構成（`react-navigation` 非依存・状態ベースの軽量タブ）:

- **鑑定**（[ReadingScreen](frontend/src/screens/ReadingScreen.tsx)）: 生年月日＋任意で時刻 →
  タイプ・五行バランス（棒グラフ）・鑑定文4セクション・相性ガイド。
- **四柱**（[FourPillarsScreen](frontend/src/screens/FourPillarsScreen.tsx)）: 年・月・日・時の
  干支を柱ごとに表示（時刻なしなら時柱は「—」）。
- **相性**（[CompatibilityScreen](frontend/src/screens/CompatibilityScreen.tsx)）: 2人の生年月日 →
  ◎○△レベルとコメント。

> ⚠ 開発環境に Node.js/npm が無いため、コードは用意済みだが**未実行・未検証**。
> 実機/エミュレータでの起動確認は各自で行うこと。Expo SDK は package.json 記載
> （SDK 51 / RN 0.74）だが、最新環境では `npx create-expo-app` で作り直し、
> `App.tsx` と `src/` を移植するのが安全。

```bash
cd frontend
npm install
npm run start   # Expo。iOS/Android/Web で確認
```

- バックエンド接続先は [`frontend/src/api.ts`](frontend/src/api.ts) の `API_BASE_URL`
  （iOS/Web=`127.0.0.1`、Android エミュレータ=`10.0.2.2`、実機は PC の LAN IP）。
- バックエンドを `uvicorn app.main:app --host 0.0.0.0 --reload` で起動しておくこと。

## 権利

タイプ体系は公有の干支・五行を土台にした掌星鑑オリジナル。
既存の占いブランド（五星三心占い・天星術など）の名称・タイプ名・鑑定文は一切使用していない。
