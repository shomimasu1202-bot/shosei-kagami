"""鑑定文の生成（Phase 2.5）。

外部AIを使わず、計算結果から**決定的に**鑑定文を組み立てる。
文体は「優しく寄り添う敬体（です・ます）」。全文が掌星鑑オリジナルで、
既存の占いブランドの鑑定文・言い回しは使用していない。

== 合成モデル（3層） ==
セクションごとに、次の3つの部品を順に連結して段落を作る:
    1. タイプ固有文  … 日干10タイプごとの固有の文（最も個別的）
    2. 五行の味付け  … 木火土金水ごとの共通テーマ文
    3. 陰陽の味付け  … 陽/陰ごとのニュアンス文
五行・陰陽は日干（＝タイプ）から一意に決まるため、タイプの世界観を
「五行ファミリー」「陰陽」の共通言語で補強する役割を持つ。

== セクション ==
    personality … 基本性格・強み・課題
    love        … 恋愛・結婚
    work        … 仕事・適職・金運
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, asdict

from .type_table import ShoseiType, get_type
from .compatibility import CompatibilityGuide, compatibility_guide_for_type
from .element_balance import (
    FiveElementBalance,
    get_five_element_balance,
    describe_balance,
)
from .ganzhi import get_day_pillar
from .pillars import get_year_pillar
from .ten_gods import get_ten_god

# (section_id, 表示タイトル) 表示順。
SECTIONS: tuple[tuple[str, str], ...] = (
    ("personality", "基本性格・強み・課題"),
    ("love", "恋愛・結婚"),
    ("work", "仕事・適職・金運"),
    ("relations", "対人関係・相性"),
)

# --- 1. タイプ固有文: TYPE_TEXT[type_id][section_id] ---
TYPE_TEXT: dict[str, dict[str, str]] = {
    "you": {  # 葉 / 木陽
        "personality": "まっすぐに伸びていく葉のように、素直な成長力があなたの魅力です。新しいことへ物おじせず踏み出せる一方、伸びを急ぐあまり無理を重ねやすいところは、時どき立ち止まって確かめてあげてください。",
        "love": "好意はまっすぐ言葉や態度に表れ、相手に安心感を与えます。駆け引きは得意ではないぶん、飾らず正直でいられる人と穏やかな関係を築けます。",
        "work": "目標に向かって着実に力を伸ばせる、努力の人です。金運は堅実に積み上げるほど安定し、成長のための自己投資が後の実りにつながります。",
        "relations": "まっすぐで裏表のない接し方が、周囲の信頼を集めます。素直に本音を伝え合える関係でこそ、あなたらしくのびのびと過ごせます。",
    },
    "fuji": {  # 藤 / 木陰
        "personality": "しなやかにつるを伸ばす藤のように、環境や相手に合わせて柔らかく形を変えられる人です。人と人をつなぐ力に恵まれますが、周りに合わせすぎて自分の願いを後回しにしやすい点は、意識して大切にしてください。",
        "love": "相手の気持ちを汲み取るのが上手で、寄り添う恋を育てます。尽くしすぎて疲れないよう、あなたが甘えられる相手を選ぶと長く続きます。",
        "work": "人の間を取り持ち、場をなめらかに回す潤滑油のような存在です。金運は人の縁から広がりやすく、信頼を重ねることが実入りにつながります。",
        "relations": "相手に合わせて距離を柔らかく調整でき、幅広い人と良い縁を結べます。合わせすぎて疲れたら、少し離れてひと息つくことも大切にしてください。",
    },
    "asahi": {  # 旭 / 火陽
        "personality": "朝の光のように、その場をぱっと明るくする温かさを持っています。裏表なく人を励ませる一方、気持ちがまっすぐ出やすいので、勢いのままの一言には少し気をつけると安心です。",
        "love": "好きな気持ちを惜しみなく伝え、相手を元気にする恋をします。素直な愛情表現が持ち味なので、それを喜んでくれる人と相性が良いでしょう。",
        "work": "周囲を照らし、場の空気を前向きに変えるムードメーカーです。金運は人前に立つ場面や発信から開けやすく、明るさそのものが財産になります。",
        "relations": "明るく開けっぴろげで、初対面でもすぐ打ち解けられます。気持ちがまっすぐ伝わるぶん、勢いのある一言には少しだけ気を配ると安心です。",
    },
    "hotaru": {  # 蛍 / 火陰
        "personality": "暗がりでそっと光る蛍のように、細やかな気配りと静かな温もりを持つ人です。相手の小さな変化によく気づきますが、気を回しすぎて疲れやすいので、自分をいたわる時間も大切にしてください。",
        "love": "派手さより誠実さで、じんわりと信頼を深めていく恋を育てます。言葉数は少なくても想いは深く、そばで安心をくれる相手と穏やかに結ばれます。",
        "work": "細やかさと気づきで、周囲を陰から支える頼れる存在です。金運はこつこつと堅実に守るほど安定し、無理のない蓄えが力になります。",
        "relations": "聞き役に回り、相手の心にそっと寄り添うのが得意です。狭く深い付き合いで、少人数の温かな輪の中に安らぎを感じられます。",
    },
    "mine": {  # 嶺 / 土陽
        "personality": "どっしりと構える山の頂のように、揺るがない安定感と包容力があります。頼られると力を発揮しますが、抱え込みやすい面もあるので、人に任せる勇気も持てるとより楽になります。",
        "love": "安心できる居場所をつくるのが上手で、相手を丸ごと受け止めます。急がずじっくり関係を育てるほど、深い信頼で結ばれていきます。",
        "work": "腰を据えて物事を支える、周囲の土台となる存在です。金運は長い目でこつこつ築くほど安定し、堅実な蓄えが大きな安心になります。",
        "relations": "どっしり構えた安心感で、周囲から頼られる存在です。抱え込みやすいので、弱音を見せられる相手を持つと関係がより楽になります。",
    },
    "sono": {  # 苑 / 土陰
        "personality": "草木を育てる庭のように、人を丁寧に育て支える優しさを持っています。面倒見の良さが魅力ですが、尽くしすぎて自分を後回しにしやすいので、時には甘える側にも回ってください。",
        "love": "相手の成長を見守り、包み込むような愛情で関係を育てます。日々の小さな思いやりが、長く穏やかな絆につながっていきます。",
        "work": "人や場を丁寧に整え、みんなが力を出せる環境をつくる人です。金運は地道な積み重ねで安定し、人を育てた縁が巡り巡って実りになります。",
        "relations": "面倒見が良く、相手を気づかう優しさで慕われます。与えるばかりでなく、受け取ることも自分に許してあげてください。",
    },
    "rin": {  # 鈴 / 金陽
        "personality": "澄んだ鈴の音のように、まっすぐで潔い決断力を持つ人です。筋を通す強さが魅力ですが、白黒つけたい気持ちが強く出ると窮屈になるので、時にはゆるさも自分に許してあげてください。",
        "love": "誠実で一途、言ったことを守る姿勢が信頼を生みます。駆け引きより正直さを大切に、まっすぐ向き合える相手と長続きします。",
        "work": "決めるべき場面で迷わず動ける、頼れる意志の強さがあります。金運はけじめのある管理で堅実に増え、無駄を省く姿勢が実を結びます。",
        "relations": "筋を通す誠実さで、まっすぐな信頼関係を築きます。正論が強く出やすいので、相手の事情をくむ余白を持つと角が立ちません。",
    },
    "gyoku": {  # 玉 / 金陰
        "personality": "磨かれた宝玉のように、繊細な美意識と気品を備えた人です。質の高いものを見抜く目を持ちますが、完璧を求めすぎると疲れやすいので、程よい妥協も自分への優しさになります。",
        "love": "丁寧で品のある振る舞いが、相手に特別な心地よさを与えます。上辺でなく本物の誠実さを見せてくれる人と、深く結ばれていきます。",
        "work": "細部まで妥協しない仕事ぶりで、質の高さが評価されます。金運は良いものを見極める眼で堅実に育ち、価値あるものへの投資が生きます。",
        "relations": "礼儀正しく品のある振る舞いで、一目置かれる存在です。心を開くまで時間がかかるぶん、打ち解けた相手とは長く深い縁が続きます。",
    },
    "minato": {  # 湊 / 水陽
        "personality": "人が集う水辺のように、おおらかで人を惹きつける温かさがあります。懐が広く自然と輪の中心になりますが、頼まれると断りにくい面もあるので、無理はほどほどにしてください。",
        "love": "自然体で相手を安心させ、心地よい距離感をつくるのが上手です。包容力のある愛し方で、いろいろな人と穏やかに打ち解けられます。",
        "work": "人と人をつなぎ、機会を呼び込む求心力が持ち味です。金運は人の縁や流れに乗るほど広がり、開かれた姿勢が実入りを増やします。",
        "relations": "分け隔てなく人を受け入れ、自然と輪の中心になります。頼まれると断りにくいので、線引きを意識すると心地よい距離を保てます。",
    },
    "shizuku": {  # 雫 / 水陰
        "personality": "静かに落ちる露のように、豊かな感受性と鋭い直感を持つ人です。繊細に物事を感じ取れる一方、周りの空気を受けすぎて揺れやすいので、心を休める静かな時間を大切にしてください。",
        "love": "言葉にならない機微を感じ取り、深く相手に寄り添う恋をします。安心できる相手の前で、その豊かな内面がのびのびと花開きます。",
        "work": "直感とひらめきで本質をつかむ、感性を生かせる人です。金運は流れを読む勘で穏やかに保て、無理せず自然体でいるほど安定します。",
        "relations": "相手の気持ちの機微を敏感に察し、そっと寄り添えます。人の空気を受けやすいので、一人で心を整える時間を大切にしてください。",
    },
}

# --- 2. 五行の味付け: ELEMENT_FLAVOR[五行][section_id] ---
ELEMENT_FLAVOR: dict[str, dict[str, str]] = {
    "木": {
        "personality": "根を伸ばす木の性質は、前へ進もうとする向上心と、しなやかに立て直す回復力をあなたに添えています。",
        "love": "木の気は、共に育っていける関係にこそ心地よさを感じさせます。",
        "work": "木の気は、成長できる環境や学びの多い場でいっそう力を伸ばします。",
        "relations": "木の気は、共に伸びていける相手との交わりで、いっそう生き生きとします。",
    },
    "火": {
        "personality": "燃える火の性質は、情熱と表現力、そして人を温める明るさをあなたに添えています。",
        "love": "火の気は、気持ちを素直に伝え合える熱のある関係を心地よく感じさせます。",
        "work": "火の気は、人に伝え・表現する場面でこそ輝きを増します。",
        "relations": "火の気は、心を開いて語り合える相手との交わりを温かく感じます。",
    },
    "土": {
        "personality": "大地のような土の性質は、落ち着きと信頼感、人を支える包容力をあなたに添えています。",
        "love": "土の気は、安心と安定を積み重ねていける関係に心地よさを感じさせます。",
        "work": "土の気は、腰を据えて信頼を築く場でこそ真価を発揮します。",
        "relations": "土の気は、安心して寄りかかり合える落ち着いた関係を心地よく感じます。",
    },
    "金": {
        "personality": "磨かれた金の性質は、けじめと誠実さ、美しいものを見極める感性をあなたに添えています。",
        "love": "金の気は、筋の通った誠実な関係にこそ深い安心を感じさせます。",
        "work": "金の気は、精度や品質が問われる場でこそ評価につながります。",
        "relations": "金の気は、礼節と信義のある付き合いにこそ深い安心を感じます。",
    },
    "水": {
        "personality": "流れる水の性質は、柔軟さと深い感受性、人とつながる力をあなたに添えています。",
        "love": "水の気は、心の機微を分かち合える柔らかな関係を心地よく感じさせます。",
        "work": "水の気は、流れや人の縁を読み、しなやかに立ち回る場で生きます。",
        "relations": "水の気は、心のひだを分かち合える柔らかなつながりで満たされます。",
    },
}

# --- 3. 陰陽の味付け: YINYANG_FLAVOR[陰陽][section_id] ---
YINYANG_FLAVOR: dict[str, dict[str, str]] = {
    "陽": {
        "personality": "陽の巡りは、自分から動き、場をひらいていく能動的な力を後押しします。",
        "love": "恋でも自分から歩み寄るほど、良いご縁が動き出しやすいでしょう。",
        "work": "仕事では前に出て発信するほど、道が開けていきます。",
        "relations": "陽の巡りは、自分から声をかけ、輪を広げていく積極性を後押しします。",
    },
    "陰": {
        "personality": "陰の巡りは、じっくり受けとめ、細やかに整えていく落ち着いた力を後押しします。",
        "love": "恋では焦らず相手を受けとめるほど、信頼が静かに深まっていきます。",
        "work": "仕事では支え・整える立場でこそ、確かな信頼を得られます。",
        "relations": "陰の巡りは、相手をよく見て受けとめる、聞き上手な魅力を引き出します。",
    },
}


# 今年の運勢: 流年（その年の年干）の通変星ごとのメッセージ。
YEAR_FORTUNE_TEXT: dict[str, str] = {
    "比肩": "自分の足で立ち、仲間と対等に歩む力が高まる年です。自分の軸を大切にしつつ、協力できる場面では素直に手を取り合うと、実りが大きくなります。",
    "劫財": "行動力と勝負運が高まる一方、出費や競争も増えやすい年です。勢いは活かしつつ、大きな決断やお金の使い方は少し慎重にすると安心です。",
    "食神": "楽しみや表現がのびのびと広がる、豊かで穏やかな年です。好きなことに素直に取り組むほど、心も運も満たされていきます。",
    "傷官": "感性と才能が冴えわたる年です。表現やこだわりが光りますが、言葉がつい鋭くなりがちなので、伝え方をやわらげると人間関係が円満に運びます。",
    "偏財": "人脈やチャンスが広がり、フットワーク軽く動くほど得るものが多い年です。器用に立ち回れますが、あれもこれもと手を広げすぎない工夫を。",
    "正財": "堅実な積み重ねが実を結ぶ、信頼と安定の年です。地道な努力やコツコツした管理が、着実な形になって返ってきます。",
    "偏官": "挑戦とプレッシャーが力に変わる年です。ハードルは高めでも、逃げずに立ち向かうことで大きく成長できます。無理のないペース配分を忘れずに。",
    "正官": "責任や役割が高まり、まわりからの信用が育つ年です。けじめある振る舞いが評価につながります。背伸びしすぎず、誠実に務めるのが吉です。",
    "偏印": "学びやひらめき、新しい視点を得る変化の年です。興味の赴くままに知識を広げると、思わぬ道が開けます。ただし気移りには少し注意を。",
    "印綬": "まわりに支えられ、知識や安心を得られる穏やかな年です。学びや準備に向いた時期なので、じっくり土台を固めると後の飛躍につながります。",
}


@dataclass(frozen=True)
class SectionReading:
    """1 セクション分の鑑定文。JSON シリアライズ可能。"""

    section_id: str
    title: str
    text: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class Reading:
    """タイプの鑑定文一式。JSON シリアライズ可能。"""

    type_id: str
    名称: str
    読み: str
    五行: str
    陰陽: str
    headline: str
    sections: tuple[SectionReading, ...]
    compatibility_guide: CompatibilityGuide
    element_balance: FiveElementBalance | None = None
    year_fortune: dict | None = None

    def to_dict(self) -> dict:
        return {
            "type_id": self.type_id,
            "名称": self.名称,
            "読み": self.読み,
            "五行": self.五行,
            "陰陽": self.陰陽,
            "headline": self.headline,
            "sections": [s.to_dict() for s in self.sections],
            "compatibility_guide": self.compatibility_guide.to_dict(),
            "element_balance": (
                self.element_balance.to_dict() if self.element_balance else None
            ),
            "year_fortune": self.year_fortune,
        }


def _compose_section(t: ShoseiType, section_id: str) -> str:
    """3層（タイプ→五行→陰陽）を連結して1段落にする。"""
    parts = [
        TYPE_TEXT[t.type_id][section_id],
        ELEMENT_FLAVOR[t.五行][section_id],
        YINYANG_FLAVOR[t.陰陽][section_id],
    ]
    return "".join(parts)


def build_reading_for_type(
    t: ShoseiType,
    balance: FiveElementBalance | None = None,
    year_fortune: dict | None = None,
) -> Reading:
    """ShoseiType から鑑定文を組み立てる（決定的）。

    balance を渡すと「五行バランス」セクション（基本性格の直後）と
    element_balance フィールドが加わり、三柱の五行分布で個別化される。
    year_fortune を渡すと「今年の運勢」セクション（末尾）と year_fortune フィールドが加わる。
    どちらも None なら日干タイプのみに基づく（タイプの基準文）。
    """
    headline = f"{t.名称}（{t.読み}）― {t.一言特徴}【五行:{t.五行}／{t.陰陽}】"
    sections: list[SectionReading] = [
        SectionReading(section_id=sid, title=title, text=_compose_section(t, sid))
        for sid, title in SECTIONS
    ]
    if balance is not None:
        # 「基本性格・強み・課題」(index 0) の直後に五行バランスを挿入。
        sections.insert(
            1,
            SectionReading(
                section_id="balance",
                title="五行バランス",
                text=describe_balance(balance),
            ),
        )
    fortune_field = None
    if year_fortune is not None:
        sections.append(
            SectionReading(
                section_id="fortune_year",
                title="今年の運勢",
                text=year_fortune["text"],
            )
        )
        fortune_field = {k: v for k, v in year_fortune.items() if k != "text"}
    return Reading(
        type_id=t.type_id,
        名称=t.名称,
        読み=t.読み,
        五行=t.五行,
        陰陽=t.陰陽,
        headline=headline,
        sections=tuple(sections),
        compatibility_guide=compatibility_guide_for_type(t),
        element_balance=balance,
        year_fortune=fortune_field,
    )


def _build_year_fortune(
    value: _dt.date | _dt.datetime,
    reference_date: _dt.date,
    late_night_boundary: bool,
) -> dict:
    """流年（reference_date の年柱）× 日主 → 今年の運勢（通変星ベース）。"""
    day_stem = get_day_pillar(value, late_night_boundary=late_night_boundary).day_stem_index
    yp = get_year_pillar(reference_date)
    ten_god = get_ten_god(day_stem, yp.year_stem_index)
    text = (
        f"{yp.astrological_year}年（{yp.ganzhi_name}）は、あなたの日主から見て"
        f"「{ten_god}」が巡る年です。{YEAR_FORTUNE_TEXT[ten_god]}"
    )
    return {
        "reference_year": reference_date.year,
        "astrological_year": yp.astrological_year,
        "year_ganzhi": yp.ganzhi_name,
        "ten_god": ten_god,
        "text": text,
    }


def get_reading(
    value: _dt.date | _dt.datetime,
    *,
    late_night_boundary: bool = True,
    reference_date: _dt.date | None = None,
) -> Reading:
    """生年月日（＋時刻）→ 鑑定文（タイプ＋五行バランス＋今年の運勢で合成）。

    time を含む datetime を渡すと、五行バランスは四柱（時柱込み）で集計される。
    reference_date（既定=今日）の流年から「今年の運勢」を通変星で算出する。
    late_night_boundary=True（既定・論点A）: 23時以降は翌日の日干でタイプ・日柱を出す。
    """
    t = get_type(value, late_night_boundary=late_night_boundary)
    balance = get_five_element_balance(value, late_night_boundary=late_night_boundary)
    ref = reference_date or _dt.date.today()
    year_fortune = _build_year_fortune(value, ref, late_night_boundary)
    return build_reading_for_type(t, balance, year_fortune)
