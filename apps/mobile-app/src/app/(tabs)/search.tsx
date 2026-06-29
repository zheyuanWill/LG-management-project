import { useState, useCallback } from 'react'
import { View, FlatList, StyleSheet, TouchableOpacity } from 'react-native'
import { Searchbar, Text, Card, Chip } from 'react-native-paper'
import { router } from 'expo-router'
import { useApiQuery } from '@lg/react-hooks'
import { EmptyState } from '../../components/EmptyState'
import { formatMoney } from '@lg/core'
import type { Order, PageResponse } from '@lg/api-client'

export default function SearchScreen() {
  const [query, setQuery] = useState('')
  const [searchKeyword, setSearchKeyword] = useState('')

  const { data, isLoading } = useApiQuery<PageResponse<Order>>(
    ['search', searchKeyword], '/orders', { keyword: searchKeyword, size: 30 },
    { enabled: !!searchKeyword }
  )

  const handleSearch = () => {
    if (query.trim()) setSearchKeyword(query.trim())
  }

  const renderItem = useCallback(({ item }: { item: Order }) => (
    <TouchableOpacity onPress={() => router.push({ pathname: '/project/[id]', params: { id: String(item.id) } })}>
      <Card style={styles.card}>
        <Card.Content>
          <Text variant="titleSmall">{item.order_no}</Text>
          <Text variant="bodySmall" style={styles.meta}>
            {item.customer_name} · {formatMoney(item.total_amount, item.currency)}
          </Text>
        </Card.Content>
      </Card>
    </TouchableOpacity>
  ), [])

  return (
    <View style={styles.container}>
      <Searchbar
        placeholder="搜索订单号/客户名称"
        value={query}
        onChangeText={setQuery}
        onSubmitEditing={handleSearch}
        style={styles.searchbar}
      />
      <FlatList
        data={data?.items ?? []}
        keyExtractor={(item) => String(item.id)}
        renderItem={renderItem}
        ListEmptyComponent={!isLoading && searchKeyword ? <EmptyState message="未找到相关结果" /> : null}
        contentContainerStyle={(data?.items ?? []).length === 0 ? { flex: 1 } : undefined}
      />
    </View>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f7fa' },
  searchbar: { margin: 12, borderRadius: 10 },
  card: { marginHorizontal: 12, marginBottom: 8, borderRadius: 10 },
  meta: { color: '#999', marginTop: 4 },
})
