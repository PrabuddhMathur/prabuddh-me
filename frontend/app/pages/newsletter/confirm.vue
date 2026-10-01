<script setup lang="ts">
import type { NewsletterResponse } from '~/types/api'

// /newsletter/confirm/?token=...: the link in the confirmation email. The token is posted to the
// backend while the page renders on the server. Laid out like a static page.
const route = useRoute()
const { data: site } = await useSiteSettings()
const form = computed(() => (site.value?.footer.show_newsletter ? ' with the form below' : ''))

const token = typeof route.query.token === 'string' ? route.query.token : ''

const result = ref<NewsletterResponse | null>(null)
let failed: 'invalid' | 'error' | null = token ? null : 'invalid'
if (token) {
  const { data, error } = await useApi<NewsletterResponse>('/api/v2/newsletter/confirm/', {
    method: 'POST',
    body: { token },
    key: `newsletter-confirm-${token}`,
    watch: false,
  })
  result.value = data.value ?? null
  if (error.value) failed = error.value.statusCode === 404 ? 'invalid' : 'error'
  else if (!data.value) failed = 'error'
}

const view = computed(() => {
  if (failed === 'invalid') {
    return { title: 'This link doesn\'t work', text: `It may be incomplete or out of date. Try subscribing again${form.value}.` }
  }
  if (failed === 'error') return { title: 'Something went wrong', text: 'Please try again later.' }
  if (result.value?.status === 'subscribed') {
    return { title: 'You\'re subscribed', text: `Thanks for confirming. New posts will arrive at ${result.value.email}.` }
  }
  if (result.value?.status === 'unsubscribed') {
    return { title: 'You\'ve unsubscribed', text: `This address unsubscribed earlier. To get new posts again, subscribe${form.value}.` }
  }
  return { title: 'Something went wrong', text: 'Please try again later.' }
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

        <div v-if="!failed && result?.status === 'subscribed'">
            <NuxtLink to="/blog/" class="btn btn-primary">Read the blog</NuxtLink>
        </div>
    </article>
</div>
</template>
