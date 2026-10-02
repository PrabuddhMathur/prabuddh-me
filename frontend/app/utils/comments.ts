import type { InjectionKey, Ref } from 'vue'

/** A piece of comment text: plain text, or a web address to link. */
export interface CommentPart {
  text: string
  /** Set for web addresses. */
  href?: string
}

// http(s) addresses up to the next whitespace, `<` or quote.
const URL_PATTERN = /https?:\/\/[^\s<>"']+/gi
const SCHEME = /^https?:\/\//i
const CLOSING_BRACKETS: Record<string, string> = { ')': '(', ']': '[', '}': '{' }

const count = (text: string, char: string) => text.split(char).length - 1

/**
 * Drops what a sentence puts after an address: punctuation, and a closing bracket without its
 * opening one inside the address ("(see https://a.com/x)" loses the ")", wikipedia's "A_(b)" keeps it).
 */
function trimUrl(raw: string): string {
  let url = raw
  for (;;) {
    const last = url.slice(-1)
    const opening = CLOSING_BRACKETS[last]
    if (/[.,;:!?'"]/.test(last) || (opening && count(url, last) > count(url, opening))) {
      url = url.slice(0, -1)
    } else {
      return url
    }
  }
}

/**
 * Splits comment text into text and link parts, in order, so a template can render them
 * with v-for and no v-html: "see https://example.com/a, ok" gives "see ", the link, ", ok".
 * Only http and https addresses become links.
 */
export function linkifyComment(text: string): CommentPart[] {
  const parts: CommentPart[] = []
  let done = 0
  for (const match of text.matchAll(URL_PATTERN)) {
    const url = trimUrl(match[0])
    if (url.length <= (SCHEME.exec(url)?.[0].length ?? url.length)) continue
    if (match.index > done) parts.push({ text: text.slice(done, match.index) })
    parts.push({ text: url, href: url })
    done = match.index + url.length
  }
  if (done < text.length) parts.push({ text: text.slice(done) })
  return parts
}

/** What the comment section provides to its comments, so a comment can open its reply form. */
export interface CommentsContext {
  postId: number
  formToken: string
  akismet: boolean
  likeLabel: string
  /** New comments are accepted (shows the Reply controls). */
  open: boolean
  /** The id of the comment whose reply form is open, or null. */
  replyingTo: Readonly<Ref<number | null>>
  openReply: (id: number) => void
  closeReply: () => void
}

/** provide(commentsKey, …) in CommentSection; inject(commentsKey) in CommentItem. */
export const commentsKey: InjectionKey<CommentsContext> = Symbol('comments')
