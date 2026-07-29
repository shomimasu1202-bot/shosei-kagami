import { useState } from 'react';
import { SafeAreaView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { StatusBar } from 'expo-status-bar';

import { colors } from './src/theme';
import { ReadingScreen } from './src/screens/ReadingScreen';
import { FourPillarsScreen } from './src/screens/FourPillarsScreen';
import { CompatibilityScreen } from './src/screens/CompatibilityScreen';

type Tab = 'reading' | 'pillars' | 'compat';

const TABS: { key: Tab; label: string; icon: string }[] = [
  { key: 'reading', label: '鑑定', icon: '🔮' },
  { key: 'pillars', label: '四柱', icon: '🌙' },
  { key: 'compat', label: '相性', icon: '💕' },
];

export default function App() {
  const [tab, setTab] = useState<Tab>('reading');

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar style="dark" />
      <View style={styles.header}>
        <Text style={styles.title}>✨ 掌星鑑 ✨</Text>
        <Text style={styles.subtitle}>
          {tab === 'reading' ? '🌸 生年月日から性格を診断' : null}
          {tab === 'pillars' ? '🌙 四柱（命式）を算出' : null}
          {tab === 'compat' ? '💕 二人の相性を占う' : null}
        </Text>
      </View>

      <View style={styles.screen}>
        {tab === 'reading' && <ReadingScreen />}
        {tab === 'pillars' && <FourPillarsScreen />}
        {tab === 'compat' && <CompatibilityScreen />}
      </View>

      <View style={styles.tabBar}>
        {TABS.map((t) => {
          const active = t.key === tab;
          return (
            <TouchableOpacity
              key={t.key}
              style={styles.tabItem}
              onPress={() => setTab(t.key)}
              activeOpacity={0.7}
            >
              <Text style={[styles.tabIcon, active && styles.tabActive]}>{t.icon}</Text>
              <Text style={[styles.tabLabel, active && styles.tabActive]}>{t.label}</Text>
            </TouchableOpacity>
          );
        })}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  header: { paddingHorizontal: 20, paddingTop: 14, paddingBottom: 6, alignItems: 'center' },
  title: { color: colors.accent, fontSize: 30, fontWeight: '800', letterSpacing: 2 },
  subtitle: { color: colors.subtext, fontSize: 13, marginTop: 4 },
  screen: { flex: 1 },
  tabBar: {
    flexDirection: 'row',
    backgroundColor: colors.card,
    borderTopWidth: 1,
    borderTopColor: colors.border,
    paddingBottom: 8,
    paddingTop: 4,
  },
  tabItem: { flex: 1, alignItems: 'center', paddingVertical: 8 },
  tabIcon: { fontSize: 24, opacity: 0.45 },
  tabLabel: { color: colors.muted, fontSize: 12, marginTop: 2, fontWeight: '600' },
  tabActive: { color: colors.accent, opacity: 1 },
});
