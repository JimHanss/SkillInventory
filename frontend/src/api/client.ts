export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(path, { ...init, headers: { 'Content-Type': 'application/json', ...init?.headers } });
  } catch {
    throw new Error('无法连接服务器，请检查连接后重试。');
  }
  if (!response.ok) {
    let detail: unknown;
    try { detail = (await response.json()).detail; } catch { /* Proxy errors may not be JSON. */ }
    if (Array.isArray(detail)) {
      throw new Error(detail.map((error: { loc?: string[]; msg?: string }) => `${error.loc?.slice(1).join('.') || '输入'}: ${error.msg || '无效'}`).join('；'));
    }
    const messages: Record<number, string> = { 404: 'Skill 不存在或已被删除。', 409: '该标识已存在，请使用其他标识。', 503: '数据库暂时不可用，请稍后重试。' };
    throw new Error(messages[response.status] || (typeof detail === 'string' ? detail : `请求失败 (${response.status})`));
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}
