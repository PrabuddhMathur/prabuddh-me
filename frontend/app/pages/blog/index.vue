<script setup lang="ts">
import type { PostsResponse } from '~/types/api'

const route = useRoute()
const { data, error } = await useApi<PostsResponse>('/api/v2/posts/', {
  query: computed(() => ({ page: [route.query.page].flat()[0] ?? 1 })),
})
if (error.value) {
  throw createError(error.value.statusCode === 404
    ? { statusCode: 404, statusMessage: 'Page Not Found', fatal: true }
    : { statusCode: 500, statusMessage: 'Internal Server Error', fatal: true })
}

usePageSeo({
  title: 'Blog - All Posts',
  seoMeta: { title: 'Blog - All Posts', description: 'Browse all blog posts' },
})
</script>

<template>
  <PostListing
    v-if="data"
    variant="listing"
    heading="All Blog Posts"
    :count="data.count"
    :posts="data.results"
    :page="data.page"
    :num-pages="data.num_pages"
  />
</template>

