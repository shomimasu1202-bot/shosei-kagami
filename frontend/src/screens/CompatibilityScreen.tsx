// 相性画面: 2人の生年月日 → 五行の相生・相剋による相性。

import { useState } from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';

import { fetchCompatibility, Compatibility } from '../api';
import { colors, levelColor } from '../theme';
import { Card, ErrorText, Field, PrimaryButton, SectionTitle } from '../components/ui';

const LEVEL_LABEL: Record<string, string> = {
  '◎': 'とても良い相性',
  '○': '気の合う相性',
  '△': '刺激し合う相性',
};

export function CompatibilityScreen() {
  const [dateA, setDateA] = useState('1990-04-15');
  const [dateB, setDateB] = useState('1988-11-03');
  const [result, setResult] = useState<Compatibility | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit() {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      setResult(await fetchCompatibility(dateA, dateB));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
      <Card>
        <Field label="あなたの生年月日" value={dateA} onChangeText={setDateA} placeholder="YYYY-MM-DD" />
        <Field label="お相手の生年月日" value={dateB} onChangeText={setDateB} placeholder="YYYY-MM-DD" />
        <PrimaryButton title="相性を見る" onPress={onSubmit} loading={loading} />
        {error && <ErrorText message={error} />}
      </Card>

      {result && (
        <Card>
          <View style={styles.pairRow}>
            <Text style={styles.pairName}>{result.名称_a}</Text>
            <Text style={styles.pairX}>×</Text>
            <Text style={styles.pairName}>{result.名称_b}</Text>
          </View>

          <View style={[styles.levelBadge, { borderColor: levelColor(result.level) }]}>
            <Text style={[styles.levelMark, { color: levelColor(result.level) }]}>
              {result.level}
            </Text>
            <Text style={styles.levelLabel}>{LEVEL_LABEL[result.level] ?? ''}</Text>
          </View>

          <SectionTitle>{result.relation}（{result.direction}）</SectionTitle>
          <Text style={styles.body}>{result.comment}</Text>
        </Card>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  content: { padding: 16, paddingBottom: 40 },
  pairRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center' },
  pairName: { color: colors.text, fontSize: 26, fontWeight: '700' },
  pairX: { color: colors.subtext, fontSize: 20, marginHorizontal: 16 },
  levelBadge: {
    alignSelf: 'center',
    alignItems: 'center',
    borderWidth: 2,
    borderRadius: 100,
    width: 130,
    height: 130,
    justifyContent: 'center',
    marginVertical: 18,
  },
  levelMark: { fontSize: 52, fontWeight: '700', lineHeight: 58 },
  levelLabel: { color: colors.subtext, fontSize: 13, marginTop: 2 },
  body: { color: colors.text, fontSize: 15, lineHeight: 25, marginTop: 4 },
});
