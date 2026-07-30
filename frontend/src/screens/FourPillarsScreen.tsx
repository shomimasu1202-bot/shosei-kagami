// 四柱画面: 生年月日（＋任意で時刻）→ 年・月・日・時の干支。

import { useState } from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';

import { fetchFourPillars, FourPillars } from '../api';
import { colors, elementColors, fonts } from '../theme';
import { Card, ErrorText, Field, PrimaryButton, SectionTitle } from '../components/ui';

function PillarColumn({
  label,
  stem,
  branch,
  element,
  sub,
}: {
  label: string;
  stem: string;
  branch: string;
  element?: string;
  sub?: string;
}) {
  const tint = element ? elementColors[element] : colors.muted;
  return (
    <View style={styles.col}>
      <Text style={styles.colLabel}>{label}</Text>
      <View style={[styles.gz, { borderColor: tint }]}>
        <Text style={styles.gzChar}>{stem}</Text>
        <Text style={styles.gzChar}>{branch}</Text>
      </View>
      <Text style={[styles.colElem, { color: tint }]}>{element ?? '—'}</Text>
      {sub ? <Text style={styles.colSub}>{sub}</Text> : <Text style={styles.colSub}> </Text>}
    </View>
  );
}

export function FourPillarsScreen() {
  const [date, setDate] = useState('1990-04-15');
  const [time, setTime] = useState('14:20');
  const [result, setResult] = useState<FourPillars | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit() {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      setResult(await fetchFourPillars(date, time));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
      <Card>
        <Field label="生年月日" value={date} onChangeText={setDate} placeholder="YYYY-MM-DD" />
        <Field
          label="出生時刻（任意）"
          value={time}
          onChangeText={setTime}
          placeholder="HH:MM（例 14:20）"
        />
        <PrimaryButton title="四柱を出す" onPress={onSubmit} loading={loading} />
        {error && <ErrorText message={error} />}
      </Card>

      {result && (
        <Card>
          <SectionTitle>四柱（命式）</SectionTitle>
          <View style={styles.pillarRow}>
            <PillarColumn
              label="年柱"
              stem={result.year.year_stem_name}
              branch={result.year.year_branch_name}
              element={result.year.五行}
              sub={`${result.year.astrological_year}年`}
            />
            <PillarColumn
              label="月柱"
              stem={result.month.month_stem_name}
              branch={result.month.month_branch_name}
              element={result.month.五行}
              sub={result.month.solar_term_name}
            />
            <PillarColumn
              label="日柱"
              stem={result.day.day_stem_name}
              branch={result.day.day_branch_name}
              sub="日主"
            />
            <PillarColumn
              label="時柱"
              stem={result.hour ? result.hour.hour_stem_name : '—'}
              branch={result.hour ? result.hour.hour_branch_name : '—'}
              element={result.hour?.五行}
              sub={result.hour ? result.hour.time_range : '時刻なし'}
            />
          </View>
          <Text style={styles.note}>
            ※ 年は立春、月は節入りで切り替わります。23時以降は翌日の日干で日柱・時柱を算出します。
          </Text>
        </Card>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  content: { padding: 16, paddingBottom: 40 },
  pillarRow: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 6 },
  col: { flex: 1, alignItems: 'center' },
  colLabel: { color: colors.subtext, fontSize: 13, marginBottom: 8, fontFamily: fonts.body },
  gz: {
    borderWidth: 2,
    borderRadius: 16,
    paddingVertical: 10,
    paddingHorizontal: 6,
    alignItems: 'center',
    backgroundColor: colors.cardAlt,
    minWidth: 46,
  },
  gzChar: { color: colors.text, fontSize: 26, fontFamily: fonts.title, lineHeight: 34 },
  colElem: { fontSize: 14, fontFamily: fonts.bold, marginTop: 8 },
  colSub: { color: colors.muted, fontSize: 11, marginTop: 2, textAlign: 'center', fontFamily: fonts.body },
  note: { color: colors.muted, fontSize: 11, marginTop: 16, lineHeight: 17, fontFamily: fonts.body },
});
