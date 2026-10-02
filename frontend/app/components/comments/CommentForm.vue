<script setup lang="ts">
import type { CommentSubmitResponse } from '~/types/api'

// The comment form, at the bottom of the comments or right under the comment it answers.
// With JavaScript it posts JSON to the backend and shows the outcome in place. Without it the
// form posts to the same endpoint, which redirects back to the post with ?comment=<status>
// (CommentSection shows the outcome then).
const props = defineProps<{
  postId: number
  formToken: string
  akismet: boolean
  /** The comment this answers. */
  parent?: { id: number, name: string } | null
  /** Shown right under a comment: Cancel button, closes on Escape, takes the focus when it opens. */
  inline?: boolean
  /** Without `inline`, a form that answers a comment links its Cancel here. */
  cancelTo?: string
  /** A problem to show on top, e.g. the outcome of a post made without JavaScript. */
  notice?: string
}>()
const emit = defineEmits<{ cancel: [] }>()

const { $api } = useNuxtApp()
const uid = useId()

type Field = 'name' | 'email' | 'body'

const name = ref('')
const email = ref('')
const body = ref('')
const notify = ref(false)
const website = ref('') // honeypot: real visitors never see or fill it
const sending = ref(false)
const done = ref(false)
const notified = ref(false)
const errors = ref<Partial<Record<Field, string>>>({})
const formError = ref(props.notice ?? '')
watch(() => props.notice, (value) => { formError.value = value ?? '' })

const fields = {
  name: useTemplateRef<HTMLInputElement>('nameEl'),
  email: useTemplateRef<HTMLInputElement>('emailEl'),
  body: useTemplateRef<HTMLTextAreaElement>('bodyEl'),
}

const MESSAGES: Record<string, string> = {
  closed: 'Comments are closed on this post.',
  rate_limited: 'Too many comments from your connection. Please try again later.',
}
const GENERIC_ERROR = 'Something went wrong. Please try again later.'
// The theme's error colour, darkened (light) or lightened (dim) towards the text colour so it reads on the card.
const ERROR_TEXT = 'text-[color:color-mix(in_oklab,var(--color-error)_55%,var(--color-base-content))]'

async function submit() {
  if (sending.value) return
  sending.value = true
  errors.value = {}
  formError.value = ''
  try {
    await $api<CommentSubmitResponse>('/api/v2/comments/', {
      method: 'POST',
      body: {
        post: props.postId,
        parent: props.parent?.id,
        name: name.value,
        email: email.value,
        body: body.value,
        notify_replies: notify.value,
        website: website.value,
        form_token: props.formToken,
      },
    })
    notified.value = notify.value
    done.value = true
  } catch (e) {
    const data = (e as { data?: Partial<CommentSubmitResponse> }).data
    if (data?.status === 'invalid') {
      const problems = data.errors ?? {}
      errors.value = { name: problems.name, email: problems.email, body: problems.body }
      const first = (['name', 'email', 'body'] as const).find(field => problems[field])
      if (problems.parent) formError.value = problems.parent
      else if (!first) formError.value = 'Please check your name, email and comment, then try again.'
      await nextTick()
      if (first) fields[first].value?.focus()
    } else {
      formError.value = MESSAGES[data?.status ?? ''] ?? GENERIC_ERROR
    }
  } finally {
    sending.value = false
  }
}

/** Puts the cursor in the comment box; a form that was already used starts again, empty. */
function show() {
  if (done.value) {
    done.value = false
    body.value = ''
    notify.value = false
  }
  nextTick(() => fields.body.value?.focus())
}
defineExpose({ show })

onMounted(() => {
  if (props.inline) fields.body.value?.focus()
})

function describedBy(field: Field) {
  const ids = []
  if (field === 'email') ids.push(`${uid}-email-hint`)
  if (errors.value[field]) ids.push(`${uid}-${field}-error`)
  return ids.length ? ids.join(' ') : undefined
}
</script>

<template>
<CommentThanks v-if="done" :notify="notified" />
<form
    v-else
    method="post"
    action="/api/v2/comments/"
    class="rounded-box bg-base-200 shadow-md p-6 md:p-8"
    @submit.prevent="submit"
    @keydown.esc="inline && emit('cancel')"
