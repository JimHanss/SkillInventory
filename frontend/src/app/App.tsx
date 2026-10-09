import { lazy, Suspense } from 'react';
import { Layout, Menu, Spin, Tag, Typography } from 'antd';
import { AppstoreOutlined, ApiOutlined, BookOutlined } from '@ant-design/icons';
import { Link, Navigate, Route, Routes, useLocation } from 'react-router-dom';

const SkillListPage = lazy(() => import('../pages/SkillListPage'));
const SkillEditPage = lazy(() => import('../pages/SkillEditPage'));
const SkillDetailPage = lazy(() => import('../pages/SkillDetailPage'));
const ApiGuidePage = lazy(() => import('../pages/ApiGuidePage'));

export default function InventoryApp() {
  const location = useLocation();
  return <Layout className="app-shell">
    <a className="skip-link" href="#main-content">跳到主要内容</a>
    <Layout.Sider width={224} breakpoint="lg" collapsedWidth={0} className="sidebar">
      <Link className="brand" to="/skills"><span className="brand-icon"><BookOutlined /></span><span>Skill Inventory<small>团队能力库</small></span></Link>
      <div className="nav-label">工作空间</div>
      <Menu mode="inline" selectedKeys={[location.pathname === '/guide' ? 'guide' : 'skills']} items={[{ key: 'skills', icon: <AppstoreOutlined />, label: <Link to="/skills">Skill 库</Link> }, { key: 'guide', icon: <ApiOutlined />, label: <Link to="/guide">客户端接入</Link> }]} />
      <div className="sidebar-footer"><Tag color="blue">MVP</Tag><div>内部 Skill 管理平台</div></div>
    </Layout.Sider>
    <Layout><Layout.Header className="topbar"><Typography.Text>{location.pathname === '/guide' ? '工作空间 / 客户端接入' : '工作空间 / Skill 库'}</Typography.Text><Tag>本地工作空间</Tag></Layout.Header><Layout.Content><main id="main-content" className="page-content"><Suspense fallback={<div className="page-loading"><Spin tip="正在加载页面" size="large"><div /></Spin></div>}><Routes><Route path="/" element={<Navigate replace to="/skills" />} /><Route path="/skills" element={<SkillListPage />} /><Route path="/skills/new" element={<SkillEditPage />} /><Route path="/skills/:id/edit" element={<SkillEditPage />} /><Route path="/skills/:id" element={<SkillDetailPage />} /><Route path="/guide" element={<ApiGuidePage />} /><Route path="*" element={<Typography.Title level={3}>页面不存在 · <Link to="/skills">返回 Skill 库</Link></Typography.Title>} /></Routes></Suspense></main></Layout.Content></Layout>
  </Layout>;
}
