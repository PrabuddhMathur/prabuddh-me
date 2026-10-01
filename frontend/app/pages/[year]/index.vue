<script setup lang="ts">
import type { PostsResponse } from '~/types/api'

definePageMeta({ path: '/:year(\\d{4})' })

const route = useRoute()
const year = computed(() => String(route.params.year))
const { data, error } = await useApi<PostsResponse>('/api/v2/posts/', {
  query: computed(() => ({ page: [route.query.page].flat()[0] ?? 1, year: Number(year.value) })),
})
if (error.value) {
  throw createError(error.value.statusCode === 404
    ? { statusCode: 404, statusMessage: 'Page Not Found', fatal: true }
    : { statusCode: 500, statusMessage: 'Internal Server Error', fatal: true })
}

usePageSeo(() => ({
  title: `Blog Archive - ${year.value}`,
  seoMeta: { title: `Blog Archive - ${year.value}`, description: `Blog posts from ${year.value}` },
}))
</script>

<template>
  <PostListing
    v-if="data"
    variant="archive"
    :heading="`Posts from ${year}`"
    :count="data.count"
    :posts="data.results"
    :page="data.page"
    :num-pages="data.num_pages"
  />
</template>