>
    <h3 class="text-xl md:text-2xl font-bold mb-6">
        <template v-if="!parent">Leave a comment</template>
        <template v-else-if="inline">Reply to {{ parent.name }}</template>
        <template v-else>Replying to {{ parent.name }} · <NuxtLink :to="cancelTo || ''" class="font-normal text-base text-base-content/70 underline hover:text-base-content transition-colors">Cancel</NuxtLink></template>
    </h3>

    <p v-if="formError" class="mb-6 rounded-box border border-error bg-base-100 px-4 py-3 text-sm text-base-content" role="alert">{{ formError }}</p>

    <input type="hidden" name="post" :value="postId">
    <input v-if="parent" type="hidden" name="parent" :value="parent.id">
    <input type="hidden" name="form_token" :value="formToken">

    <div class="grid gap-5 md:grid-cols-2">
        <div>
            <label :for="`${uid}-name`" class="block text-sm font-medium mb-2">Name</label>
            <input
                :id="`${uid}-name`"
                ref="nameEl"
                v-model="name"
                type="text"
                name="name"
                class="input block w-full"
                :class="{ 'border-error': errors.name }"
                autocomplete="name"
                maxlength="80"
                required
                :aria-invalid="errors.name ? 'true' : undefined"
                :aria-describedby="describedBy('name')"
            >
            <p v-if="errors.name" :id="`${uid}-name-error`" class="text-sm mt-2" :class="ERROR_TEXT">{{ errors.name }}</p>
        </div>
        <div>
            <label :for="`${uid}-email`" class="block text-sm font-medium mb-2">Email</label>
            <input
                :id="`${uid}-email`"
                ref="emailEl"
                v-model="email"
                type="email"
                name="email"
                class="input block w-full"
                :class="{ 'border-error': errors.email }"
                autocomplete="email"
                maxlength="254"
                required
                :aria-invalid="errors.email ? 'true' : undefined"
                :aria-describedby="describedBy('email')"
            >
            <p :id="`${uid}-email-hint`" class="text-xs text-base-content/60 mt-2">Never shown.</p>
            <p v-if="errors.email" :id="`${uid}-email-error`" class="text-sm mt-2" :class="ERROR_TEXT">{{ errors.email }}</p>
        </div>
    </div>

    <div class="mt-5">
        <label :for="`${uid}-body`" class="block text-sm font-medium mb-2">Comment</label>
        <textarea
            :id="`${uid}-body`"
            ref="bodyEl"
            v-model="body"
            name="body"
            rows="5"
            class="textarea block w-full"
            :class="{ 'border-error': errors.body }"
            maxlength="5000"
            required
            :aria-invalid="errors.body ? 'true' : undefined"
            :aria-describedby="describedBy('body')"
        ></textarea>
        <p v-if="errors.body" :id="`${uid}-body-error`" class="text-sm mt-2" :class="ERROR_TEXT">{{ errors.body }}</p>
    </div>

    <label class="mt-5 flex w-fit cursor-pointer items-center gap-3 text-sm">
        <input v-model="notify" type="checkbox" name="notify_replies" class="checkbox">
        Email me when someone replies
    </label>

    <div class="hidden" aria-hidden="true"><input v-model="website" type="text" name="website" tabindex="-1" autocomplete="off"></div>

    <div class="mt-6 flex flex-wrap items-center gap-3">
        <button type="submit" class="btn btn-primary" :disabled="sending">{{ parent ? 'Post reply' : 'Post comment' }}</button>
        <button v-if="inline" type="button" class="btn btn-outline" @click="emit('cancel')">Cancel</button>
    </div>

    <p class="mt-4 text-xs text-base-content/60">
        Comments are reviewed before they appear. Your email address is never shown.<template v-if="akismet"> Spam is filtered by Akismet. <a href="https://akismet.com/privacy/" rel="noopener" class="underline hover:text-base-content transition-colors">How your data is handled</a>.</template>
    </p>
</form>
</template>
