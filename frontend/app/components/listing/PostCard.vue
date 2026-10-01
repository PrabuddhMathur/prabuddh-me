<script setup lang="ts">
import type { PostSummary } from '~/types/api'

// Old blog/includes/post_card.html (masonry view).
const props = defineProps<{ post: PostSummary }>()
const img = computed(() => rendition(props.post.featured_image, 'card'))
</script>

<template>
<NuxtLink :to="post.url" no-rel class="block bg-base-100 hover:bg-base-200 rounded-xl border-2 border-base-content/10 overflow-hidden shadow-lg hover:shadow-2xl transition-all duration-300 group">

    <!-- Image section -->
    <div v-if="post.featured_image" class="relative">
        <div v-if="post.featured" class="absolute top-4 left-4 z-10 px-3 py-1 bg-primary text-primary-content rounded-lg shadow-lg text-sm font-bold flex items-center gap-1">
            <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"/></svg>
            Featured
        </div>
        <img :src="img?.url" :alt="post.featured_image.title" class="w-full h-56 object-cover group-hover:scale-105 transition-transform duration-500">
    </div>

    <!-- Content section -->
    <div class="p-6 space-y-4">
        <!-- Title -->
        <h2 class="text-xl md:text-2xl font-bold text-base-content group-hover:text-primary transition-colors line-clamp-2">
            {{ post.title }}
        </h2>

        <!-- Meta info -->
        <div class="flex items-center gap-2 text-sm text-base-content/60">
            <time :datetime="formatDate(post.date, 'Y-m-d')">{{ formatDate(post.date, 'M d, Y') }}</time>
            <template v-if="post.estimated_reading_time">
            <span>•</span>
            <span>{{ post.estimated_reading_time }} min read</span>
            </template>
        </div>

        <!-- Excerpt -->
        <p v-if="post.intro" class="text-base text-base-content/70 line-clamp-3 leading-relaxed">
            {{ post.intro }}
        </p>

        <!-- Tags -->
        <div v-if="post.tags.length" class="flex flex-wrap gap-2">
            <span v-for="tag in post.tags.slice(0, 3)" :key="tag.slug" class="px-2 py-1 text-xs bg-base-200 text-base-content rounded-md">#{{ tag.name }}</span>
        </div>
    </div>
</NuxtLink>
</template>
