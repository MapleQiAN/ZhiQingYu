import MarkdownIt from 'markdown-it'

const md = new MarkdownIt({
  html: false,
  linkify: true,
  breaks: true,
  typographer: true,
})

export const renderMarkdown = (content?: string | null) => {
  if (!content) return ''
  return md.render(content)
}

