<script setup lang="ts">
import type { ReplyAlertsResponse } from '~/types/api'

// /comments/alerts/stop/?token=...: the "stop these emails" link in every reply alert. A page
// with a button, because opening a link must never change anything (mail scanners open links).
// Without JavaScript the form posts to the backend, which redirects back here with ?status=...
// Laid out like a static page.
const route = useRoute()
const { $api } = useNuxtApp()

const token = typeof route.query.token === 'string' ? route.query.token : ''
const status = typeof route.query.status === 'string' ? route.query.status : ''

type State = 'form' | 'off' | 'invalid' | 'error'
const state = ref<State>(
  status === 'off' ? 'off'
    : status === 'invalid_token' ? 'invalid'
      : status ? 'error'
        : token ? 'form' : 'invalid',
)
const sending = ref(false)

async function stop() {
  if (sending.value) return
  sending.value = true
  try {
    await $api<ReplyAlertsResponse>('/api/v2/comments/alerts/stop/', { method: 'POST', body: { token } })
    state.value = 'off'
  } catch (e) {
    const code = (e as { statusCode?: number, data?: { status?: string } })
    state.value = code.statusCode === 404 || code.data?.status === 'invalid_token' ? 'invalid' : 'error'
  } finally {
    sending.value = false
  }
}

const view = computed(() => {
  switch (state.value) {
    case 'form':
      return { title: 'Stop reply emails', text: 'Stop getting emails about replies to your comment?' }
    case 'off':
      return { title: 'Reply emails are off', text: 'You won\'t get any more emails about replies to this comment.' }
    case 'invalid':
      return { title: 'This link doesn\'t work', text: 'It may be incomplete. Use the stop link from the latest reply email you received.' }
    default:
      return { title: 'Something went wrong', text: 'Please try again later.' }
  }
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
                <p class="text-xl text-base-content/80 leading-relaxed">{{ view.text }}</p>
            </div>
        </header>

        <form v-if="state === 'form'" method="post" action="/api/v2/comments/alerts/stop/" @submit.prevent="stop">
            <input type="hidden" name="token" :value="token">
            <button type="submit" class="btn btn-primary" :disabled="sending">Stop emails</button>
        </form>
    </article>
</div>
</template>
