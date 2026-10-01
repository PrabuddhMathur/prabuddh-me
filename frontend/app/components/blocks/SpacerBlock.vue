<script setup lang="ts">
import type { SpacerBlock } from '~/types/api'

// Old core/blocks/spacer_block.html.
defineProps<{ block: SpacerBlock }>()
</script>

<template>
<div
    :class="{
        'h-4': block.value.height === 'small',
        'h-8': block.value.height === 'medium',
        'h-16': block.value.height === 'large',
        'h-24': block.value.height === 'xlarge',
    }"
></div>
</template>
