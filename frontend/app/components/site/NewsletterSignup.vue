<script setup lang="ts">
import type { NewsletterResponse } from '~/types/api'

// Old core/sections/newsletter-signup.html. The card/card-body classes are replaced by
// daisyUI's effective styles. With JavaScript the form posts JSON to the backend; without it
// the form posts to the same endpoint, which redirects to /newsletter/?status=...
const { $api } = useNuxtApp()

const email = ref('')
const website = ref('') // honeypot: real visitors never see or fill it
const sending = ref(false)
const done = ref(false)
const error = ref('')

const messages: Record<string, string> = {
  invalid_email: 'Please enter a valid email address.',
  rate_limited: 'Too many attempts. Please try again in a few minutes.',
}

async function subscribe() {
  if (sending.value) return
  sending.value = true
  error.value = ''
  try {
    await $api<NewsletterResponse>('/api/v2/newsletter/subscribe/', {
      method: 'POST',
      body: { email: email.value, website: website.value },
    })
    done.value = true
  } catch (e) {
    const status = (e as { data?: { status?: string } }).data?.status ?? ''
    error.value = messages[status] ?? 'Something went wrong. Please try again later.'
  } finally {
    sending.value = false
  }
}
</script>

<template>
  <div class="relative flex flex-col rounded-box bg-gradient-to-br from-primary/5 to-secondary/5 border border-primary/10">
    <div class="flex flex-auto flex-col gap-2 p-6 text-[0.875rem] text-center items-center">
      <h3 class="text-2xl font-bold mb-2">Stay Updated</h3>
      <p class="grow text-base-content/70 mb-4">Get new posts delivered to your inbox</p>
      <p v-if="done" class="text-base-content/80" role="status">Thanks! Check your inbox for a link to confirm your subscription.</p>
      <form v-else class="gap-4" method="post" action="/api/v2/newsletter/subscribe/" @submit.prevent="subscribe">
        <input
          v-model="email"
          type="email"
          name="email"
          placeholder="your@email.com"
          class="input w-full mb-4"
          required
          aria-label="Email address"
        >
        <button type="submit" class="btn btn-primary" :disabled="sending">Subscribe</button>
        <div class="hidden" aria-hidden="true"><input v-model="website" type="text" name="website" tabindex="-1" autocomplete="off"></div>
      </form>
      <p v-if="error" class="text-sm text-base-content/80 mt-2" role="alert">{{ error }}</p>
    </div>
  </div>
</template>
