<script setup lang="ts">
import type { HomePageData, PageData } from '~/types/api'

// The home page: the CMS page at the site root.
const { data: page, error } = await useApi<PageData>('/api/v2/pages/find/', { query: { html_path: '/' } })

if (error.value?.statusCode === 404) {
  throw createError({ statusCode: 404, statusMessage: 'Page Not Found', fatal: true })
}
if (error.value || page.value?.meta.type !== 'home.HomePage') {
  throw createError({ statusCode: 500, statusMessage: 'Could not load the home page', fatal: true })
}

// The old title: "{title} - {hero_subtitle}", or just the title.
const home = computed(() => (page.value?.meta.type === 'home.HomePage' ? (page.value as HomePageData) : undefined))

usePageSeo(() => ({
  title: home.value?.hero_subtitle ? `${home.value.title} - ${home.value.hero_subtitle}` : home.value?.title,
  page: home.value,
  fallbackImage: home.value?.hero_image,
}))
</script>

<template>
  <HomePageView v-if="home" :page="home" />
</template>
