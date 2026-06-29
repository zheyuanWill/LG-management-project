import { useState } from 'react'
import { View, StyleSheet, KeyboardAvoidingView, Platform, ScrollView } from 'react-native'
import { TextInput, Button, Text, Card } from 'react-native-paper'
import { router } from 'expo-router'
import { useAuthStore } from '../../stores/authStore'

const quickAccounts = [
  { username: 'owner', password: 'owner123', label: '老板' },
  { username: 'pm', password: 'pm123', label: '项目经理' },
  { username: 'proc', password: 'proc123', label: '采购' },
  { username: 'fin', password: 'fin123', label: '财务' },
  { username: 'ops', password: 'ops123', label: '仓库' },
]

export default function LoginScreen() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const login = useAuthStore((s) => s.login)

  const handleLogin = async () => {
    if (!username || !password) {
      setError('请输入用户名和密码')
      return
    }
    try {
      setLoading(true)
      setError('')
      await login(username, password)
      router.replace('/(tabs)')
    } catch (e) {
      setError(e instanceof Error ? e.message : '登录失败')
    } finally {
      setLoading(false)
    }
  }

  const quickLogin = async (acc: { username: string; password: string }) => {
    setUsername(acc.username)
    setPassword(acc.password)
    try {
      setLoading(true)
      setError('')
      await login(acc.username, acc.password)
      router.replace('/(tabs)')
    } catch (e) {
      setError(e instanceof Error ? e.message : '登录失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <KeyboardAvoidingView style={styles.container} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <View style={styles.header}>
          <Text variant="headlineLarge" style={styles.title}>LG Management</Text>
          <Text variant="bodyMedium" style={styles.subtitle}>
            修船项目管理 & 供应链系统
          </Text>
        </View>

        <Card style={styles.card}>
          <Card.Content>
            <Text variant="titleLarge" style={styles.cardTitle}>欢迎登录</Text>

            <TextInput
              label="用户名"
              value={username}
              onChangeText={setUsername}
              mode="outlined"
              style={styles.input}
              autoCapitalize="none"
            />
            <TextInput
              label="密码"
              value={password}
              onChangeText={setPassword}
              mode="outlined"
              secureTextEntry
              style={styles.input}
            />

            {error ? <Text style={styles.error}>{error}</Text> : null}

            <Button mode="contained" onPress={handleLogin} loading={loading} style={styles.button}>
              登录
            </Button>

            {__DEV__ && (
              <View style={styles.quickSection}>
                <Text variant="bodySmall" style={styles.quickLabel}>快速登录（开发环境）</Text>
                <View style={styles.quickRow}>
                  {quickAccounts.map((acc) => (
                    <Button key={acc.username} mode="outlined" compact onPress={() => quickLogin(acc)} style={styles.quickBtn}>
                      {acc.label}
                    </Button>
                  ))}
                </View>
              </View>
            )}
          </Card.Content>
        </Card>
      </ScrollView>
    </KeyboardAvoidingView>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f7fa' },
  scrollContent: { flexGrow: 1, justifyContent: 'center', padding: 24 },
  header: { alignItems: 'center', marginBottom: 32 },
  title: { fontWeight: '700', color: '#1677ff' },
  subtitle: { color: '#666', marginTop: 8 },
  card: { borderRadius: 16 },
  cardTitle: { textAlign: 'center', marginBottom: 20, fontWeight: '600' },
  input: { marginBottom: 12 },
  error: { color: '#ff4d4f', textAlign: 'center', marginBottom: 8 },
  button: { marginTop: 8 },
  quickSection: { marginTop: 24, alignItems: 'center' },
  quickLabel: { color: '#999', marginBottom: 8 },
  quickRow: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'center', gap: 8 },
  quickBtn: { marginHorizontal: 2 },
})
