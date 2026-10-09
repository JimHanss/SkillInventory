export interface SkillInput { name: string; description: string; content: string }
export interface SkillCreate extends SkillInput { slug: string }
export interface PublishedSkill { slug: string; name: string; description: string; revision: number; published_at: string }
export interface SkillSummary {
  id: string; slug: string; name: string; description: string;
  created_at: string; updated_at: string;
  published_revision: number | null; published_at: string | null;
}
export interface SkillDetail extends SkillSummary { content: string; published: (PublishedSkill & { content: string }) | null }
export interface Page<T> { items: T[]; total: number; limit: number; offset: number }
