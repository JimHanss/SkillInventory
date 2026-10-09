import { request } from './client';
import type { Page, PublishedSkill, SkillCreate, SkillDetail, SkillInput, SkillSummary } from '../types/skills';

const base = '/api/admin/skills';
export function listSkills(query: { q: string; status: string; limit: number; offset: number }) {
  const params = new URLSearchParams({ limit: String(query.limit), offset: String(query.offset) });
  if (query.q) params.set('q', query.q);
  if (query.status) params.set('status', query.status);
  return request<Page<SkillSummary>>(`${base}?${params}`);
}
export const getSkill = (id: string) => request<SkillDetail>(`${base}/${encodeURIComponent(id)}`);
export const createSkill = (data: SkillCreate) => request<SkillDetail>(base, { method: 'POST', body: JSON.stringify(data) });
export const updateSkill = (id: string, data: SkillInput) => request<SkillDetail>(`${base}/${encodeURIComponent(id)}`, { method: 'PUT', body: JSON.stringify(data) });
export const deleteSkill = (id: string) => request<void>(`${base}/${encodeURIComponent(id)}`, { method: 'DELETE' });
export const publishSkill = (id: string, data?: SkillInput) => request<PublishedSkill>(`${base}/${encodeURIComponent(id)}/publish`, { method: 'POST', ...(data ? { body: JSON.stringify(data) } : {}) });
