<script setup lang="ts">
// Old core/components/post-meta.html: the post date ("Jan 5, 2025") and reading time.
withDefaults(defineProps<{
  /** The post's date, YYYY-MM-DD. */
  date: string
  /** Minutes; the "• N min read" part is left out when 0. */
  readingTime?: number
  showIcons?: boolean
  /** Extra classes, appended like the old `classes` parameter. */
  classes?: string
}>(), {
  readingTime: 0,
  showIcons: false,
  classes: '',
})
</script>

<template>
  <div class="flex flex-wrap gap-2 items-center text-sm text-base-content/60" :class="classes">
    <svg v-if="showIcons" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
    </svg>
    <time class="font-medium" :datetime="formatDate(date, 'Y-m-d')">{{ formatDate(date, 'M j, Y') }}</time>

    <template v-if="readingTime">
      <span>•</span>
      <svg v-if="showIcons" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <span class="font-medium">{{ readingTime }} min read</span>
    </template>
  </div>
</template>
