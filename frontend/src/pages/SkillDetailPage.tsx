import { Alert, App, Button, Card, Descriptions, Space, Spin, Tabs, Tag, Typography } from 'antd';
import { EditOutlined, SendOutlined, DeleteOutlined } from '@ant-design/icons';
import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { deleteSkill, getSkill, publishSkill } from '../api/skills';
import ContentPreview from '../components/ContentPreview';
import type { SkillDetail } from '../types/skills';

export default function SkillDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { message, modal } = App.useApp();
  const navigate = useNavigate();
  const [item, setItem] = useState<SkillDetail>();
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    let active = true; setItem(undefined); setError('');
    getSkill(id!).then(value => { if (active) setItem(value); }).catch((err: Error) => { if (active) setError(err.message); });
    return () => { active = false; };
  }, [id]);
  function publish() {
    modal.confirm({ title: '发布当前已保存草稿？', content: '客户端将立即读取本次发布的内容。', okText: '确认发布', cancelText: '取消', onOk: async () => {
      setBusy(true);
      try { await publishSkill(id!); setItem(await getSkill(id!)); void message.success('发布成功'); }
      catch (err) { void message.error((err as Error).message); throw err; }
      finally { setBusy(false); }
    } });
  }
  function remove() {
    modal.confirm({ title: '删除这个 Skill？', content: '草稿和已发布内容将一起删除，客户端将无法继续读取。此操作不可恢复。', okText: '删除', cancelText: '取消', okButtonProps: { danger: true }, onOk: async () => {
      setBusy(true);
      try { await deleteSkill(id!); void message.success('已删除'); navigate('/skills'); }
      catch (err) { void message.error((err as Error).message); throw err; }
      finally { setBusy(false); }
    } });
  }
  if (error) return <Alert type="error" title={error} action={<Link to="/skills">返回列表</Link>} />;
  if (!item) return <Spin />;
  const changed = !!item.published && ['name', 'description', 'content'].some(key => item[key as 'name' | 'description' | 'content'] !== item.published![key as 'name' | 'description' | 'content']);
  return <>
    <Link className="back-link" to="/skills">← 返回 Skill 库</Link>
    <div className="page-heading"><div><Typography.Title level={2}>{item.name}</Typography.Title><Space><Typography.Text code>{item.slug}</Typography.Text><Tag color={item.published ? 'green' : 'default'}>{item.published ? `已发布 r${item.published.revision}` : '未发布'}</Tag></Space></div><Space wrap><Link to={`/skills/${id}/edit`}><Button icon={<EditOutlined />} disabled={busy}>编辑草稿</Button></Link><Button type="primary" icon={<SendOutlined />} onClick={publish} loading={busy}>{item.published ? '再次发布' : '发布 Skill'}</Button><Button danger icon={<DeleteOutlined />} onClick={remove} disabled={busy}>删除</Button></Space></div>
    {changed && <Alert className="section-card" type="warning" title="草稿有未发布的修改" description="客户端仍在读取上次发布的内容，再次发布后才会更新。" />}
    <Card className="section-card"><Descriptions column={{ xs: 1, md: 2 }} items={[{ key: 'description', label: '草稿简介', children: item.description || '暂无简介', span: 2 }, { key: 'updated', label: '草稿更新', children: new Date(item.updated_at).toLocaleString('zh-CN') }, { key: 'published', label: '最近发布', children: item.published_at ? new Date(item.published_at).toLocaleString('zh-CN') : '尚未发布' }]} /></Card>
    <Card><Tabs items={[{ key: 'draft', label: '草稿 · SKILL.md', children: <ContentPreview content={item.content} /> }, { key: 'published', label: '客户端读取的发布内容', children: item.published ? <><Typography.Paragraph><strong>{item.published.name}</strong> · {item.published.description}</Typography.Paragraph><ContentPreview content={item.published.content} /><Typography.Paragraph copyable className="endpoint">{`${window.location.origin}/api/v1/skills/${item.slug}/content`}</Typography.Paragraph></> : <Alert type="info" title="尚未发布，客户端暂时无法读取此 Skill。" /> }]} /></Card>
  </>;
}
