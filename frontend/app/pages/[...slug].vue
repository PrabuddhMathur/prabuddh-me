<script setup lang="ts">
import type { BlogPageData, PageData, StaticPageData } from '~/types/api'

// Static pages (/about/, /contact/, ...): the CMS page at this tree path.
const route = useRoute()
const { data: page, error } = await useApi<PageData>('/api/v2/pages/find/', { query: { html_path: route.path } })

if (error.value?.statusCode === 404) {
  throw createError({ statusCode: 404, statusMessage: 'Page Not Found', fatal: true })
}
if (error.value || !page.value) {
  throw createError({ statusCode: 500, statusMessage: 'Could not load the page', fatal: true })
}
// A blog post's tree path (/<slug>/) moves to its date URL.
if (page.value.meta.type === 'blog.BlogPage') {
  await navigateTo((page.value as BlogPageData).url, { redirectCode: 301, replace: true })
}
// Anything else here that isn't a static page (only the home page, which lives at /) has no page.
else if (page.value.meta.type !== 'core.StaticPage') {
  throw createError({ statusCode: 404, statusMessage: 'Page Not Found', fatal: true })
}

// The page, once it is known to be a static page (nested discriminants don't narrow in TypeScript).
const staticPage = computed(() => (page.value?.meta.type === 'core.StaticPage' ? (page.value as StaticPageData) : undefined))

usePageSeo(() => ({
  title: staticPage.value ? staticPage.value.meta.seo_title || staticPage.value.title : undefined,
  page: staticPage.value,
}))
</script>

<template>
  <StaticPageView v-if="staticPage" :page="staticPage" />
</template>
