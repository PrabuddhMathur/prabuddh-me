<script setup lang="ts">
// What replaces the comment form once a comment is in (with JavaScript, or after the redirect
// back from a form posted without it). `notify`: the reply-alerts box was ticked.
defineProps<{ notify?: boolean }>()
</script>

<template>
<div class="rounded-box bg-base-200 shadow-md p-6 md:p-8" role="status">
    <p class="text-base-content/80 leading-relaxed">Thanks! Your comment is waiting for review and will appear once it's approved.<template v-if="notify"> If it's approved, you'll get an email to turn on reply notifications.</template></p>
</div>
</template>
