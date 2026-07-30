import { useState } from 'react';
import {
  ActivityIndicator,
  SafeAreaView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { useFonts } from 'expo-font';

import { colors, fonts } from './src/theme';
import { ReadingScreen } from './src/screens/ReadingScreen';
import { FourPillarsScreen } from './src/screens/FourPillarsScreen';
import { CompatibilityScreen } from './src/screens/CompatibilityScreen';

type Tab = 'reading' | 'pillars' | 'compat';

const TABS: { key: Tab; label: string; icon: string }[] = [
  { key: 'reading', label: '鑑定', icon: '🔮' },
  { key: 'pillars', label: '四柱', icon: '🌙' },
  { key: 'compat', label: '相性', icon: '💕' },
];

// 背景の飾り（星・花）。ふんわり散りばめる。
const DECOR: { emoji: string; top: string; left: string; size: number; op: number }[] = [
  { emoji: '🌸', top: '6%', left: '82%', size: 30, op: 0.5 },
  { emoji: '✨', top: '14%', left: '8%', size: 22, op: 0.6 },
  { emoji: '🌙', top: '30%', left: '88%', size: 24, op: 0.35 },
  { emoji: '⭐', top: '44%', left: '5%', size: 18, op: 0.4 },
  { emoji: '🌷', top: '58%', left: '90%', size: 24, op: 0.4 },
  { emoji: '💫', top: '70%', left: '10%', size: 22, op: 0.4 },
  { emoji: '🌸', top: '84%', left: '80%', size: 26, op: 0.45 },
  { emoji: '✨', top: '92%', left: '20%', size: 20, op: 0.5 },
];

export default function App() {
  const [tab, setTab] = useState<Tab>('reading');
  // 特定の .ttf だけを require（パッケージindex経由だと全ウェイトが同梱され重くなるため）。
  const [fontsLoaded] = useFonts({
    ZenMaruGothic_400Regular: require('@expo-google-fonts/zen-maru-gothic/400Regular/ZenMaruGothic_400Regular.ttf'),
    MochiyPopOne_400Regular: require('@expo-google-fonts/mochiy-pop-one/400Regular/MochiyPopOne_400Regular.ttf'),
  });

  if (!fontsLoaded) {
    return (
      <SafeAreaView style={[styles.container, styles.center]}>
        <ActivityIndicator color={colors.accent} size="large" />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar style="dark" />

      {/* 背景の飾り */}
      <View style={styles.decorLayer} pointerEvents="none">
        {DECOR.map((d, i) => (
          <Text
            key={i}
            style={{
              position: 'absolute',
              top: d.top as any,
              left: d.left as any,
              fontSize: d.size,
              opacity: d.op,
            }}
          >
            {d.emoji}
          </Text>
        ))}
      </View>

      <View style={styles.header}>
        <Text style={styles.title}>✿ 掌星鑑 ✿</Text>
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
  center: { justifyContent: 'center', alignItems: 'center' },
  decorLayer: { ...StyleSheet.absoluteFillObject },
  header: { paddingHorizontal: 20, paddingTop: 14, paddingBottom: 6, alignItems: 'center' },
  title: { color: colors.accent, fontSize: 30, fontFamily: fonts.title, letterSpacing: 2 },
  subtitle: { color: colors.subtext, fontSize: 13, marginTop: 6, fontFamily: fonts.body },
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
  tabLabel: { color: colors.muted, fontSize: 12, marginTop: 2, fontFamily: fonts.bold },
  tabActive: { color: colors.accent, opacity: 1 },
});
