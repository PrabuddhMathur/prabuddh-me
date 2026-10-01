<script setup lang="ts">
import type { TextBlock } from '~/types/api'

// Old core/blocks/rich_text_block.html.
defineProps<{ block: TextBlock }>()
</script>

<template>
<RichText
    :html="block.value.text"
    class="prose max-w-none"
    :class="{
        'text-left': block.value.alignment === 'left',
        'text-center': block.value.alignment === 'center',
        'text-right': block.value.alignment === 'right',
        'text-justify': block.value.alignment === 'justify',
    }"
/>
</template>
