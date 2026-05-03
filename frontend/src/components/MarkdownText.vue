<template>
  <component :is="tag" class="md" :class="{ 'md-inline': inline }" v-html="html" @click="onClick" />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import MarkdownIt from 'markdown-it'

const md = new MarkdownIt({
  html: false,
  linkify: true,
  breaks: true,
  typographer: false,
})

const defaultLinkOpen =
  md.renderer.rules.link_open ||
  ((tokens, idx, options, _env, self) => self.renderToken(tokens, idx, options))

md.renderer.rules.link_open = (tokens, idx, options, env, self) => {
  const token = tokens[idx]
  const hrefIdx = token.attrIndex('href')
  if (hrefIdx >= 0) {
    let href = token.attrs![hrefIdx][1]
    // /media/ 等本地资源链接补全为绝对地址,避免 Vue Router 拦截
    if (href.startsWith('/media/')) {
      token.attrs![hrefIdx][1] = window.location.origin + href
    }
  }
  const targetIdx = token.attrIndex('target')
  if (targetIdx < 0) token.attrPush(['target', '_blank'])
  else token.attrs![targetIdx][1] = '_blank'
  const relIdx = token.attrIndex('rel')
  if (relIdx < 0) token.attrPush(['rel', 'noopener noreferrer'])
  else token.attrs![relIdx][1] = 'noopener noreferrer'
  return defaultLinkOpen(tokens, idx, options, env, self)
}

const props = withDefaults(defineProps<{
  text?: string | null
  inline?: boolean
}>(), { inline: false })

const tag = computed(() => (props.inline ? 'span' : 'div'))

function onClick(e: MouseEvent) {
  const link = (e.target as HTMLElement).closest('a')
  if (!link) return
  const href = link.getAttribute('href')
  if (href && href.includes('/media/')) {
    e.preventDefault()
    e.stopPropagation()
    const abs = href.startsWith('/media/') ? window.location.origin + href : href
    window.open(abs, '_blank')
  }
}

const html = computed(() => {
  const src = props.text || ''
  let rendered = props.inline ? md.renderInline(src) : md.render(src)
  // 给 table 包一层卡片 wrapper,便于做圆角阴影和"表格"标签
  rendered = rendered
    .replace(/<table>/g, '<div class="table-wrap"><table>')
    .replace(/<\/table>/g, '</table></div>')
  // 强制 /media/ 链接补全绝对地址 + 新窗口打开 + 触发下载
  // 避免 Vue Router catch-all 把 /media/... 当成前端路由
  rendered = rendered.replace(
    /<a\s+([^>]*)href="([^"]*\/media\/[^"]*)"([^>]*)>/gi,
    (_match, before: string, href: string, after: string) => {
      const abs = href.startsWith('/media/')
        ? window.location.origin + href
        : href
      // 移除已有的 target/rel/download 避免重复
      const cleanBefore = before.replace(/\s*(target|rel|download)="[^"]*"/gi, '')
      const cleanAfter = after.replace(/\s*(target|rel|download)="[^"]*"/gi, '')
      return `<a ${cleanBefore}href="${abs}"${cleanAfter} target="_blank" rel="noopener noreferrer" download>`
    },
  )
  return rendered
})
</script>

<style scoped>
.md {
  line-height: 1.8;
  word-break: break-word;
  white-space: normal;
  font-size: 15px;
  color: var(--txt-primary);
}
.md-inline {
  font-size: inherit;
  line-height: inherit;
}

/* paragraph */
.md :deep(p) { margin: 0 0 12px; }
.md :deep(p:last-child) { margin-bottom: 0; }

/* lists */
.md :deep(ul),
.md :deep(ol) { padding-left: 28px; margin: 8px 0 12px; }
.md :deep(li) { margin: 6px 0; }
.md :deep(li > p) { margin: 0; }
.md :deep(ul ul) { list-style-type: circle; }
.md :deep(ul ul ul) { list-style-type: square; }
.md :deep(ol ol) { list-style-type: lower-alpha; }

/* emphasis */
.md :deep(strong) { font-weight: 700; color: inherit; }
.md :deep(em) { font-style: italic; }

/* headings */
.md :deep(h1),
.md :deep(h2),
.md :deep(h3),
.md :deep(h4),
.md :deep(h5),
.md :deep(h6) {
  font-weight: 700;
  margin: 20px 0 12px;
  line-height: 1.4;
  padding-bottom: 8px;
  border-bottom: 1px solid #eee;
}
.md :deep(h1) { font-size: 20px; }
.md :deep(h2) { font-size: 18px; }
.md :deep(h3) { font-size: 16px; }
.md :deep(h4),
.md :deep(h5),
.md :deep(h6) { font-size: 15px; border-bottom: none; padding-bottom: 0; }

/* inline code */
.md :deep(code) {
  background: rgba(15, 23, 42, .06);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
  font-size: .88em;
}

/* code block */
.md :deep(pre) {
  background: #f8f9fa;
  border: 1px solid #e8e8e8;
  padding: 14px 16px;
  border-radius: 8px;
  overflow: auto;
  font-size: 13px;
  margin: 10px 0;
  line-height: 1.6;
}
.md :deep(pre code) {
  background: transparent;
  padding: 0;
  border-radius: 0;
}

/* links */
.md :deep(a) {
  color: #d62828;
  text-decoration: none;
  border-bottom: 1px solid rgba(214, 40, 40, .3);
}
.md :deep(a:hover) {
  color: #ff7a1a;
  border-bottom-color: #ff7a1a;
}

/* blockquote */
.md :deep(blockquote) {
  border-left: 4px solid #ff7a1a;
  background: rgba(255, 122, 26, .04);
  padding: 10px 16px;
  margin: 12px 0;
  color: var(--txt-secondary);
  border-radius: 0 8px 8px 0;
}

/* hr */
.md :deep(hr) {
  border: none;
  border-top: 1px solid #eee;
  margin: 16px 0;
}

/* table card */
.md :deep(.table-wrap) {
  position: relative;
  margin: 16px 0;
  border-radius: 8px;
  border: 1px solid #e8e8e8;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, .04);
}
.md :deep(.table-wrap)::before {
  content: '表格';
  display: block;
  padding: 8px 14px;
  font-size: 12px;
  color: var(--txt-muted);
  background: #f8f9fa;
  border-bottom: 1px solid #eee;
  font-weight: 500;
}
.md :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 0;
}
.md :deep(th),
.md :deep(td) {
  border: none;
  border-bottom: 1px solid #eee;
  padding: 10px 14px;
  font-size: 14px;
  text-align: left;
}
.md :deep(th) {
  background: #f5f7fa;
  font-weight: 600;
  border-bottom: 2px solid #e8e8e8;
}
.md :deep(tr:last-child td) { border-bottom: none; }
.md :deep(tr:hover td) { background: #fafbfc; }

/* images */
.md :deep(img) {
  max-width: 100%;
  border-radius: 8px;
  margin: 8px 0;
}
</style>
