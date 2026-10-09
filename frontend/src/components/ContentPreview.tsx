export default function ContentPreview({ content }: { content: string }) {
  return <pre className="content-preview">{content || '暂无内容'}</pre>;
}
