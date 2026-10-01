<script setup lang="ts">
import type { HeadingBlock } from '~/types/api'

// Old core/blocks/heading_block.html.
defineProps<{ block: HeadingBlock }>()
</script>

<template>
<component
    :is="block.value.heading_level"
    :class="{
        'text-left': block.value.alignment === 'left',
        'text-center': block.value.alignment === 'center',
        'text-right': block.value.alignment === 'right',
    }"
>
    {{ block.value.heading_text }}
</component>
</template>
