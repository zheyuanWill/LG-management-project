import { useCallback } from 'react'
import { View, FlatList, StyleSheet, RefreshControl } from 'react-native'
import { Text, Card, Badge } from 'react-native-paper'
import { useApiQuery } from '@lg/react-hooks'
import { EmptyState } from '../../components/EmptyState'
import { formatDate } from '@lg/core'
import type { Notification, PageResponse } from '@lg/api-client'

const typeLabels: Record<string, string> = { APPROVAL: '审批', OVERDUE: '逾期', PAYMENT: '付款', SYSTEM: '系统', INFO: '通知' }
const typeColors: Record<string, string> = { APPROVAL: '#faad14', OVERDUE: '#ff4d4f', PAYMENT: '#52c41a', SYSTEM: '#1677ff', INFO: '#999' }

export default function MessageScreen() {
  const { data, isLoading, refetch } = useApiQuery<PageResponse<Notification>>(
    ['notifications'], '/notifications', { size: 50 }
  )
  const items = data?.items ?? []

  const renderItem = useCallback(({ item }: { item: Notification }) => (
    <Card style={[styles.card, !item.is_read && styles.unread]}>
      <Card.Content>
        <View style={styles.row}>
          <View style={[styles.typeBadge, { backgroundColor: typeColors[item.type] ?? '#999' }]}>
            <Text style={styles.typeText}>{typeLabels[item.type] ?? item.type}</Text>
          </View>
          <Text variant="bodySmall" style={styles.time}>{formatDate(item.created_at)}</Text>
        </View>
        <Text variant="titleSmall" style={{ marginTop: 6 }}>{item.title}</Text>
        <Text variant="bodySmall" style={styles.content}>{item.content}</Text>
      </Card.Content>
    </Card>
  ), [])

  return (
    <View style={styles.container}>
      <FlatList
        data={items}
        keyExtractor={(item) => String(item.id)}
        renderItem={renderItem}
        refreshControl={<RefreshControl refreshing={isLoading} onRefresh={refetch} />}
        ListEmptyComponent={!isLoading ? <EmptyState message="暂无消息" /> : null}
        contentContainerStyle={items.length === 0 ? { flex: 1 } : undefined}
      />
    </View>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f7fa' },
  card: { marginHorizontal: 12, marginTop: 8, borderRadius: 10 },
  unread: { borderLeftWidth: 3, borderLeftColor: '#1677ff' },
  row: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  typeBadge: { paddingHorizontal: 8, paddingVertical: 2, borderRadius: 4 },
  typeText: { color: '#fff', fontSize: 11, fontWeight: '600' },
  time: { color: '#999' },
  content: { color: '#666', marginTop: 4 },
})
