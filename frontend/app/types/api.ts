// Types for every JSON shape the backend returns (see the API contract).
// URLs in responses are root-relative paths (/2025/03/14/slug/, /media/images/x.jpg).

export interface Rendition {
  url: string
  width: number
  height: number
}

/** An image with the named renditions each endpoint lists (card, list, og, ...). */
export interface ApiImage {
  id: number
  /** Used as the alt text, as the old templates did. */
  title: string
  renditions: Record<string, Rendition>
}

export interface Tag {
  name: string
  slug: string
}

export interface LinkItem {
  text: string
  url: string
}

/** Listings, the home page, the recent-posts block. */
export interface PostSummary {
  id: number
  title: string
  slug: string
  /** /YYYY/MM/DD/slug/ */
  url: string
  /** YYYY-MM-DD */
  date: string
  /** ISO 8601 UTC, or null. */
  first_published_at: string | null
  intro: string
  featured: boolean
  estimated_reading_time: number
  tags: Tag[]
  /** Renditions: card, list (+ thumb, grid, cards inside the recent-posts block). */
  featured_image: ApiImage | null
}

/** Previous/next post links on a blog post. */
export interface PostLink {
  title: string
  url: string
  intro: string
}

// StreamField blocks

export type Alignment = 'left' | 'center' | 'right'

interface BlockBase<T extends string, V> {
  type: T
  value: V
  id: string
}

export type HeadingBlockValue = {
  heading_text: string
  heading_level: 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6'
  alignment: Alignment
}

export type TextBlockValue = {
  /** Front-end HTML (internal links resolved, spoilers as span.spoiler). */
  text: string
  alignment: Alignment | 'justify'
}

export type ImageBlockValue = {
  /** Renditions: display, full. */
  image: ApiImage | null
  caption: string
  alt_text: string
  alignment: Alignment | 'full'
}

export type QuoteBlockValue = {
  quote: string
  author: string
  author_title: string
  style: 'default' | 'large' | 'bordered' | 'accent'
}

export type ButtonBlockValue = {
  button_text: string
  button_url: string
  button_size: 'xs' | 'sm' | 'md' | 'lg'
  open_in_new_tab: boolean
}

export type SpacerBlockValue = {
  height: 'small' | 'medium' | 'large' | 'xlarge'
}

export type HeroBlockValue = {
  title: string
  subtitle: string
  /** Renditions: original. */
  background_image: ApiImage | null
  background_overlay: boolean
  height: 'small' | 'medium' | 'large' | 'full'
  cta_text: string
  cta_link: string
}

export type CtaBlockValue = {
  title: string
  description: string
  button_text: string
  button_link: string
  background_color: 'transparent' | 'base-100' | 'base-200' | 'primary' | 'secondary' | 'accent'
  text_alignment: Alignment
}

export type AuthorBioBlockValue = {
  author_name: string
  /** Renditions: avatar. */
  author_image: ApiImage | null
  /** Front-end HTML. */
  bio_text: string
  website_url: string
  twitter_url: string
  linkedin_url: string
  github_url: string
  email: string
  show_social_icons: boolean
}

export type RecentPostsBlockValue = {
  title: string
  number_of_posts: number
  show_excerpt: boolean
  show_date: boolean
  show_featured_image: boolean
  layout_style: 'list' | 'grid' | 'cards'
  /** Each featured_image also has thumb, grid and cards renditions. */
  posts: PostSummary[]
}

export type HeadingBlock = BlockBase<'heading', HeadingBlockValue>
export type TextBlock = BlockBase<'text', TextBlockValue>
export type ImageBlock = BlockBase<'image', ImageBlockValue>
export type QuoteBlock = BlockBase<'quote', QuoteBlockValue>
export type ButtonBlock = BlockBase<'button', ButtonBlockValue>
export type SpacerBlock = BlockBase<'spacer', SpacerBlockValue>
export type HeroBlock = BlockBase<'hero', HeroBlockValue>
export type CtaBlock = BlockBase<'cta', CtaBlockValue>
export type AuthorBioBlock = BlockBase<'author_bio', AuthorBioBlockValue>
export type RecentPostsBlock = BlockBase<'recent_posts', RecentPostsBlockValue>

/** One StreamField block; narrow on `type`. */
export type StreamBlock =
  | HeadingBlock
  | TextBlock
  | ImageBlock
  | QuoteBlock
  | ButtonBlock
  | SpacerBlock
  | HeroBlock
  | CtaBlock
  | AuthorBioBlock
  | RecentPostsBlock

export type StreamBlockType = StreamBlock['type']

// Pages

export type PageType = 'home.HomePage' | 'blog.BlogPage' | 'core.StaticPage'

/** Wagtail's `meta` on page detail responses. */
export interface PageMeta {
  type: PageType
  slug: string
  seo_title: string
  search_description: string
  first_published_at: string | null
  last_published_at?: string | null
  html_url: string | null
  [key: string]: unknown
}

export interface SeoFields {
  meta_description: string
  meta_keywords: string
  og_title: string
  og_description: string
  /** Renditions: og. */
  og_image: ApiImage | null
}

interface PageBase<T extends PageType> extends SeoFields {
  id: number
  meta: PageMeta & { type: T }
  title: string
}

export interface HomePageData extends PageBase<'home.HomePage'> {
  hero_title: string
  hero_subtitle: string
  /** Renditions: hero, og. */
  hero_image: ApiImage | null
  hero_cta_text: string
  hero_cta_link: string
  hero_text_horizontal: Alignment
  hero_text_vertical: 'top' | 'center' | 'bottom'
  body: StreamBlock[]
  show_featured_posts: boolean
  featured_posts_title: string
  featured_posts: PostSummary[]
  show_recent_posts: boolean
  recent_posts_title: string
  recent_posts: PostSummary[]
  show_author_sidebar: boolean
}

