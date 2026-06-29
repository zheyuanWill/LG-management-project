import { useState } from 'react'
import { View, Text, TouchableOpacity, StyleSheet, ScrollView } from 'react-native'

interface Tab {
  key: string
  label: string
  count?: number
}

interface TabsBarProps {
  tabs: Tab[]
  activeKey: string
  onChange: (key: string) => void
}

export function TabsBar({ tabs, activeKey, onChange }: TabsBarProps) {
  return (
    <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.container}>
      {tabs.map((tab) => (
        <TouchableOpacity
          key={tab.key}
          onPress={() => onChange(tab.key)}
          style={[styles.tab, activeKey === tab.key && styles.activeTab]}
        >
          <Text style={[styles.label, activeKey === tab.key && styles.activeLabel]}>
            {tab.label}
            {tab.count != null && tab.count > 0 ? ` (${tab.count})` : ''}
          </Text>
        </TouchableOpacity>
      ))}
    </ScrollView>
  )
}

const styles = StyleSheet.create({
  container: { flexDirection: 'row', paddingHorizontal: 12, marginBottom: 8 },
  tab: { paddingHorizontal: 16, paddingVertical: 8, marginRight: 8, borderRadius: 20, backgroundColor: '#f5f5f5' },
  activeTab: { backgroundColor: '#1677ff' },
  label: { fontSize: 14, color: '#666' },
  activeLabel: { color: '#fff', fontWeight: '600' },
})
