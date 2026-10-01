<script setup lang="ts">
import type { HeroBlock } from '~/types/api'

// Old core/blocks/hero_block.html. height "large" has no min-height (the old min-h-screen-75
// was never a real class). The background image is shown (deliberate fix: the old CSS targeted
// a .hero class the section didn't have).
const props = defineProps<{ block: HeroBlock }>()

const background = computed(() => rendition(props.block.value.background_image, 'original'))
</script>

<template>
<section
    class="relative my-12 flex items-center"
    :class="{
        'min-h-72': block.value.height === 'small',
        'min-h-96': block.value.height === 'medium',
        'min-h-screen': block.value.height === 'full',
        'bg-base-100': !block.value.background_image,
    }"
    :style="background ? {
        backgroundImage: `url('${background.url}')`,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundRepeat: 'no-repeat',
    } : undefined"
>
    <div v-if="block.value.background_image" class="absolute inset-0" :class="block.value.background_overlay ? 'bg-base-100/40' : 'bg-base-100/0'"></div>
    
    <div class="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-12 w-full">
        <div class="max-w-2xl text-base-content">
            <h1 class="text-3xl md:text-5xl font-bold leading-tight mb-6">
                {{ block.value.title }}
            </h1>
            
            <p v-if="block.value.subtitle" class="text-lg md:text-xl leading-relaxed mb-8 opacity-90">
                {{ block.value.subtitle }}
            </p>
            
            <NuxtLink v-if="block.value.cta_text && block.value.cta_link" :to="block.value.cta_link" no-rel class="inline-block px-6 py-3 border border-base-content hover:bg-base-content hover:text-base-100 transition-colors font-medium">
                {{ block.value.cta_text }}
            </NuxtLink>
        </div>
    </div>
</section>
</template>
