import { View, StyleSheet, ScrollView, Alert } from 'react-native'
import { Text, Avatar, Card, List, Divider, Button } from 'react-native-paper'
import { router } from 'expo-router'
import { useAuthStore } from '../../stores/authStore'

const roleLabels: Record<string, string> = { OWNER: '管理层', PM: '项目经理', PROC: '采购', FIN: '财务', OPS: '运营' }

export default function MineScreen() {
  const user = useAuthStore((s) => s.user)
  const logout = useAuthStore((s) => s.logout)

  const handleLogout = () => {
    Alert.alert('确认', '确定要退出登录吗？', [
      { text: '取消', style: 'cancel' },
      { text: '确定', style: 'destructive', onPress: () => logout() },
    ])
  }

  return (
    <ScrollView style={styles.container}>
      <Card style={styles.profileCard}>
        <Card.Content style={styles.profileContent}>
          <Avatar.Text size={64} label={user?.realName?.charAt(0) ?? user?.username?.charAt(0) ?? 'U'} />
          <View style={styles.profileInfo}>
            <Text variant="titleLarge">{user?.realName ?? user?.username}</Text>
            <Text variant="bodyMedium" style={{ color: '#666' }}>
              {roleLabels[user?.role ?? ''] ?? user?.role}
            </Text>
          </View>
        </Card.Content>
      </Card>

      <Card style={styles.menuCard}>
        <List.Item title="设置" left={(props) => <List.Icon {...props} icon="cog-outline" />} onPress={() => router.push('/settings/')} />
        <Divider />
        <List.Item title="帮助与反馈" left={(props) => <List.Icon {...props} icon="help-circle-outline" />} onPress={() => router.push('/help/')} />
        <Divider />
        <List.Item title="关于" left={(props) => <List.Icon {...props} icon="information-outline" />} onPress={() => Alert.alert('关于', 'LG Management v1.0.0\n修船项目管理系统')} />
      </Card>

      <Button mode="outlined" onPress={handleLogout} textColor="#ff4d4f" style={styles.logoutBtn}>
        退出登录
      </Button>
    </ScrollView>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f7fa' },
  profileCard: { margin: 12, borderRadius: 12 },
  profileContent: { flexDirection: 'row', alignItems: 'center' },
  profileInfo: { marginLeft: 16 },
  menuCard: { margin: 12, borderRadius: 12 },
  logoutBtn: { margin: 12, borderColor: '#ff4d4f' },
})
