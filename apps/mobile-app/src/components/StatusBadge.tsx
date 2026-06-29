import { View, Text, StyleSheet } from 'react-native'

const colorMap: Record<string, { bg: string; text: string }> = {
  PENDING: { bg: '#f0f0f0', text: '#666' },
  IN_PROGRESS: { bg: '#e6f4ff', text: '#1677ff' },
  COMPLETED: { bg: '#f6ffed', text: '#52c41a' },
  CANCELLED: { bg: '#fff2f0', text: '#ff4d4f' },
  OVERDUE: { bg: '#fff2f0', text: '#ff4d4f' },
  DRAFT: { bg: '#f0f0f0', text: '#666' },
  APPROVED: { bg: '#f6ffed', text: '#52c41a' },
  REJECTED: { bg: '#fff2f0', text: '#ff4d4f' },
  SUBMITTED: { bg: '#e6f4ff', text: '#1677ff' },
  PENDING_APPROVAL: { bg: '#fffbe6', text: '#faad14' },
}

interface StatusBadgeProps {
  status: string
  label: string
}

export function StatusBadge({ status, label }: StatusBadgeProps) {
  const colors = colorMap[status] ?? colorMap.PENDING
  return (
    <View style={[styles.badge, { backgroundColor: colors.bg }]}>
      <Text style={[styles.text, { color: colors.text }]}>{label}</Text>
    </View>
  )
}

const styles = StyleSheet.create({
  badge: { paddingHorizontal: 8, paddingVertical: 2, borderRadius: 4 },
  text: { fontSize: 12, fontWeight: '500' },
})
