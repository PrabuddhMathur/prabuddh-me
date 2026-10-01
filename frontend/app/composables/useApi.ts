import type { UseFetchOptions } from 'nuxt/app'

/**
 * useFetch against the backend: `const { data, error } = await useApi<PostsResponse>('/api/v2/posts/', { query })`.
 * Takes every useFetch option. Pass `key` when the same URL is fetched with different options.
 */
export function useApi<T>(
  url: string | Ref<string> | (() => string),
  options: UseFetchOptions<T> = {},
) {
  return useFetch(url, {
    ...options,
    $fetch: useNuxtApp().$api as typeof $fetch,
  })
}
