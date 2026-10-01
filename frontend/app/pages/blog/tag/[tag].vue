<script setup lang="ts">
import type { PostsResponse } from '~/types/api'

const route = useRoute()
const { data, error } = await useApi<PostsResponse>('/api/v2/posts/', {
  query: computed(() => ({ page: [route.query.page].flat()[0] ?? 1, tag: route.params.tag })),
})
if (error.value || !data.value?.tag) {
  throw createError(!error.value || error.value.statusCode === 404
    ? { statusCode: 404, statusMessage: 'Page Not Found', fatal: true }
    : { statusCode: 500, statusMessage: 'Internal Server Error', fatal: true })
}

const title = computed(() => `Posts tagged "${data.value?.tag?.name}"`)

usePageSeo(() => ({
  title: title.value,
  seoMeta: { title: title.value, description: `All blog posts tagged with ${data.value?.tag?.name}` },
}))
</script>

<template>
  <PostListing
    v-if="data"
    variant="archive"
    :heading="title"
    :count="data.count"
    :posts="data.results"
    :page="data.page"
    :num-pages="data.num_pages"
  />
</template>
