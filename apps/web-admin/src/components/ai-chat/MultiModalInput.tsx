import { useState, useRef, useCallback } from 'react';
import { Input, Button, Space, Upload, Image, Typography } from 'antd';
import { SendOutlined, PictureOutlined, CloseCircleOutlined, StopOutlined } from '@ant-design/icons';

const { Text } = Typography;

interface Props {
  onSend: (text: string, imageBase64?: string) => void;
  onStop?: () => void;
  isStreaming: boolean;
  disabled?: boolean;
}

export function MultiModalInput({ onSend, onStop, isStreaming, disabled }: Props) {
  const [text, setText] = useState('');
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [imageBase64, setImageBase64] = useState<string | null>(null);
  const textAreaRef = useRef<any>(null);

  const handleSend = useCallback(() => {
    const trimmed = text.trim();
    if (!trimmed && !imageBase64) return;

    onSend(trimmed || '请分析这张图片', imageBase64 || undefined);
    setText('');
    setImagePreview(null);
    setImageBase64(null);
  }, [text, imageBase64, onSend]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }, [handleSend]);

  const handlePaste = useCallback((e: React.ClipboardEvent) => {
    const items = e.clipboardData?.items;
    if (!items) return;

    for (const item of items) {
      if (item.type.startsWith('image/')) {
        e.preventDefault();
        const blob = item.getAsFile();
        if (!blob) continue;

        const reader = new FileReader();
        reader.onload = () => {
          const dataUrl = reader.result as string;
          setImagePreview(dataUrl);
          setImageBase64(dataUrl.split(',')[1]);
        };
        reader.readAsDataURL(blob);
        break;
      }
    }
  }, []);

  const handleImageUpload = useCallback((file: File) => {
    const reader = new FileReader();
    reader.onload = () => {
      const dataUrl = reader.result as string;
      setImagePreview(dataUrl);
      setImageBase64(dataUrl.split(',')[1]);
    };
    reader.readAsDataURL(file);
    return false;
  }, []);

  return (
    <div style={{ borderTop: '1px solid #f0f0f0', padding: '8px 12px' }}>
      {imagePreview && (
        <div style={{ marginBottom: 8, position: 'relative', display: 'inline-block' }}>
          <Image src={imagePreview} height={60} style={{ borderRadius: 6 }} preview={false} />
          <CloseCircleOutlined
            onClick={() => { setImagePreview(null); setImageBase64(null); }}
            style={{
              position: 'absolute', top: -6, right: -6,
              fontSize: 18, color: '#ff4d4f', cursor: 'pointer',
              background: '#fff', borderRadius: '50%',
            }}
          />
        </div>
      )}

      <Space.Compact style={{ width: '100%' }}>
        <Upload
          accept="image/*"
          showUploadList={false}
          beforeUpload={handleImageUpload}
        >
          <Button icon={<PictureOutlined />} disabled={disabled || isStreaming} />
        </Upload>

        <Input.TextArea
          ref={textAreaRef}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          onPaste={handlePaste}
          placeholder="输入问题...（Shift+Enter 换行）"
          autoSize={{ minRows: 1, maxRows: 4 }}
          disabled={disabled}
          style={{ flex: 1 }}
        />

        {isStreaming ? (
          <Button
            icon={<StopOutlined />}
            onClick={onStop}
            danger
          >
            停止
          </Button>
        ) : (
          <Button
            type="primary"
            icon={<SendOutlined />}
            onClick={handleSend}
            disabled={disabled || (!text.trim() && !imageBase64)}
          >
            发送
          </Button>
        )}
      </Space.Compact>

      <Text type="secondary" style={{ fontSize: 11, marginTop: 4, display: 'block' }}>
        支持粘贴图片 · Shift+Enter 换行
      </Text>
    </div>
  );
}
