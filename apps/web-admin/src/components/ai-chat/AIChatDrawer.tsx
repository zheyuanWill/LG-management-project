import { useState, useCallback } from 'react';
import { FloatButton, Drawer, Badge } from 'antd';
import { RobotOutlined } from '@ant-design/icons';
import { AIChatPanel } from './AIChatPanel';

interface Props {
  baseUrl: string;
}

export function AIChatDrawer({ baseUrl }: Props) {
  const [open, setOpen] = useState(false);

  const toggle = useCallback(() => setOpen((prev) => !prev), []);

  return (
    <>
      <FloatButton
        icon={<RobotOutlined />}
        type="primary"
        onClick={toggle}
        tooltip="AI 助手"
        style={{ right: 24, bottom: 24, width: 48, height: 48 }}
      />

      <Drawer
        title={null}
        placement="right"
        width={440}
        open={open}
        onClose={() => setOpen(false)}
        closable={false}
        styles={{ body: { padding: 0, height: '100%' } }}
        destroyOnClose={false}
      >
        <AIChatPanel baseUrl={baseUrl} style={{ height: '100%' }} />
      </Drawer>
    </>
  );
}
