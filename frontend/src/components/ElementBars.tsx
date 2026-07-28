// 五行バランスの横棒グラフ（木火土金水）。

import { DimensionValue, StyleSheet, Text, View } from 'react-native';

import { ELEMENTS, elementColors, colors } from '../theme';
import { ElementBalance } from '../api';

export function ElementBars({ balance }: { balance: ElementBalance }) {
  const max = Math.max(1, ...ELEMENTS.map((e) => balance.percentages[e] ?? 0));
  return (
    <View>
      {ELEMENTS.map((e) => {
        const pct = balance.percentages[e] ?? 0;
        const isDominant = balance.dominant.includes(e);
        const isLacking = balance.lacking.includes(e);
        const width = `${(pct / max) * 100}%` as DimensionValue;
        return (
          <View key={e} style={styles.row}>
            <Text style={styles.label}>{e}</Text>
            <View style={styles.track}>
              <View
                style={[styles.fill, { width, backgroundColor: elementColors[e] }]}
              />
            </View>
            <Text style={[styles.pct, isDominant && styles.dominant, isLacking && styles.lacking]}>
              {pct}%
              {isDominant ? ' ▲' : ''}
              {isLacking ? ' ×' : ''}
            </Text>
          </View>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: 'row', alignItems: 'center', marginVertical: 4 },
  label: { color: colors.text, width: 22, fontSize: 15, fontWeight: '700' },
  track: {
    flex: 1,
    height: 14,
    backgroundColor: colors.cardAlt,
    borderRadius: 7,
    overflow: 'hidden',
    marginHorizontal: 8,
  },
  fill: { height: '100%', borderRadius: 7 },
  pct: { color: colors.subtext, width: 62, fontSize: 12, textAlign: 'right' },
  dominant: { color: colors.accent, fontWeight: '700' },
  lacking: { color: colors.muted },
});
