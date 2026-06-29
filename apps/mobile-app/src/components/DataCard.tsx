import { View, Text, StyleSheet } from 'react-native'
import { Card } from 'react-native-paper'

interface DataCardProps {
  value: number | string
  label: string
  subtitle?: string
  color?: string
}

export function DataCard({ value, label, subtitle, color = '#1677ff' }: DataCardProps) {
  return (
    <Card style={styles.card}>
      <Card.Content>
        <Text style={[styles.value, { color }]}>{value}</Text>
        <Text style={styles.label}>{label}</Text>
        {subtitle && <Text style={styles.subtitle}>{subtitle}</Text>}
      </Card.Content>
    </Card>
  )
}

const styles = StyleSheet.create({
  card: { flex: 1, margin: 4 },
  value: { fontSize: 24, fontWeight: '700' },
  label: { fontSize: 13, color: '#666', marginTop: 4 },
  subtitle: { fontSize: 11, color: '#999', marginTop: 2 },
})
