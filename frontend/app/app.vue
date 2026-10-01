<script setup lang="ts">
const { data: site } = useSiteSettings()

// Google Analytics: only in production builds, only when the site settings have an ID
// (the old site's two gtag snippets).
if (!import.meta.dev) {
  useHead({
    script: () => {
      const id = site.value?.google_analytics_id ?? ''
      if (!/^[\w-]+$/.test(id)) return []
      return [
        { src: `https://www.googletagmanager.com/gtag/js?id=${id}`, async: true },
        {
          innerHTML: `window.dataLayer = window.dataLayer || [];
function gtag(){dataLayer.push(arguments);}
gtag('js', new Date());
gtag('config', '${id}');`,
        },
      ]
    },
  })
}
</script>

<template>
  <NuxtLayout>
    <NuxtPage />
  </NuxtLayout>
</template>
