// Text and date helpers that give the same output as the Django template filters
// the old templates used. Auto-imported by Nuxt.

export const MONTH_NAMES = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
] as const

const MONTH_ABBRS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'] as const

export interface DateParts {
  year: number
  /** 1-12 */
  month: number
  day: number
}

const DATE_ONLY = /^(\d{4})-(\d{2})-(\d{2})$/

/**
 * A date from the API: "2025-01-10" is read from its parts (no time zone shift);
 * a datetime ("2025-01-10T10:00:00Z") is shown in UTC, like the old site (TIME_ZONE = "UTC").
 */
function toDateParts(value: string | DateParts): DateParts | null {
  if (typeof value !== 'string') return value
  const match = DATE_ONLY.exec(value)
  if (match) return { year: Number(match[1]), month: Number(match[2]), day: Number(match[3]) }
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return null
  return { year: date.getUTCFullYear(), month: date.getUTCMonth() + 1, day: date.getUTCDate() }
}

const pad = (n: number, width = 2) => String(n).padStart(width, '0')

/**
 * Django's `|date:"…"` filter for these format characters:
 * `d` (05), `j` (5), `m` (01), `n` (1), `M` (Jan), `F` (January), `Y` (2025), `y` (25).
 * A backslash escapes the next character; everything else is copied as is.
 * Examples: "M d, Y" → "Jan 05, 2025", "M j, Y" → "Jan 5, 2025", "F j, Y" → "January 5, 2025",
 * "Y-m-d" → "2025-01-05", "F d, Y" → "January 05, 2025" (Python's "%B %d, %Y").
 * Empty or invalid values give "", like Django.
 */
export function formatDate(value: string | DateParts | null | undefined, format: string): string {
  if (!value) return ''
  const parts = toDateParts(value)
  if (!parts) return ''
  const { year, month, day } = parts
  let out = ''
  for (let i = 0; i < format.length; i++) {
    const ch = format.charAt(i)
    switch (ch) {
      case 'd': out += pad(day); break
      case 'j': out += String(day); break
      case 'm': out += pad(month); break
      case 'n': out += String(month); break
      case 'M': out += MONTH_ABBRS[month - 1] ?? ''; break
      case 'F': out += MONTH_NAMES[month - 1] ?? ''; break
      case 'Y': out += pad(year, 4); break
      case 'y': out += pad(year % 100); break
      case '\\': i++; out += format.charAt(i); break
      default: out += ch
    }
  }
  return out
}

/** Python's str.split() whitespace (a little wider than JavaScript's \s). */
const PY_WHITESPACE = /[\t\n\v\f\r\x1c-\x1f \x85\xa0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]+/

/**
 * Django's `|truncatewords:N`: split on whitespace, keep the first N words joined by single
 * spaces, and add " …" (a space, then an ellipsis) only if words were dropped.
 * Text that isn't truncated still has its whitespace collapsed.
 * "Joel is a slug" with 2 → "Joel is …".
 */
export function truncateWords(value: string | null | undefined, length: number): string {
  if (!value || length <= 0) return ''
  const words = value.split(PY_WHITESPACE).filter(Boolean)
  if (words.length <= length) return words.join(' ')
  const text = words.slice(0, length).join(' ')
  return text.endsWith(' …') ? text : `${text} …`
}

/**
 * Django's `|pluralize` ("s" unless the value is 1) and `|pluralize:"y,ies"`.
 * An array counts its items.
 */
export function pluralize(value: number | string | readonly unknown[], suffixes = 's'): string {
  const bits = (suffixes.includes(',') ? suffixes : `,${suffixes}`).split(',')
  if (bits.length > 2) return ''
  const [singular = '', plural = ''] = bits
  const count = Array.isArray(value) ? value.length : Number(value)
  if (Number.isNaN(count)) return ''
  return count === 1 ? singular : plural
}

/**
 * Django's `|title`: Python's str.title() (each run of letters starts upper case, the rest
 * is lower case), except no capital after an apostrophe or a digit.
 * "blogpage" → "Blogpage", "they're 3rd" → "They're 3rd".
 */
export function titleCase(value: string): string {
  let out = ''
  let previousIsCased = false
  for (const ch of value) {
    const lower = ch.toLowerCase()
    const upper = ch.toUpperCase()
    const cased = lower !== upper
    // A capital that is two letters in upper case ("ß" → "SS") is "Ss" in title case.
    out += cased ? (previousIsCased ? lower : upper.charAt(0) + upper.slice(1).toLowerCase()) : ch
    previousIsCased = cased
  }
  return out
    .replace(/([a-z])'([A-Z])/g, (m) => m.toLowerCase())
    .replace(/\d([A-Z])/g, (m) => m.toLowerCase())
}
