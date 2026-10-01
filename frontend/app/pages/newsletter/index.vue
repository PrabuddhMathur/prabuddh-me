<script setup lang="ts">
// /newsletter/: where the no-JavaScript signup form lands (the backend redirects to ?status=...).
// Not in the old site. It is laid out like a static page (components/page/StaticPageView.vue).
const route = useRoute()
const { data: site } = await useSiteSettings()

if (!site.value?.footer.show_newsletter) {
  throw createError({ statusCode: 404, statusMessage: 'Page Not Found', fatal: true })
}

const status = computed(() => (typeof route.query.status === 'string' ? route.query.status : ''))

const view = computed(() => {
  switch (status.value) {
    case '':
      return { title: 'Newsletter', text: 'Get new posts delivered to your inbox. Subscribe with the form below.' }
    case 'ok':
      return {
        title: 'Check your inbox',
        text: 'An email with a link to confirm your subscription is on its way. If it doesn\'t arrive in a few minutes, check your spam folder.',
      }
    case 'invalid_email':
      return { title: 'That email address doesn\'t look right', text: 'Please check it and try again with the form below.' }
    case 'rate_limited':
      return { title: 'Too many attempts', text: 'Please wait a few minutes and try again.' }
    default:
      return { title: 'Something went wrong', text: 'The confirmation email couldn\'t be sent. Please try again later.' }
  }
})

usePageSeo({ title: 'Newsletter', noindex: true })
</script>

<template>
<div class="max-w-7xl mx-auto px-6 lg:px-12 py-12">
    <article class="max-w-4xl mx-auto">
        <nav class="text-sm mb-8 text-base-content/60" aria-label="Breadcrumb">
            <ol class="flex items-center gap-2">
                <li><NuxtLink to="/" class="hover:text-base-content transition-colors">Home</NuxtLink></li>
                <li><span class="text-base-content/40">/</span></li>
                <li class="text-base-content font-medium">Newsletter</li>
            </ol>
        </nav>

        <header class="mb-12">
            <h1 class="text-4xl md:text-5xl font-bold mb-6 leading-tight">{{ view.title }}</h1>
            <div class="prose prose-lg max-w-none mb-8">
                <p class="text-xl text-base-content/80 leading-relaxed">{{ view.text }}</p>
            </div>
        </header>
    </article>
</div>
</template>
