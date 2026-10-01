<script setup lang="ts">
import type { NuxtError } from '#app'

// 404: the old 404.html, inside the normal layout.
// Anything else: the old 500.html, a standalone page (no header or footer) that was always
// light and used the system sans font (it had no theme script and no web font).
const props = defineProps<{ error: NuxtError }>()

const notFound = computed(() => (props.error.statusCode ?? props.error.status) === 404)

if (notFound.value) usePageSeo({ title: 'Page Not Found' })
else useHead({ title: 'Internal Server Error' })
</script>

<template>
  <NuxtLayout v-if="notFound">
    <div class="max-w-4xl mx-auto px-6 lg:px-12 py-16 md:py-24">
      <div class="text-center">
        <div class="text-8xl mb-6">🔍</div>

        <div class="text-6xl md:text-7xl font-bold mb-4 bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
          404
        </div>

        <h1 class="text-3xl md:text-4xl font-bold mb-4 text-base-content">Page Not Found</h1>

        <p class="text-lg text-base-content/70 mb-8 max-w-md mx-auto leading-relaxed">
          The page you're looking for doesn't exist or has been moved. Let's get you back on track!
        </p>

        <div class="flex flex-col sm:flex-row gap-4 justify-center items-center">
          <NuxtLink to="/" class="btn btn-primary gap-2 min-h-[44px]">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
            </svg>
            Go to Home
          </NuxtLink>
          <NuxtLink to="/blog/" class="btn btn-outline gap-2 min-h-[44px]">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" />
            </svg>
            Browse Blog
          </NuxtLink>
        </div>
      </div>
    </div>
  </NuxtLayout>

  <div v-else data-theme="light" class="font-sans min-h-screen flex items-center justify-center bg-base-100">
    <div class="max-w-4xl mx-auto px-6 lg:px-12">
      <div class="text-center">
        <div class="text-8xl mb-6">⚠️</div>

        <div class="text-6xl md:text-7xl font-bold mb-4 bg-gradient-to-r from-error to-warning bg-clip-text text-transparent">
          500
        </div>

        <h1 class="text-3xl md:text-4xl font-bold mb-4 text-base-content">Internal Server Error</h1>

        <p class="text-lg text-base-content/70 mb-8 max-w-md mx-auto leading-relaxed">
          Oops! Something went wrong on our end. We're working to fix it. Please try again in a few moments.
        </p>

        <NuxtLink to="/" class="btn btn-primary gap-2 min-h-[44px]">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
          </svg>
          Go to Home
        </NuxtLink>
      </div>
    </div>
  </div>
</template>
