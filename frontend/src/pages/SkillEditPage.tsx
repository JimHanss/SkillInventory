import { Alert, App, Button, Form, Spin, Typography } from 'antd';
import { SendOutlined } from '@ant-design/icons';
import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { createSkill, getSkill, publishSkill, updateSkill } from '../api/skills';
import SkillForm from '../components/SkillForm';
import type { SkillCreate, SkillDetail } from '../types/skills';

export default function SkillEditPage() {
  const { id } = useParams();
  const [form] = Form.useForm<SkillCreate>();
  const navigate = useNavigate();
  const { message } = App.useApp();
  const [initial, setInitial] = useState<SkillDetail>();
  const [createdId, setCreatedId] = useState<string>();
  const [loading, setLoading] = useState(!!id);
  const [busy, setBusy] = useState(false);
  const [loadError, setLoadError] = useState('');
  const [saveError, setSaveError] = useState('');
  useEffect(() => {
    let active = true;
    setInitial(undefined); setCreatedId(undefined); setLoadError(''); setLoading(!!id);
    if (id) getSkill(id).then(value => { if (active) setInitial(value); }).catch((err: Error) => { if (active) setLoadError(err.message); }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [id]);
  async function save(data: SkillCreate, publish = false) {
    setBusy(true); setSaveError('');
    try {
      const { slug: _slug, ...update } = data;
      let skillId = id || createdId;
      if (!skillId) {
        const item = await createSkill(data);
        skillId = item.id;
        setCreatedId(item.id);
        setInitial(item);
      }
      if (publish) {
        await publishSkill(skillId, update);
        void message.success('发布成功');
        if (window.history.state?.idx > 0) navigate(-1);
        else navigate('/skills');
      } else {
        if (id || createdId) await updateSkill(skillId, update);
        void message.success('草稿已保存'); navigate(`/skills/${skillId}`);
      }
    } catch (err) { setSaveError((err as Error).message); }
    finally { setBusy(false); }
  }
  return <>
    <Link className="back-link" to="/skills">← 返回</Link>
    <div className="page-heading"><div><Typography.Title level={2}>{id || createdId ? '编辑草稿' : '新建 Skill'}</Typography.Title><Typography.Text type="secondary">用 Markdown 描述可复用的工作方法。</Typography.Text></div><Button type="primary" icon={<SendOutlined />} loading={busy} disabled={loading || !!loadError} onClick={() => { void form.validateFields().then(data => save(data, true)).catch(() => {}); }}>发布</Button></div>
    {loading ? <Spin /> : loadError ? <Alert type="error" title={loadError} /> : <>
      {saveError && <Alert className="section-card" type="error" title={saveError} />}
      <SkillForm key={id || 'new'} initial={initial} form={form} busy={busy} onSave={data => save(data)} onCancel={() => navigate('/skills')} />
    </>}
  </>;
}
