<script setup lang="ts">
import type { PostsResponse } from '~/types/api'

definePageMeta({ path: '/:year(\\d{4})/:month(\\d{1,2})' })

const route = useRoute()
const year = computed(() => String(route.params.year))
const month = computed(() => Number(route.params.month))
const { data, error } = await useApi<PostsResponse>('/api/v2/posts/', {
  query: computed(() => ({ page: [route.query.page].flat()[0] ?? 1, year: Number(year.value), month: month.value })),
})
if (error.value) {
  throw createError(error.value.statusCode === 404
    ? { statusCode: 404, statusMessage: 'Page Not Found', fatal: true }
    : { statusCode: 500, statusMessage: 'Internal Server Error', fatal: true })
}

const monthYear = computed(() => `${MONTH_NAMES[month.value - 1]} ${year.value}`)

usePageSeo(() => ({
  title: `Blog Archive - ${monthYear.value}`,
  seoMeta: { title: `Blog Archive - ${monthYear.value}`, description: `Blog posts from ${monthYear.value}` },
}))
</script>

<template>
  <PostListing
    v-if="data"
    variant="archive"
    :heading="`Posts from ${monthYear}`"
    :count="data.count"
    :posts="data.results"
    :page="data.page"
    :num-pages="data.num_pages"
  />
</template>
