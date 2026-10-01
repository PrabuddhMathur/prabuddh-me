<script setup lang="ts">
import type { Component } from 'vue'
import type { StreamBlock } from '~/types/api'
import AuthorBioBlock from './AuthorBioBlock.vue'
import ButtonBlock from './ButtonBlock.vue'
import CtaBlock from './CtaBlock.vue'
import HeadingBlock from './HeadingBlock.vue'
import HeroBlock from './HeroBlock.vue'
import ImageBlock from './ImageBlock.vue'
import QuoteBlock from './QuoteBlock.vue'
import RecentPostsBlock from './RecentPostsBlock.vue'
import SpacerBlock from './SpacerBlock.vue'
import TextBlock from './TextBlock.vue'

// A StreamField body: each block rendered by its template. With `wrap`, each block sits in
// <div class="block-{type}">, which is how Wagtail renders `{{ page.body }}` (the home page);
// without it the blocks are rendered one after another (`{% include_block block %}`), with the
// whitespace that the old template left between them (it is what spaces adjacent buttons apart).
const props = withDefaults(defineProps<{
  blocks: StreamBlock[]
  wrap?: boolean
}>(), {
  wrap: false,
})

const components: Record<string, Component> = {
  heading: HeadingBlock,
  text: TextBlock,
  image: ImageBlock,
  quote: QuoteBlock,
  button: ButtonBlock,
  spacer: SpacerBlock,
  hero: HeroBlock,
  cta: CtaBlock,
  author_bio: AuthorBioBlock,
  recent_posts: RecentPostsBlock,
}

// Unknown block types render nothing.
const known = computed(() => props.blocks.filter((block) => {
  if (components[block.type]) return true
  if (import.meta.dev) console.warn(`StreamField: unknown block type "${block.type}"`)
  return false
}))
</script>

<template>
<template v-for="block in known" :key="block.id">
<div v-if="wrap" :class="`block-${block.type}`"><component :is="components[block.type]" :block="block" /></div>
<template v-else><component :is="components[block.type]" :block="block" />{{ ' ' }}</template>
</template>
</template>
