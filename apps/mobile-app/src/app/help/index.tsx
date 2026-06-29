import { useState } from 'react'
import { View, StyleSheet, ScrollView, Alert } from 'react-native'
import { Text, Card, List, TextInput, Button, Divider } from 'react-native-paper'

const faqs = [
  { q: '如何查看订单详情？', a: '在首页点击搜索，找到订单后点击进入详情页面。' },
  { q: '如何提交审批？', a: '在审批中心查看待审批项目，点击通过或驳回。' },
  { q: '如何上传附件？', a: '进入上传页面，选择拍照或从相册选取，填写关联信息后上传。' },
  { q: '忘记密码怎么办？', a: '请联系管理员重置密码。' },
]

export default function HelpScreen() {
  const [feedback, setFeedback] = useState('')

  const submitFeedback = () => {
    if (!feedback.trim()) {
      Alert.alert('提示', '请输入反馈内容')
      return
    }
    Alert.alert('感谢', '您的反馈已提交')
    setFeedback('')
  }

  return (
    <ScrollView style={styles.container}>
      <Text variant="titleMedium" style={styles.sectionTitle}>常见问题</Text>
      <Card style={styles.card}>
        {faqs.map((faq, i) => (
          <View key={i}>
            {i > 0 && <Divider />}
            <List.Accordion title={faq.q} titleStyle={{ fontSize: 14 }}>
              <View style={styles.answer}><Text variant="bodySmall">{faq.a}</Text></View>
            </List.Accordion>
          </View>
        ))}
      </Card>

      <Text variant="titleMedium" style={styles.sectionTitle}>反馈建议</Text>
      <Card style={styles.card}>
        <Card.Content>
          <TextInput
            label="请输入反馈内容"
            value={feedback}
            onChangeText={setFeedback}
            mode="outlined"
            multiline
            numberOfLines={4}
            style={styles.input}
          />
          <Button mode="contained" onPress={submitFeedback} style={styles.submitBtn}>提交反馈</Button>
        </Card.Content>
      </Card>

      <Card style={styles.card}>
        <Card.Content>
          <Text variant="bodySmall" style={{ color: '#666' }}>联系方式：support@lgmarineservices.com</Text>
        </Card.Content>
      </Card>
    </ScrollView>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f7fa' },
  sectionTitle: { marginLeft: 16, marginTop: 16, marginBottom: 4 },
  card: { margin: 12, borderRadius: 12 },
  answer: { paddingHorizontal: 16, paddingBottom: 12 },
  input: { marginBottom: 12 },
  submitBtn: { marginTop: 4 },
})
