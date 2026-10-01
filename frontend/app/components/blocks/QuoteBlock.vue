<script setup lang="ts">
import type { QuoteBlock } from '~/types/api'

// Old core/blocks/quote_block.html. font-serif is Tailwind's default serif stack, as before.
defineProps<{ block: QuoteBlock }>()
</script>

<template>
<blockquote
    class="my-8"
    :class="{
        'border-l-4 border-base-content pl-6 py-4': block.value.style === 'default',
        'text-center py-8 px-6': block.value.style === 'large',
        'border-2 border-base-200 p-6': block.value.style === 'bordered',
        'bg-base-200 border-l-4 border-base-content p-6': block.value.style === 'accent',
    }"
>
    <template v-if="block.value.style === 'large'">
        <svg class="w-8 h-8 mx-auto mb-4 text-base-content/30" fill="currentColor" viewBox="0 0 24 24">
            <path d="M14.017 21v-7.391c0-5.704 3.731-9.57 8.983-10.609l.995 2.151c-2.432.917-3.995 3.638-3.995 5.849h4v10h-9.983zm-14.017 0v-7.391c0-5.704 3.748-9.57 9-10.609l.996 2.151c-2.433.917-3.996 3.638-3.996 5.849h4v10h-10z"/>
        </svg>
        
        <p class="text-2xl md:text-3xl font-serif leading-relaxed text-base-content mb-6">
            "{{ block.value.quote }}"
        </p>
    </template>
    <template v-else>
        <p class="text-lg md:text-xl font-serif leading-relaxed text-base-content mb-4">
            "{{ block.value.quote }}"
        </p>
    </template>
    
    <footer v-if="block.value.author" :class="block.value.style === 'large' ? 'text-center' : 'text-right'">
        <cite class="text-base-content/70 font-medium not-italic">
            — {{ block.value.author }}<template v-if="block.value.author_title">, {{ block.value.author_title }}</template>
        </cite>
    </footer>
</blockquote>
</template>
