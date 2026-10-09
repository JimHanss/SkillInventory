import { App, Alert, Button, Card, Empty, Input, Select, Space, Table, Tag, Typography } from 'antd';
import type { TableColumnsType } from 'antd';
import { PlusOutlined, SearchOutlined, ReloadOutlined, BookOutlined, InfoCircleOutlined } from '@ant-design/icons';
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { deleteSkill, listSkills, publishSkill } from '../api/skills';
import type { Page, SkillSummary } from '../types/skills';

export default function SkillListPage() {
  const { message } = App.useApp();
  const [q, setQ] = useState('');
  const [status, setStatus] = useState('');
  const [page, setPage] = useState(1);
  const [size, setSize] = useState(20);
  const [data, setData] = useState<Page<SkillSummary>>({ items: [], total: 0, limit: 20, offset: 0 });
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState('');
  const [reload, setReload] = useState(0);
  const [pending, setPending] = useState<{ id: string; action: 'delete' | 'publish' }>();
  async function runAction(item: SkillSummary, action: 'delete' | 'publish') {
    if (pending) return;
    setPending({ id: item.id, action });
    try {
      if (action === 'delete') await deleteSkill(item.id);
      else await publishSkill(item.id);
      void message.success(action === 'delete' ? '已删除' : '发布成功');
      if (action === 'delete' && data.items.length === 1 && page > 1) setPage(page - 1);
      setReload(value => value + 1);
    } catch (err) { void message.error((err as Error).message); }
    finally { setPending(undefined); }
  }
  useEffect(() => {
    let active = true;
    setBusy(true); setError('');
    listSkills({ q, status, limit: size, offset: (page - 1) * size })
      .then(result => { if (active) setData(result); })
      .catch((err: Error) => { if (active) { setError(err.message); void message.error(err.message); } })
      .finally(() => { if (active) setBusy(false); });
    return () => { active = false; };
  }, [q, status, page, size, reload, message]);
  const columns: TableColumnsType<SkillSummary> = [
    { title: 'Skill', width: 240, dataIndex: 'name', render: (_, item) => <div className="skill-cell"><span className="skill-avatar" aria-hidden="true"><BookOutlined /></span><div><Link className="skill-name" to={`/skills/${item.id}`}>{item.name}</Link><div className="slug">{item.slug}</div></div></div> },
    { title: '简介', dataIndex: 'description', ellipsis: true, render: value => value || <Typography.Text type="secondary">暂无简介</Typography.Text> },
    { title: '发布状态', width: 135, render: (_, item) => item.published_revision ? <Tag color="green">已发布 · r{item.published_revision}</Tag> : <Tag>未发布</Tag> },
    { title: '更新时间', width: 185, dataIndex: 'updated_at', render: value => new Date(value).toLocaleString('zh-CN') },
    { title: '编辑', width: 90, render: (_, item) => <Link to={`/skills/${item.id}/edit`}>编辑</Link> },
    { title: '发布', width: 100, render: (_, item) => item.published_revision ? <Typography.Text type="secondary">已发布</Typography.Text> : <Button type="link" disabled={!!pending} loading={pending?.id === item.id && pending.action === 'publish'} onClick={() => void runAction(item, 'publish')}>发布</Button> },
    { title: '删除', width: 100, render: (_, item) => <Button type="link" danger disabled={!!pending} loading={pending?.id === item.id && pending.action === 'delete'} onClick={() => void runAction(item, 'delete')}>删除</Button> },
  ];
  return <>
    <div className="page-heading"><div><Typography.Title level={2}>Skill 库</Typography.Title><Typography.Text type="secondary">集中管理团队知识，将可复用能力交付给内部客户端。</Typography.Text></div><Link to="/skills/new"><Button type="primary" icon={<PlusOutlined />}>新建 Skill</Button></Link></div>
    <Card className="inventory-card" title={<Space>全部 Skill <Tag className="count-tag">{data.total}</Tag></Space>}>
      <div className="list-toolbar"><Input.Search aria-label="搜索 Skill 名称或标识" prefix={<SearchOutlined />} placeholder="搜索名称或标识" allowClear maxLength={120} onSearch={value => { setQ(value); setPage(1); }} className="search-input" /><Select aria-label="发布状态" value={status} onChange={value => { setStatus(value); setPage(1); }} options={[{ value: '', label: '全部状态' }, { value: 'draft', label: '未发布' }, { value: 'published', label: '已发布' }]} style={{ width: 150 }} /><Button aria-label="刷新 Skill 列表" loading={busy} icon={<ReloadOutlined />} onClick={() => setReload(reload + 1)}>刷新</Button></div>
      {error && <Alert type="error" title={error} style={{ marginBottom: 16 }} />}
      <Table<SkillSummary> rowKey="id" columns={columns} dataSource={data.items} loading={busy} scroll={{ x: 1050 }} locale={{ emptyText: <Empty description="暂无 Skill，创建第一个草稿开始使用" /> }} pagination={{ current: page, pageSize: size, total: data.total, showSizeChanger: true, pageSizeOptions: [10, 20, 50, 100], showTotal: total => `共 ${total} 项`, onChange: (next, nextSize) => { setPage(nextSize !== size ? 1 : next); setSize(nextSize); } }} />
    </Card>
    <div className="hint-strip"><InfoCircleOutlined aria-hidden="true" /> 草稿与发布内容分开保存。编辑后再次发布，客户端才会收到更新。</div>
  </>;
}
