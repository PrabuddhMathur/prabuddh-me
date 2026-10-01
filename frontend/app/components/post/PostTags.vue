<script setup lang="ts">
import type { Tag } from '~/types/api'

// Old core/components/post-tags.html: at most `maxTags` tag links (3 by default, even on the
// post page, as before). Clicks don't reach a surrounding clickable card.
const props = withDefaults(defineProps<{
  tags: Tag[]
  maxTags?: number
  /** Leaves out the bottom margin (mb-3). */
  showInline?: boolean
  /** Adds the "Tags:" label. */
  showLabel?: boolean
  /** Extra classes, appended like the old `classes` parameter. */
  classes?: string
}>(), {
  maxTags: 3,
  showInline: false,
  showLabel: false,
  classes: '',
})

const shown = computed(() => props.tags.slice(0, props.maxTags))
</script>

<template>
  <div v-if="tags.length" class="flex flex-wrap gap-1.5 sm:gap-2 items-center" :class="[{ 'mb-3': !showInline }, classes]">
    <span v-if="showLabel" class="text-xs sm:text-sm text-base-content/60 font-medium">Tags:</span>

    <NuxtLink
      v-for="tag in shown"
      :key="tag.slug"
      :to="tagUrl(tag.slug)"
      class="inline-flex items-center gap-1.5 text-xs px-2 py-0.5 sm:py-1 border border-base-content/10 hover:border-base-content transition-colors rounded-md relative z-10"
      :aria-label="`View posts tagged with ${tag.name}`"
      @click.stop
    >
      <span>#</span>
      <span>{{ tag.name }}</span>
    </NuxtLink>
  </div>
</template>
