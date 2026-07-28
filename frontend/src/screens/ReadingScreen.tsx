// 鑑定画面: 生年月日（＋任意で時刻）→ タイプ・五行バランス・鑑定文・相性ガイド。

import { useState } from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';

import { fetchReading, Reading } from '../api';
import { colors, elementColors } from '../theme';
import { Card, ErrorText, Field, PrimaryButton, SectionTitle } from '../components/ui';
import { ElementBars } from '../components/ElementBars';

export function ReadingScreen() {
  const [date, setDate] = useState('1990-04-15');
  const [time, setTime] = useState('');
  const [result, setResult] = useState<Reading | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit() {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      setResult(await fetchReading(date, time));
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
          label="出生時刻（任意・四柱になります）"
          value={time}
          onChangeText={setTime}
          placeholder="HH:MM（例 14:20）"
        />
        <PrimaryButton title="鑑定する" onPress={onSubmit} loading={loading} />
        {error && <ErrorText message={error} />}
      </Card>

      {result && (
        <>
          <Card style={{ backgroundColor: elementColors[result.五行] + '22' }}>
            <Text style={styles.typeName}>
              {result.名称}
              <Text style={styles.typeReading}>（{result.読み}）</Text>
            </Text>
            <Text style={styles.typeMeta}>
              五行: {result.五行} ／ 陰陽: {result.陰陽}
            </Text>
          </Card>

          {result.element_balance && (
            <Card>
              <SectionTitle>
                五行バランス（{result.element_balance.pillar_count === 4 ? '四柱' : '三柱'}
                {result.element_balance.include_hidden_stems ? '・蔵干込み' : ''}）
              </SectionTitle>
              <ElementBars balance={result.element_balance} />
              <Text style={styles.balanceComment}>{result.element_balance.comment}</Text>
            </Card>
          )}

          {result.sections.map((sec) => (
            <Card key={sec.section_id}>
              <SectionTitle>{sec.title}</SectionTitle>
              <Text style={styles.body}>{sec.text}</Text>
            </Card>
          ))}

          <Card>
            <SectionTitle>相性のヒント</SectionTitle>
            <View style={styles.chipRow}>
              <Text style={styles.chipLabelGood}>好相性</Text>
              <Text style={styles.chipText}>{result.compatibility_guide.best.join('・') || '—'}</Text>
            </View>
            <View style={styles.chipRow}>
              <Text style={styles.chipLabelCaution}>要注意</Text>
              <Text style={styles.chipText}>
                {result.compatibility_guide.caution.join('・') || '—'}
              </Text>
            </View>
          </Card>
        </>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  content: { padding: 16, paddingBottom: 40 },
  typeName: { color: colors.text, fontSize: 32, fontWeight: '700' },
  typeReading: { color: colors.subtext, fontSize: 18, fontWeight: '400' },
  typeMeta: { color: colors.subtext, fontSize: 15, marginTop: 6 },
  balanceComment: { color: colors.subtext, fontSize: 13, marginTop: 10 },
  body: { color: colors.text, fontSize: 15, lineHeight: 25 },
  chipRow: { flexDirection: 'row', alignItems: 'center', marginTop: 8 },
  chipLabelGood: {
    color: colors.good,
    fontWeight: '700',
    width: 64,
    fontSize: 14,
  },
  chipLabelCaution: {
    color: colors.caution,
    fontWeight: '700',
    width: 64,
    fontSize: 14,
  },
  chipText: { color: colors.text, fontSize: 15, flex: 1 },
});
