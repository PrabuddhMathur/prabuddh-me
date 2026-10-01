<script setup lang="ts">
import type { PostsResponse } from '~/types/api'

definePageMeta({ path: '/:year(\\d{4})/:month(\\d{1,2})/:day(\\d{1,2})' })

const route = useRoute()
const year = computed(() => Number(route.params.year))
const month = computed(() => Number(route.params.month))
const day = computed(() => Number(route.params.day))
const { data, error } = await useApi<PostsResponse>('/api/v2/posts/', {
  query: computed(() => ({
    page: [route.query.page].flat()[0] ?? 1,
    year: year.value,
    month: month.value,
    day: day.value,
  })),
})
if (error.value) {
  throw createError(error.value.statusCode === 404
    ? { statusCode: 404, statusMessage: 'Page Not Found', fatal: true }
    : { statusCode: 500, statusMessage: 'Internal Server Error', fatal: true })
}

const longDate = computed(() => formatDate({ year: year.value, month: month.value, day: day.value }, 'F d, Y'))
const isoDate = computed(() => formatDate({ year: year.value, month: month.value, day: day.value }, 'Y-m-d'))

usePageSeo(() => ({
  title: `Blog Archive - ${longDate.value}`,
  seoMeta: { title: `Blog Archive - ${longDate.value}`, description: `Blog posts from ${longDate.value}` },
}))
</script>

<template>
  <PostListing
    v-if="data"
    variant="archive"
    :heading="`Posts from ${isoDate}`"
    :count="data.count"
    :posts="data.results"
    :page="data.page"
    :num-pages="data.num_pages"
  />
</template>
