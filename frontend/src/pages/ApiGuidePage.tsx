import { Alert, Card, Space, Table, Typography } from 'antd';
import ContentPreview from '../components/ContentPreview';

export default function ApiGuidePage() {
  const origin = window.location.origin;
  return <>
    <div className="page-heading"><div><Typography.Title level={2}>客户端接入</Typography.Title><Typography.Text type="secondary">通过 HTTP 发现和读取已发布的 Skill。</Typography.Text></div><a href="/docs" target="_blank" rel="noreferrer">打开 API 文档 ↗</a></div>
    <Alert className="section-card" type="info" title="只有已发布内容对客户端可见" description="保存草稿不会影响客户端，发布会替换当前快照并递增 revision。首版不提供历史版本下载。" />
    <Card className="section-card" title="读取接口"><Table pagination={false} rowKey="path" scroll={{ x: 600 }} columns={[{ title: '方法', dataIndex: 'method', width: 90 }, { title: '路径', dataIndex: 'path', render: value => <Typography.Text code>{value}</Typography.Text> }, { title: '用途', dataIndex: 'description' }]} dataSource={[{ method: 'GET', path: '/api/v1/skills', description: '已发布元数据列表，支持 q、limit、offset' }, { method: 'GET', path: '/api/v1/skills/{slug}', description: '名称、简介、revision 和发布时间' }, { method: 'GET', path: '/api/v1/skills/{slug}/content', description: 'SKILL.md 原文，text/plain UTF-8' }]} /></Card>
    <Card title="调用示例" className="section-card"><ContentPreview content={`# 列出可用 Skill\ncurl "${origin}/api/v1/skills?limit=20&offset=0"\n\n# 获取元数据\ncurl "${origin}/api/v1/skills/code-review"\n\n# 读取 SKILL.md 原文\ncurl "${origin}/api/v1/skills/code-review/content"`} /><Typography.Paragraph type="secondary">将 code-review 替换为已发布 Skill 的唯一标识。不存在、未发布或已删除的 Skill 返回 404。</Typography.Paragraph></Card>
    <Space direction="vertical"><Typography.Text type="secondary">本地演示服务无账户认证，仅绑定本机。向内网开放前需补充认证和访问控制。</Typography.Text></Space>
  </>;
}
