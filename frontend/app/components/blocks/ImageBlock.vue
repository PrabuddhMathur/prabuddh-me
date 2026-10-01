<script setup lang="ts">
import type { ImageBlock } from '~/types/api'

// Old core/blocks/image_block.html. On a blog post the button opens the gallery (the post
// provides galleryKey); anywhere else it does nothing, as before.
const props = defineProps<{ block: ImageBlock }>()

const gallery = inject(galleryKey, null)

const img = computed(() => rendition(props.block.value.image, 'display'))
const full = computed(() => rendition(props.block.value.image, 'full'))
const alt = computed(() => props.block.value.alt_text || props.block.value.caption || 'Image')
</script>

<template>
<figure
    class="mx-auto text-center"
    :class="block.value.alignment === 'full' ? 'w-full' : 'max-w-4xl'"
>
    <button
        class="block cursor-pointer group relative w-full bg-transparent border-0 p-0 blog-gallery-image"
        :data-full-url="full?.url"
        :data-caption="block.value.caption"
        :data-alt="alt"
        aria-label="View full size image"
        @click="gallery?.open(block.id)">
        <img
            :src="img?.url"
            :alt="alt"
            :class="block.value.alignment === 'full' ? 'w-full' : 'max-w-full h-auto mx-auto'"
            class="rounded-lg"
            :width="img?.width"
            :height="img?.height"
        />
    </button>
    
    <figcaption v-if="block.value.caption" class="mt-2 text-sm text-base-content/60">
        {{ block.value.caption }}
    </figcaption>
</figure>
</template>
