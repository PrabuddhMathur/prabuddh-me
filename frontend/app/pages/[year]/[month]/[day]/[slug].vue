<script setup lang="ts">
import type { BlogPageData, PagesListResponse } from '~/types/api'

definePageMeta({ path: '/:year(\\d{4})/:month(\\d{1,2})/:day(\\d{1,2})/:slug' })

// A blog post at /YYYY/MM/DD/slug/. The slug is unique among posts and the date in the URL
// has to be the post's date (otherwise there's no such page). Like the old site, 3/3 and 03/03
// both match.
const route = useRoute()
const { data, error } = await useApi<PagesListResponse<BlogPageData>>('/api/v2/pages/', {
  query: { type: 'blog.BlogPage', slug: String(route.params.slug), fields: '*' },
})

if (error.value && error.value.statusCode !== 404) {
  throw createError({ statusCode: 500, statusMessage: 'Could not load the post', fatal: true })
}

const page = computed(() => {
  const [year, month, day] = [route.params.year, route.params.month, route.params.day].map(value => Number(value))
  return data.value?.items.find((post) => {
    const [postYear, postMonth, postDay] = post.date.split('-').map(Number)
    return postYear === year && postMonth === month && postDay === day
  })
})

if (!page.value) {
  throw createError({ statusCode: 404, statusMessage: 'Page Not Found', fatal: true })
}

usePageSeo(() => ({
  title: page.value ? page.value.meta.seo_title || page.value.title : undefined,
  page: page.value,
  fallbackImage: page.value?.featured_image,
}))
</script>

<template>
  <BlogPostView v-if="page" :page="page" />
</template>
