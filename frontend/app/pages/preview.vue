<script setup lang="ts">
import type { BlogPageData, HomePageData, PageData, StaticPageData } from '~/types/api'

// The Wagtail "preview" and "View live" target (wagtail_headless_preview): the draft stored under
// ?content_type=<app.model>&token=<token>, rendered with the same views as the live pages.
const route = useRoute()

function param(value: unknown): string {
  return String((Array.isArray(value) ? value.at(-1) : value) ?? '')
}
const contentType = param(route.query.content_type)
const token = param(route.query.token)

if (!contentType || !token) {
  throw createError({ statusCode: 404, statusMessage: 'Page Not Found', fatal: true })
}

const { data: page, error } = await useApi<PageData>('/api/v2/page_preview/', {
  query: { content_type: contentType, token },
})

if (error.value?.statusCode === 404) {
  throw createError({ statusCode: 404, statusMessage: 'Page Not Found', fatal: true })
}
if (error.value || !page.value) {
  throw createError({ statusCode: 500, statusMessage: 'Could not load the preview', fatal: true })
}

const type = computed(() => page.value?.meta.type)
const home = computed(() => (type.value === 'home.HomePage' ? (page.value as HomePageData) : undefined))
const post = computed(() => (type.value === 'blog.BlogPage' ? (page.value as BlogPageData) : undefined))
const staticPage = computed(() => (type.value === 'core.StaticPage' ? (page.value as StaticPageData) : undefined))

usePageSeo(() => ({
  title: page.value?.title,
  page: page.value,
  fallbackImage: home.value?.hero_image ?? post.value?.featured_image,
  noindex: true,
}))
</script>

<template>
  <HomePageView v-if="home" :page="home" />
  <BlogPostView v-else-if="post" :page="post" :show-comments="false" />
  <StaticPageView v-else-if="staticPage" :page="staticPage" />
</template>