export type LineHeight = 'default' | 'normal' | 'comfortable' | 'relaxed' | 'spacious' | 'loose'

export interface BlogPageData extends PageBase<'blog.BlogPage'> {
  /** YYYY-MM-DD */
  date: string
  /** /YYYY/MM/DD/slug/ */
  url: string
  intro: string
  featured: boolean
  estimated_reading_time: number
  line_height: LineHeight
  /** Renditions: display, full, og. */
  featured_image: ApiImage | null
  featured_image_caption: string
  body: StreamBlock[]
  tags: Tag[]
  /** The next older post. */
  previous_post: PostLink | null
  /** The next newer post. */
  next_post: PostLink | null
}

export interface StaticPageData extends PageBase<'core.StaticPage'> {
  intro: string
  body: StreamBlock[]
  show_last_updated: boolean
  /** ISO 8601 UTC, or null. */
  last_updated: string | null
}

/** Any page detail response (find, page_preview); narrow on `meta.type`. */
export type PageData = HomePageData | BlogPageData | StaticPageData

/** Wagtail's standard listing (e.g. /api/v2/pages/?type=blog.BlogPage&slug=...&fields=*). */
export interface PagesListResponse<T> {
  meta: { total_count: number }
  items: T[]
}

// Custom endpoints

export type SocialIcon = 'globe' | 'twitter' | 'linkedin' | 'github' | 'mastodon' | 'email'

export interface SocialLink {
  name: 'Website' | 'Twitter' | 'LinkedIn' | 'GitHub' | 'Mastodon' | 'Email'
  url: string
  icon: SocialIcon
}

/** GET /api/v2/site/ */
export interface SiteSettings {
  site_name: string
  default_meta_description: string
  google_analytics_id: string
  header: {
    site_title: string
    show_logo: boolean
    /** Renditions: logo. */
    logo: ApiImage | null
    navigation: LinkItem[]
    show_search: boolean
    show_theme_toggle: boolean
    header_style: 'sticky' | 'static'
  }
  footer: {
    copyright_text: string
    show_year: boolean
    show_newsletter: boolean
    show_quick_links: boolean
    links: LinkItem[]
  }
  author: {
    name: string
    title: string
    bio_short: string
    /** Renditions: sidebar. */
    image: ApiImage | null
    social_links: SocialLink[]
  }
}

/** GET /api/v2/posts/ */
export interface PostsResponse {
  count: number
  page: number
  num_pages: number
  per_page: number
  tag: Tag | null
  results: PostSummary[]
}

export interface SearchResult {
  id: number
  title: string
  url: string
  search_description: string
  type: string
  /** e.g. "Blogpage" (the old `content_type.model|title`). */
  type_label: string
}

/** GET /api/v2/search/ */
export interface SearchResponse {
  query: string
  count: number
  page: number
  num_pages: number
  per_page: number
  results: SearchResult[]
}

// Newsletter: /api/v2/newsletter/{subscribe,confirm,unsubscribe}/ (JSON in, JSON out).

/** The `status` of a newsletter response. 'ok' answers a signup; the others are errors or states. */
export type NewsletterStatus =
  | 'ok'
  | 'invalid_email'
  | 'rate_limited'
  | 'email_failed'
  | 'subscribed'
  | 'unsubscribed'
  | 'invalid_token'

export interface NewsletterResponse {
  status: NewsletterStatus
  /** Only on confirm and unsubscribe answers (subscribed, unsubscribed). */
  email?: string
}

// Comments: GET and POST /api/v2/comments/, POST /api/v2/comments/alerts/{confirm,stop}/.

export interface CommentReplyTo {
  id: number
  name: string
}

/** One public comment. */
export interface CommentData {
  id: number
  name: string
  /** Plain text; may contain line breaks and URLs. */
  body: string
  /** ISO 8601 UTC. */
  created_at: string
  /** Written by the site owner. */
  is_author: boolean
  /** The owner's heart. */
  liked: boolean
}

/** A reply, flattened under its thread's top-level comment. */
export interface CommentReply extends CommentData {
  /** The comment answered, when it is not the top-level one. */
  reply_to: CommentReplyTo | null
}

export interface CommentThread extends CommentData {
  /** Every reply of the thread (all depths), oldest first. */
  replies: CommentReply[]
}

export interface CommentsResponse {
  /** Comments are switched on for the site. When false, nothing else is worth showing. */
  enabled: boolean
  /** Enabled, and this post accepts new comments. */
  open: boolean
  /** Text of the owner's heart badge. */
  like_label: string
  /** Akismet is configured (for the privacy note). */
  akismet: boolean
  /** Visible comments, replies included. */
  count: number
  /** Signed time stamp the form posts back. */
  form_token: string
  comments: CommentThread[]
}

export type CommentSubmitStatus = 'pending' | 'invalid' | 'closed' | 'not_found' | 'rate_limited'

export interface CommentSubmitResponse {
  status: CommentSubmitStatus
  /** With status "invalid": a sentence per field. */
  errors?: Partial<Record<'name' | 'email' | 'body' | 'parent', string>>
}

/** The answer of the reply-alert confirm and stop endpoints. */
export interface ReplyAlertsResponse {
  status: 'on' | 'off' | 'invalid_token'
  /** The comment's post, when the token is known. */
  post?: { title: string, url: string }
}
