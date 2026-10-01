<script setup lang="ts">
import type { CtaBlock } from '~/types/api'

// Old core/blocks/cta_block.html.
const props = defineProps<{ block: CtaBlock }>()

const external = computed(() => props.block.value.button_link.slice(0, 4) === 'http')
</script>

<template>
<section
    class="py-12 my-8 rounded-lg"
    :class="[
        {
            'bg-transparent': block.value.background_color === 'transparent',
            'bg-base-100': block.value.background_color === 'base-100',
            'bg-base-200': block.value.background_color === 'base-200',
            'bg-primary text-primary-content': block.value.background_color === 'primary',
            'bg-secondary text-secondary-content': block.value.background_color === 'secondary',
            'bg-accent text-accent-content': block.value.background_color === 'accent',
        },
        { 'shadow-lg': block.value.background_color !== 'transparent' },
    ]"
>
    <div class="max-w-7xl mx-auto px-6 lg:px-12 text-center">
        <div
            class="max-w-2xl mx-auto"
            :class="{
                'text-left': block.value.text_alignment === 'left',
                'text-center': block.value.text_alignment === 'center',
                'text-right': block.value.text_alignment === 'right',
            }"
        >
            <h2 class="text-3xl md:text-4xl font-bold mb-4 leading-tight">
                {{ block.value.title }}
            </h2>
            
            <p v-if="block.value.description" class="text-lg md:text-xl mb-8 leading-relaxed opacity-90">
                {{ block.value.description }}
            </p>
            
            <div
                :class="{
                    'text-left': block.value.text_alignment === 'left',
                    'text-center': block.value.text_alignment === 'center',
                    'text-right': block.value.text_alignment === 'right',
                }"
            >
                <NuxtLink
                    :to="block.value.button_link"
                    class="inline-block px-6 py-3 border border-base-content hover:bg-base-content hover:text-base-100 transition-colors font-medium"
                    :target="external ? '_blank' : undefined"
                    :rel="external ? 'noopener noreferrer' : undefined"
                    :no-rel="external ? undefined : true"
                >
                    {{ block.value.button_text }}
                </NuxtLink>
            </div>
        </div>
    </div>
</section>
</template>
