import { useState, useCallback } from 'react'
import { View, FlatList, StyleSheet, TouchableOpacity, RefreshControl } from 'react-native'
import { Text, Card } from 'react-native-paper'
import { router } from 'expo-router'
import { StatusBadge } from '../../components/StatusBadge'
import { EmptyState } from '../../components/EmptyState'
import { TabsBar } from '../../components/TabsBar'
import { useTasks } from '../../hooks/useTasks'
import { nodeStatusLabels } from '@lg/core'
import { formatDate } from '@lg/core'
import type { TrackingNode } from '@lg/api-client'

const tabs = [
  { key: 'all', label: '全部' },
  { key: 'PENDING', label: '待处理' },
  { key: 'IN_PROGRESS', label: '进行中' },
  { key: 'COMPLETED', label: '已完成' },
]

export default function TaskScreen() {
  const [activeTab, setActiveTab] = useState('all')
  const params = activeTab === 'all' ? {} : { status: activeTab }
  const { data, isLoading, refetch } = useTasks(params)
  const items = data?.items ?? []

  const renderItem = useCallback(({ item }: { item: TrackingNode }) => (
    <TouchableOpacity onPress={() => router.push({ pathname: '/project/[id]', params: { id: String(item.order_id) } })}>
      <Card style={styles.card}>
        <Card.Content>
          <View style={styles.row}>
            <Text variant="titleSmall" style={{ flex: 1 }}>{item.name}</Text>
            <StatusBadge status={item.status} label={nodeStatusLabels[item.status] ?? item.status} />
          </View>
          <Text variant="bodySmall" style={styles.meta}>订单: {item.order_no ?? '-'} · {item.assignee_name ?? '-'}</Text>
          {item.planned_date && <Text variant="bodySmall" style={styles.meta}>计划: {formatDate(item.planned_date)}</Text>}
        </Card.Content>
      </Card>
    </TouchableOpacity>
  ), [])

  return (
    <View style={styles.container}>
      <TabsBar tabs={tabs} activeKey={activeTab} onChange={setActiveTab} />
      <FlatList
        data={items}
        keyExtractor={(item) => String(item.id)}
        renderItem={renderItem}
        refreshControl={<RefreshControl refreshing={isLoading} onRefresh={refetch} />}
        ListEmptyComponent={!isLoading ? <EmptyState message="暂无任务" /> : null}
        contentContainerStyle={items.length === 0 ? { flex: 1 } : undefined}
      />
    </View>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f7fa', paddingTop: 8 },
  card: { marginHorizontal: 12, marginBottom: 8, borderRadius: 10 },
  row: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  meta: { color: '#999', marginTop: 4 },
})
