import { View, ScrollView, StyleSheet, TouchableOpacity, RefreshControl } from 'react-native'
import { Text, Card, Avatar } from 'react-native-paper'
import { router } from 'expo-router'
import { useApiQuery } from '@lg/react-hooks'
import { useAuthStore } from '../../stores/authStore'
import { DataCard } from '../../components/DataCard'
import type { DashboardStats } from '@lg/api-client'

const roleLabels: Record<string, string> = { OWNER: '管理层', PM: '项目经理', PROC: '采购', FIN: '财务', OPS: '运营' }

const shortcuts = [
  { label: '搜索', icon: '🔍', route: '/(tabs)/search' },
  { label: '上传', icon: '📷', route: '/upload/' },
  { label: '审批', icon: '✅', route: '/approval/' },
  { label: '帮助', icon: '❓', route: '/help/' },
]

export default function HomeScreen() {
  const user = useAuthStore((s) => s.user)
  const { data: stats, isLoading, refetch } = useApiQuery<DashboardStats>(['dashboard-stats'], '/dashboard/stats')

  return (
    <ScrollView style={styles.container} refreshControl={<RefreshControl refreshing={isLoading} onRefresh={refetch} />}>
      <View style={styles.header}>
        <Avatar.Text size={48} label={user?.realName?.charAt(0) ?? user?.username?.charAt(0) ?? 'U'} />
        <View style={styles.headerText}>
          <Text variant="titleMedium">你好, {user?.realName ?? user?.username}</Text>
          <Text variant="bodySmall" style={{ color: '#999' }}>{roleLabels[user?.role ?? ''] ?? user?.role}</Text>
        </View>
      </View>

      <View style={styles.statsRow}>
        <DataCard value={stats?.active_orders ?? 0} label="待处理" color="#1677ff" />
        <DataCard value={stats?.pending_approval ?? 0} label="待审批" color="#faad14" />
        <DataCard value={stats?.overdue_nodes ?? 0} label="已逾期" color="#ff4d4f" />
      </View>

      <Text variant="titleSmall" style={styles.sectionTitle}>快捷操作</Text>
      <View style={styles.shortcutRow}>
        {shortcuts.map((s) => (
          <TouchableOpacity key={s.label} style={styles.shortcutItem} onPress={() => router.push(s.route as any)}>
            <Text style={styles.shortcutIcon}>{s.icon}</Text>
            <Text style={styles.shortcutLabel}>{s.label}</Text>
          </TouchableOpacity>
        ))}
      </View>
    </ScrollView>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f7fa' },
  header: { flexDirection: 'row', alignItems: 'center', padding: 16, backgroundColor: '#fff' },
  headerText: { marginLeft: 12 },
  statsRow: { flexDirection: 'row', paddingHorizontal: 12, marginTop: 12 },
  sectionTitle: { marginLeft: 16, marginTop: 20, marginBottom: 8 },
  shortcutRow: { flexDirection: 'row', justifyContent: 'space-around', backgroundColor: '#fff', paddingVertical: 16, marginHorizontal: 12, borderRadius: 12 },
  shortcutItem: { alignItems: 'center' },
  shortcutIcon: { fontSize: 28 },
  shortcutLabel: { fontSize: 12, color: '#666', marginTop: 4 },
})
