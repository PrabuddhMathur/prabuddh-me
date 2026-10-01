<script setup lang="ts">
// Old core/base.html <body>: header, main content, footer in a full-height column.
const { data: site } = await useSiteSettings()
</script>

<template>
  <div class="min-h-screen flex flex-col">
    <SiteHeader v-if="site" :header="site.header" />
    <main class="flex-grow">
      <slot />
    </main>
    <SiteFooter v-if="site" :footer="site.footer" :author-name="site.author.name" />
  </div>
</template>
