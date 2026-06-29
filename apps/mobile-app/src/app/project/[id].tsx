import { View, ScrollView, StyleSheet, RefreshControl } from 'react-native'
import { Text, Card, Divider, Chip, ActivityIndicator } from 'react-native-paper'
import { useLocalSearchParams } from 'expo-router'
import { useApiQuery } from '@lg/react-hooks'
import { StatusBadge } from '../../components/StatusBadge'
import { formatDate, formatMoney, orderStatusLabels, nodeStatusLabels } from '@lg/core'
import type { Order, TrackingNode, PageResponse } from '@lg/api-client'

export default function ProjectDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>()

  const { data: order, isLoading } = useApiQuery<Order>(
    ['order', id], `/orders/${id}`, undefined, { enabled: !!id }
  )
  const { data: nodesData } = useApiQuery<PageResponse<TrackingNode>>(
    ['tracking-nodes', id], '/tracking/nodes', { order_id: id, size: 50 }, { enabled: !!id }
  )

  if (isLoading) return <ActivityIndicator style={{ marginTop: 100 }} />
  if (!order) return <Text style={{ textAlign: 'center', marginTop: 100 }}>订单不存在</Text>

  const nodes = nodesData?.items ?? []

  return (
    <ScrollView style={styles.container}>
      <Card style={styles.card}>
        <Card.Content>
          <View style={styles.row}>
            <Text variant="titleMedium">{order.order_no}</Text>
            <StatusBadge status={order.status} label={orderStatusLabels[order.status] ?? order.status} />
          </View>
          <Divider style={{ marginVertical: 12 }} />
          <InfoRow label="客户" value={order.customer_name ?? '-'} />
          <InfoRow label="船舶" value={order.vessel_name ?? '-'} />
          <InfoRow label="项目经理" value={order.pm_name ?? '-'} />
          <InfoRow label="金额" value={formatMoney(order.total_amount, order.currency)} />
          <InfoRow label="交付日期" value={order.delivery_date ? formatDate(order.delivery_date) : '-'} />
          <InfoRow label="备注" value={order.notes ?? '-'} />
        </Card.Content>
      </Card>

      <Text variant="titleSmall" style={styles.sectionTitle}>跟踪节点 ({nodes.length})</Text>
      {nodes.map((node) => (
        <Card key={node.id} style={styles.card}>
          <Card.Content>
            <View style={styles.row}>
              <Text variant="titleSmall">{node.name}</Text>
              <StatusBadge status={node.status} label={nodeStatusLabels[node.status] ?? node.status} />
            </View>
            <Text variant="bodySmall" style={styles.meta}>
              {node.assignee_name ?? '-'} · 计划: {node.planned_date ? formatDate(node.planned_date) : '-'}
            </Text>
            {node.actual_date && <Text variant="bodySmall" style={styles.meta}>实际: {formatDate(node.actual_date)}</Text>}
          </Card.Content>
        </Card>
      ))}
    </ScrollView>
  )
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginBottom: 8 }}>
      <Text variant="bodyMedium" style={{ color: '#666' }}>{label}</Text>
      <Text variant="bodyMedium">{value}</Text>
    </View>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f7fa' },
  card: { margin: 12, marginBottom: 4, borderRadius: 10 },
  row: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  meta: { color: '#999', marginTop: 4 },
  sectionTitle: { marginLeft: 16, marginTop: 16, marginBottom: 4 },
})
