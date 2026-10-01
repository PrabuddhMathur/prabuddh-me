import type { SiteSettings } from '~/types/api'

/**
 * The site settings (/api/v2/site/): header, footer, author, SEO defaults.
 * `const { data: site } = await useSiteSettings()`; `site.value` is undefined if the request failed.
 * Every caller shares one request per page load (fixed key, pending requests are reused,
 * and later calls, including after client-side navigation, reuse the fetched data).
 */
export function useSiteSettings() {
  return useApi<SiteSettings>('/api/v2/site/', {
    key: 'site-settings',
    dedupe: 'defer',
    getCachedData: (key, nuxtApp) => nuxtApp.payload.data[key] ?? nuxtApp.static.data[key],
  })
}
