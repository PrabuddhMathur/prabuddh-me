<script setup lang="ts">
import type { ButtonBlock } from '~/types/api'

// Old core/blocks/button_block.html. The size classes are copied as they were: px-6 py-3 are
// always in the list, so the later utility wins exactly as it did in the old stylesheet.
defineProps<{ block: ButtonBlock }>()
</script>

<template>
<NuxtLink
    :to="block.value.button_url"
    class="inline-block px-6 py-3 border border-base-content hover:bg-base-content hover:text-base-100 transition-colors font-medium"
    :class="{
        'text-xs px-3 py-1.5': block.value.button_size === 'xs',
        'text-sm px-4 py-2': block.value.button_size === 'sm',
        'text-lg px-8 py-4': block.value.button_size === 'lg',
    }"
    :target="block.value.open_in_new_tab ? '_blank' : undefined"
    :rel="block.value.open_in_new_tab ? 'noopener noreferrer' : undefined"
    :no-rel="block.value.open_in_new_tab ? undefined : true"
>
    {{ block.value.button_text }}
</NuxtLink>
</template>
