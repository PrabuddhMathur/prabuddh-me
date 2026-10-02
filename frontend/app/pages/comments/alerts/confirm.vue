<script setup lang="ts">
import type { ReplyAlertsResponse } from '~/types/api'

// /comments/alerts/confirm/?token=...: the link in the "Your comment is live" email. The token is
// posted to the backend while the page renders on the server. Laid out like a static page.
const route = useRoute()

const token = typeof route.query.token === 'string' ? route.query.token : ''

const result = ref<ReplyAlertsResponse | null>(null)
let failed: 'invalid' | 'error' | null = token ? null : 'invalid'
if (token) {
  const { data, error } = await useApi<ReplyAlertsResponse>('/api/v2/comments/alerts/confirm/', {
    method: 'POST',
    body: { token },
    key: `comment-alerts-confirm-${token}`,
    watch: false,
  })
  result.value = data.value ?? null
  if (error.value) failed = error.value.statusCode === 404 ? 'invalid' : 'error'
  else if (!data.value) failed = 'error'
}

const on = computed(() => !failed && result.value?.status === 'on')
const post = computed(() => result.value?.post)

const view = computed(() => {
  if (on.value) return { title: 'Reply emails are on', text: '' }
  if (failed === 'invalid') {
    return { title: 'This link doesn\'t work', text: 'It may be incomplete. Use the link in the email we sent you.' }
  }
  return { title: 'Something went wrong', text: 'Please try again later.' }
})

usePageSeo({ title: 'Comments', noindex: true })
</script>

<template>
<div class="max-w-7xl mx-auto px-6 lg:px-12 py-12">
    <article class="max-w-4xl mx-auto">
        <nav class="text-sm mb-8 text-base-content/60" aria-label="Breadcrumb">
            <ol class="flex items-center gap-2">
                <li><NuxtLink to="/" class="hover:text-base-content transition-colors">Home</NuxtLink></li>
                <li><span class="text-base-content/40">/</span></li>
                <li class="text-base-content font-medium">Comments</li>
            </ol>
        </nav>

        <header class="mb-12">
            <h1 class="text-4xl md:text-5xl font-bold mb-6 leading-tight">{{ view.title }}</h1>
            <div class="prose prose-lg max-w-none mb-8">
                <p v-if="on" class="text-xl text-base-content/80 leading-relaxed">You'll get an email when someone replies to your comment<template v-if="post"> on <NuxtLink :to="post.url">{{ post.title }}</NuxtLink></template>.</p>
                <p v-else class="text-xl text-base-content/80 leading-relaxed">{{ view.text }}</p>
            </div>
        </header>

        <div v-if="on && post">
            <NuxtLink :to="post.url" class="btn btn-primary">Back to the post</NuxtLink>
        </div>
    </article>
</div>
</template>
