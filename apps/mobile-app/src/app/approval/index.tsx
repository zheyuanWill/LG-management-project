import { useState, useCallback } from 'react'
import { View, FlatList, StyleSheet, RefreshControl, Alert } from 'react-native'
import { Text, Card, Button } from 'react-native-paper'
import { TabsBar } from '../../components/TabsBar'
import { StatusBadge } from '../../components/StatusBadge'
import { EmptyState } from '../../components/EmptyState'
import { useApiQuery } from '@lg/react-hooks'
import { http } from '@lg/api-client'
import { formatDate, formatMoney, procurementStatusLabels } from '@lg/core'
import type { Procurement, PageResponse } from '@lg/api-client'
import { useQueryClient } from '@tanstack/react-query'

const tabs = [
  { key: 'PENDING_APPROVAL', label: '待审批' },
  { key: 'APPROVED', label: '已审批' },
]

export default function ApprovalScreen() {
  const [activeTab, setActiveTab] = useState('PENDING_APPROVAL')
  const queryClient = useQueryClient()

  const { data, isLoading, refetch } = useApiQuery<PageResponse<Procurement>>(
    ['approvals', activeTab], '/procurements', { status: activeTab, size: 50 }
  )

  const handleApprove = (id: number, approved: boolean) => {
    Alert.alert('确认', approved ? '确认审批通过？' : '确认驳回？', [
      { text: '取消', style: 'cancel' },
      {
        text: '确定',
        onPress: async () => {
          try {
            await http.post(`/procurements/${id}/approve`, { approved })
            queryClient.invalidateQueries({ queryKey: ['approvals'] })
          } catch (e) { Alert.alert('错误', e instanceof Error ? e.message : '操作失败') }
        },
      },
    ])
  }

  const renderItem = useCallback(({ item }: { item: Procurement }) => (
    <Card style={styles.card}>
      <Card.Content>
        <View style={styles.row}>
          <Text variant="titleSmall">{item.procurement_no}</Text>
          <StatusBadge status={item.status} label={procurementStatusLabels[item.status] ?? item.status} />
        </View>
        <Text variant="bodySmall" style={styles.meta}>
          {item.supplier_name ?? '-'} · {formatMoney(item.total_amount, item.currency)}
        </Text>
        {item.status === 'PENDING_APPROVAL' && (
          <View style={styles.actions}>
            <Button mode="contained" compact onPress={() => handleApprove(item.id, true)} style={styles.approveBtn}>通过</Button>
            <Button mode="outlined" compact onPress={() => handleApprove(item.id, false)} textColor="#ff4d4f" style={styles.rejectBtn}>驳回</Button>
          </View>
        )}
      </Card.Content>
    </Card>
  ), [])

  return (
    <View style={styles.container}>
      <TabsBar tabs={tabs} activeKey={activeTab} onChange={setActiveTab} />
      <FlatList
        data={data?.items ?? []}
        keyExtractor={(item) => String(item.id)}
        renderItem={renderItem}
        refreshControl={<RefreshControl refreshing={isLoading} onRefresh={refetch} />}
        ListEmptyComponent={!isLoading ? <EmptyState message="暂无审批" /> : null}
        contentContainerStyle={(data?.items ?? []).length === 0 ? { flex: 1 } : undefined}
      />
    </View>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f7fa', paddingTop: 8 },
  card: { marginHorizontal: 12, marginBottom: 8, borderRadius: 10 },
  row: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  meta: { color: '#999', marginTop: 4 },
  actions: { flexDirection: 'row', gap: 8, marginTop: 12 },
  approveBtn: { flex: 1 },
  rejectBtn: { flex: 1, borderColor: '#ff4d4f' },
})
