import type { ApiImage, PageMeta, SeoFields } from '~/types/api'

/** The fields usePageSeo reads from a page (every page detail response has them). */
export interface SeoPage extends SeoFields {
  title: string
  meta: Pick<PageMeta, 'seo_title' | 'search_description'>
}

export interface PageSeoOptions {
  /** The document <title>, exactly as the old page had it (no site name suffix). */
  title?: string
  /** A page from the API (home, blog post, static page, preview): the old `page` tags. */
  page?: SeoPage | null
  /**
   * Pages without a CMS page (blog listing and archives): the old `seo_meta` dictionary.
   * Ignored when `page` is given.
   */
  seoMeta?: { title: string, description: string } | null
  /**
   * og:image when the page has no og_image: the blog post's featured_image or the home page's
   * hero_image (their `og` rendition). Only used together with `page`.
   */
  fallbackImage?: ApiImage | null
  /** Adds <meta name="robots" content="noindex"> (previews). */
  noindex?: boolean
}

type MetaTag = { name: string, content: string } | { property: string, content: string }

/**
 * The old seo_meta.html: <title>, description, keywords, Open Graph, Twitter and canonical tags.
 * With neither `page` nor `seoMeta` (search, 404) only the generic tags are added, as before.
 *   usePageSeo(() => ({ title: page.value.meta.seo_title || page.value.title, page: page.value }))
 *   usePageSeo({ title: 'Blog - All Posts', seoMeta: { title: 'Blog - All Posts', description: 'Browse all blog posts' } })
 */
export function usePageSeo(options: MaybeRefOrGetter<PageSeoOptions>) {
  const { data: site } = useSiteSettings()
  const route = useRoute()
  const siteUrl = useRuntimeConfig().public.siteUrl

  // The old request.build_absolute_uri: this page's full URL, query string included.
  const pageUrl = computed(() => absoluteUrl(route.fullPath.split('#')[0] ?? '/', siteUrl))

  const meta = computed(() => {
    const { page, seoMeta, fallbackImage, noindex } = toValue(options)
    const siteName = site.value?.site_name ?? ''
    const siteDescription = site.value?.default_meta_description ?? ''
    const tags: MetaTag[] = []

    let title: string | undefined
    let description: string | undefined
    let socialDescription: string | undefined
    if (page) {
      title = page.og_title || page.title
      description = page.meta_description || page.meta.search_description || siteDescription || page.title
      socialDescription = page.og_description || description
    } else if (seoMeta) {
      title = seoMeta.title
      description = seoMeta.description || siteDescription
      socialDescription = description
    }

    const og = page ? (page.og_image ?? fallbackImage)?.renditions.og : undefined
    const ogUrl = og ? absoluteUrl(og.url, siteUrl) : undefined

    if (description !== undefined) tags.push({ name: 'description', content: description })
    if (page?.meta_keywords) tags.push({ name: 'keywords', content: page.meta_keywords })
    if (title !== undefined) tags.push({ property: 'og:title', content: title })
    if (socialDescription !== undefined) tags.push({ property: 'og:description', content: socialDescription })
    tags.push({ property: 'og:type', content: 'website' })
    tags.push({ property: 'og:url', content: pageUrl.value })
    if (ogUrl) {
      tags.push(
        { property: 'og:image', content: ogUrl },
        { property: 'og:image:secure_url', content: ogUrl },
        { property: 'og:image:width', content: '1200' },
        { property: 'og:image:height', content: '630' },
      )
    }
    if (siteName) tags.push({ property: 'og:site_name', content: siteName })
    tags.push({ name: 'twitter:card', content: 'summary_large_image' })
    if (title !== undefined) tags.push({ name: 'twitter:title', content: title })
    if (socialDescription !== undefined) tags.push({ name: 'twitter:description', content: socialDescription })
    if (ogUrl) tags.push({ name: 'twitter:image', content: ogUrl })
    if (noindex) tags.push({ name: 'robots', content: 'noindex' })
    return tags
  })

  useHead({
    title: () => toValue(options).title,
    meta,
    link: () => [{ rel: 'canonical', href: pageUrl.value }],
  })
}
