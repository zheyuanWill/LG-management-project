import { useState } from 'react'
import { View, StyleSheet, Image, ScrollView, Alert } from 'react-native'
import { Button, TextInput, Text, Card, ProgressBar } from 'react-native-paper'
import * as ImagePicker from 'expo-image-picker'
import { http } from '@lg/api-client'
import { useUploadStore } from '../../stores/uploadStore'

export default function UploadScreen() {
  const [image, setImage] = useState<string | null>(null)
  const [objectType, setObjectType] = useState('order')
  const [objectId, setObjectId] = useState('')
  const { isUploading, progress, startUpload, updateProgress, completeUpload, failUpload } = useUploadStore()

  const pickImage = async () => {
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ['images'],
      quality: 0.8,
    })
    if (!result.canceled && result.assets[0]) {
      setImage(result.assets[0].uri)
    }
  }

  const takePhoto = async () => {
    const permission = await ImagePicker.requestCameraPermissionsAsync()
    if (!permission.granted) {
      Alert.alert('权限', '需要相机权限')
      return
    }
    const result = await ImagePicker.launchCameraAsync({ quality: 0.8 })
    if (!result.canceled && result.assets[0]) {
      setImage(result.assets[0].uri)
    }
  }

  const handleUpload = async () => {
    if (!image || !objectId) {
      Alert.alert('提示', '请选择图片并填写关联ID')
      return
    }
    try {
      startUpload(image)
      updateProgress(30)
      const filename = image.split('/').pop() ?? 'photo.jpg'
      const presigned = await http.post<{ upload_url: string; file_key: string }>('/files/presigned-url', {
        filename, content_type: 'image/jpeg', object_type: objectType, object_id: Number(objectId),
      })
      updateProgress(60)
      await fetch(presigned.upload_url, {
        method: 'PUT',
        headers: { 'Content-Type': 'image/jpeg' },
        body: await fetch(image).then((r) => r.blob()),
      })
      updateProgress(90)
      await http.post('/files/confirm-upload', {
        file_key: presigned.file_key, original_name: filename,
        mime_type: 'image/jpeg', size: 0, object_type: objectType, object_id: Number(objectId),
      })
      completeUpload()
      Alert.alert('成功', '上传完成')
      setImage(null)
    } catch (e) {
      failUpload()
      Alert.alert('错误', e instanceof Error ? e.message : '上传失败')
    }
  }

  return (
    <ScrollView style={styles.container}>
      <Card style={styles.card}>
        <Card.Content>
          <View style={styles.btnRow}>
            <Button mode="outlined" icon="camera" onPress={takePhoto} style={styles.pickBtn}>拍照</Button>
            <Button mode="outlined" icon="image" onPress={pickImage} style={styles.pickBtn}>相册</Button>
          </View>

          {image && <Image source={{ uri: image }} style={styles.preview} resizeMode="cover" />}

          <TextInput label="关联类型" value={objectType} onChangeText={setObjectType} mode="outlined" style={styles.input} />
          <TextInput label="关联ID" value={objectId} onChangeText={setObjectId} mode="outlined" keyboardType="numeric" style={styles.input} />

          {isUploading && <ProgressBar progress={progress / 100} style={styles.progress} />}

          <Button mode="contained" onPress={handleUpload} loading={isUploading} disabled={!image || !objectId} style={styles.uploadBtn}>
            上传
          </Button>
        </Card.Content>
      </Card>
    </ScrollView>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f7fa' },
  card: { margin: 12, borderRadius: 12 },
  btnRow: { flexDirection: 'row', gap: 12, marginBottom: 12 },
  pickBtn: { flex: 1 },
  preview: { width: '100%', height: 200, borderRadius: 8, marginBottom: 12 },
  input: { marginBottom: 12 },
  progress: { marginBottom: 12 },
  uploadBtn: { marginTop: 8 },
})
