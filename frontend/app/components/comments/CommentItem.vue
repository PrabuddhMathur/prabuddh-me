<script setup lang="ts">
import type { CommentData, CommentReply } from '~/types/api'

// One comment: who, when, what, the owner's heart and a Reply control. Replies are the same
// component, indented by CommentSection. The text is plain: web addresses are linked by
// linkifyComment, and everything is rendered as text (never v-html).
const props = defineProps<{ comment: CommentData | CommentReply }>()

const ctx = inject(commentsKey, null)

const parts = computed(() => linkifyComment(props.comment.body))
const replyTo = computed(() => ('reply_to' in props.comment ? props.comment.reply_to : null))
const replying = computed(() => ctx?.replyingTo.value === props.comment.id)

const replyLink = useTemplateRef<HTMLAnchorElement>('replyLinkEl')
const form = useTemplateRef<{ show: () => void }>('replyFormEl')

// Without JavaScript the link goes to ?replyto=<id>, a page whose bottom form answers this
// comment. With it, the form opens right here.
function onReply(event: MouseEvent) {
  if (!ctx || event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return
  event.preventDefault()
  if (replying.value) form.value?.show()
  else ctx.openReply(props.comment.id)
}

function cancelReply() {
  ctx?.closeReply()
  nextTick(() => replyLink.value?.focus())
}
</script>

<template>
<article :id="`comment-${comment.id}`" class="scroll-mt-24">
    <header class="flex flex-wrap items-center gap-x-3 gap-y-1">
        <span class="font-semibold text-base-content break-words min-w-0">{{ comment.name }}</span>
        <span v-if="comment.is_author" class="inline-flex h-5 items-center justify-center rounded-selector border border-primary bg-primary px-2 text-xs text-primary-content">Author</span>
        <time :datetime="comment.created_at" class="text-sm text-base-content/60">{{ formatDate(comment.created_at, 'F j, Y') }}</time>
    </header>

    <p v-if="replyTo" class="mt-1 text-sm text-base-content/60">
        <a :href="`#comment-${replyTo.id}`" class="hover:text-base-content transition-colors">Replying to {{ replyTo.name }}</a>
    </p>

    <p class="mt-3 text-base-content/80 leading-relaxed whitespace-pre-line break-words"><template v-for="(part, index) in parts" :key="index"><a v-if="part.href" :href="part.href" rel="nofollow ugc noopener" class="underline hover:text-base-content transition-colors">{{ part.text }}</a><template v-else>{{ part.text }}</template></template></p>

    <div v-if="comment.liked || ctx?.open" class="mt-3 flex flex-wrap items-center gap-x-5 gap-y-2 text-sm">
        <span v-if="comment.liked" class="inline-flex items-center gap-1.5 text-base-content/60">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-error" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path d="M11.645 20.91l-.007-.003-.022-.012a15.247 15.247 0 01-.383-.218 25.18 25.18 0 01-4.244-3.17C4.688 15.36 2.25 12.174 2.25 8.25 2.25 5.322 4.714 3 7.688 3A5.5 5.5 0 0112 5.052 5.5 5.5 0 0116.313 3c2.973 0 5.437 2.322 5.437 5.25 0 3.925-2.438 7.111-4.739 9.256a25.175 25.175 0 01-4.244 3.17 15.247 15.247 0 01-.383.219l-.022.012-.007.004-.003.001a.752.752 0 01-.704 0l-.003-.001z" />
            </svg>
            {{ ctx?.likeLabel }}
        </span>
        <a
            v-if="ctx?.open"
            ref="replyLinkEl"
            :href="`?replyto=${comment.id}#comment-form`"
            class="inline-flex items-center gap-1.5 font-medium text-base-content/60 hover:text-base-content transition-colors"
            :aria-label="`Reply to ${comment.name}`"
            @click="onReply"
        >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" />
            </svg>
            Reply
        </a>
    </div>

    <div v-if="ctx && replying" class="mt-5">
        <CommentForm
            ref="replyFormEl"
            :post-id="ctx.postId"
            :form-token="ctx.formToken"
            :akismet="ctx.akismet"
            :parent="{ id: comment.id, name: comment.name }"
            inline
            @cancel="cancelReply"
        />
    </div>
</article>
</template>
