import type { ApiImage, Rendition } from '~/types/api'

/** The tag archive, /blog/tag/<slug>/ (the old `{% url 'blog_tag_archive' tag.slug %}`). */
export function tagUrl(slug: string): string {
  return `/blog/tag/${slug}/`
}

/**
 * True for a root-relative path ("/about/", "/blog/?page=2"): render it with <NuxtLink>.
 * False for "https://…", "//host/…", "mailto:…", "#top", "" and so on: keep a plain <a>.
 */
export function isInternalUrl(url: string | null | undefined): url is string {
  return !!url && url.startsWith('/') && !url.startsWith('//')
}

/** An absolute URL for a root-relative path (canonical and Open Graph URLs). Absolute URLs pass through. */
export function absoluteUrl(url: string, siteUrl: string): string {
  if (/^[a-z][a-z\d+.-]*:/i.test(url) || url.startsWith('//')) return url
  return siteUrl.replace(/\/+$/, '') + (url.startsWith('/') ? url : `/${url}`)
}

/** A named rendition of an API image (e.g. `rendition(post.featured_image, 'card')`). */
export function rendition(image: ApiImage | null | undefined, name: string): Rendition | undefined {
  return image?.renditions[name]
}
