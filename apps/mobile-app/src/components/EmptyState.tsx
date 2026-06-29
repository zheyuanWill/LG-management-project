import { View, Text, StyleSheet } from 'react-native'

interface EmptyStateProps {
  message?: string
}

export function EmptyState({ message = '暂无数据' }: EmptyStateProps) {
  return (
    <View style={styles.container}>
      <Text style={styles.icon}>📭</Text>
      <Text style={styles.text}>{message}</Text>
    </View>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 40 },
  icon: { fontSize: 48, marginBottom: 12 },
  text: { fontSize: 14, color: '#999' },
})
