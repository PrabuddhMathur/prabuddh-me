<script setup lang="ts">
import type { CommentsResponse } from '~/types/api'

// The comments under a blog post: the threads, then the form. Not in the old site. Rendered on
// the server like the post, so the comments are in the HTML. Nothing shows when the comments
// can't be loaded or are switched off. A form posted without JavaScript lands back here with
// ?comment=<status>, and "Reply" without JavaScript with ?replyto=<comment id>.
const props = defineProps<{ postId: number }>()

const route = useRoute()
const { data } = await useApi<CommentsResponse>('/api/v2/comments/', { query: { post: props.postId } })

const threads = computed(() => data.value?.comments ?? [])
const count = computed(() => data.value?.count ?? 0)
const open = computed(() => !!data.value?.open)
// Switched off, or closed with nothing said: no section at all.
const visible = computed(() => !!data.value?.enabled && (open.value || count.value > 0))

// An inline reply form (one at a time) under the comment with this id.
const replyingTo = ref<number | null>(null)
provide(commentsKey, {
  get postId() { return props.postId },
  get formToken() { return data.value?.form_token ?? '' },
  get akismet() { return !!data.value?.akismet },
  get likeLabel() { return data.value?.like_label ?? '' },
  get open() { return open.value },
  replyingTo,
  openReply: (id: number) => { replyingTo.value = id },
  closeReply: () => { replyingTo.value = null },
})

function query(name: string) {
  const value = route.query[name]
  return typeof value === 'string' ? value : ''
}

// The outcome of a form posted without JavaScript.
const NOTICES: Record<string, string> = {
  invalid: 'Please check your name, email and comment, then try again.',
  rate_limited: 'Too many comments from your connection. Please try again later.',
  closed: 'Comments are closed on this post.',
}
const posted = computed(() => query('comment'))
const notice = computed(() => (posted.value && posted.value !== 'pending'
  ? NOTICES[posted.value] ?? 'Something went wrong. Please try again later.'
  : ''))

// ?replyto=<id>: the bottom form answers that comment, when it is on the page.
const replyTarget = computed(() => {
  const id = Number(query('replyto'))
  if (!id) return null
  for (const thread of threads.value) {
    for (const comment of [thread, ...thread.replies]) {
      if (comment.id === id) return { id: comment.id, name: comment.name }
    }
  }
  return null
})
</script>

<template>
<section v-if="visible" id="comments" class="mt-12 pt-12 border-t border-base-content/10 scroll-mt-24" aria-labelledby="comments-heading">
    <h2 id="comments-heading" class="text-2xl md:text-3xl font-bold mb-8">{{ count > 0 ? `${count} Comment${pluralize(count)}` : 'Comments' }}</h2>

    <p v-if="!threads.length" class="text-base-content/60">No comments yet. Start the conversation.</p>

    <ol v-else class="space-y-10">
        <li v-for="thread in threads" :key="thread.id">
            <CommentItem :comment="thread" />
            <ol v-if="thread.replies.length" class="mt-6 ml-4 md:ml-12 pl-4 md:pl-6 border-l-2 border-base-content/10 space-y-6">
                <li v-for="reply in thread.replies" :key="reply.id">
                    <CommentItem :comment="reply" />
                </li>
            </ol>
        </li>
    </ol>

    <div id="comment-form" class="mt-12 scroll-mt-24">
        <p v-if="!open" class="rounded-box bg-base-200 p-6 text-base-content/70">Comments are closed.</p>
        <CommentThanks v-else-if="posted === 'pending'" />
        <CommentForm
            v-else
            :key="replyTarget?.id ?? 'new'"
            :post-id="postId"
            :form-token="data?.form_token ?? ''"
            :akismet="!!data?.akismet"
            :parent="replyTarget"
            :cancel-to="`${route.path}#comments`"
            :notice="notice"
        />
    </div>
</section>
</template>
