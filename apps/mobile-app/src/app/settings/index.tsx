import { View, StyleSheet, ScrollView, Alert } from 'react-native'
import { Text, Card, List, Switch, Divider, Button } from 'react-native-paper'
import { useState } from 'react'

export default function SettingsScreen() {
  const [notifications, setNotifications] = useState(true)
  const [autoUpdate, setAutoUpdate] = useState(false)

  const clearCache = () => {
    Alert.alert('确认', '确定要清除缓存吗？', [
      { text: '取消', style: 'cancel' },
      { text: '确定', onPress: () => Alert.alert('成功', '缓存已清除') },
    ])
  }

  return (
    <ScrollView style={styles.container}>
      <Card style={styles.card}>
        <List.Item
          title="消息通知"
          description="接收推送通知"
          right={() => <Switch value={notifications} onValueChange={setNotifications} />}
        />
        <Divider />
        <List.Item
          title="自动更新"
          description="自动下载新版本"
          right={() => <Switch value={autoUpdate} onValueChange={setAutoUpdate} />}
        />
      </Card>

      <Card style={styles.card}>
        <List.Item title="清除缓存" description="清除本地缓存数据" onPress={clearCache} right={(props) => <List.Icon {...props} icon="chevron-right" />} />
        <Divider />
        <List.Item title="修改密码" description="更改登录密码" onPress={() => Alert.alert('提示', '功能开发中')} right={(props) => <List.Icon {...props} icon="chevron-right" />} />
      </Card>

      <Text variant="bodySmall" style={styles.version}>版本 1.0.0</Text>
    </ScrollView>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f7fa' },
  card: { margin: 12, borderRadius: 12 },
  version: { textAlign: 'center', color: '#999', marginTop: 24 },
})
