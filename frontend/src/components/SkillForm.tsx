import { Button, Card, Form, Input, Space, Typography } from 'antd';
import type { FormInstance } from 'antd';
import { useState } from 'react';
import type { SkillCreate, SkillDetail } from '../types/skills';
import ContentPreview from './ContentPreview';

export default function SkillForm({ initial, busy, onSave, onCancel, form: suppliedForm }: {
  form?: FormInstance<SkillCreate>; initial?: SkillDetail; busy: boolean; onSave: (data: SkillCreate) => Promise<void>; onCancel: () => void;
}) {
  const [form] = Form.useForm<SkillCreate>(suppliedForm);
  const content = Form.useWatch('content', form) || '';
  const [preview, setPreview] = useState(false);
  const required = { required: true, whitespace: true, message: '此项不能为空' };
  return <Form form={form} layout="vertical" initialValues={initial || { description: '', content: '# Skill 名称\n\n说明用途、步骤和预期输出。\n' }} onFinish={onSave} disabled={busy}>
    <Card className="section-card" title="基本信息">
      <div className="form-grid">
        <Form.Item name="name" label="名称" rules={[required, { max: 120, message: '最多 120 个字符' }]}><Input placeholder="例如：代码审查助手" /></Form.Item>
        <Form.Item name="slug" label="唯一标识" extra="用于客户端读取；创建后不可修改。" rules={[required, { max: 64 }, { pattern: /^[a-z0-9]+(?:-[a-z0-9]+)*$/, message: '仅支持小写字母、数字和中间连字符' }]}><Input disabled={!!initial || busy} placeholder="code-review" /></Form.Item>
      </div>
      <Form.Item name="description" label="简介" rules={[{ max: 1000, message: '最多 1000 个字符' }]}><Input.TextArea rows={2} placeholder="简要描述这个 Skill 能解决什么问题" /></Form.Item>
    </Card>
    <Card className="section-card" title="SKILL.md" extra={<Button size="small" onClick={() => setPreview(!preview)}>{preview ? '继续编辑' : '查看原文预览'}</Button>}>
      <Typography.Paragraph type="secondary">保存仅更新草稿；点击右上角发布会保存并发布当前内容，客户端才能读取。</Typography.Paragraph>
      <Form.Item name="content" label="内容" hidden={preview} rules={[required, { validator: (_, value: string) => new TextEncoder().encode(value || '').length <= 262144 ? Promise.resolve() : Promise.reject(new Error('内容不能超过 256 KiB')) }]}><Input.TextArea className="markdown-editor" autoSize={{ minRows: 16, maxRows: 36 }} spellCheck={false} /></Form.Item>
      {preview && <ContentPreview content={content} />}
      <Typography.Text type="secondary">{new TextEncoder().encode(content).length.toLocaleString()} / 262,144 字节 · 原文保存，不执行脚本</Typography.Text>
    </Card>
    <div className="form-actions"><Typography.Text type="secondary">点击发布可保存并发布给客户端</Typography.Text><Space><Button type="primary" htmlType="submit" loading={busy}>保存草稿</Button><Button onClick={onCancel}>取消</Button></Space></div>
  </Form>;
}
