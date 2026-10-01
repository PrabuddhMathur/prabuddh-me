<script setup lang="ts">
import type { PostSummary } from '~/types/api'

// Old blog/includes/post_list_item.html (list view).
const props = defineProps<{ post: PostSummary }>()
const img = computed(() => rendition(props.post.featured_image, 'list'))
</script>

<template>
<NuxtLink :to="post.url" no-rel class="flex flex-col md:flex-row bg-base-100 hover:bg-base-200 rounded-xl border-2 border-base-content/10 overflow-hidden shadow-lg hover:shadow-2xl transition-all duration-300 group">

    <!-- Image -->
    <div v-if="post.featured_image" class="md:w-64 flex-shrink-0">
        <img :src="img?.url" :alt="post.featured_image.title" class="w-full h-48 md:h-full object-cover group-hover:scale-105 transition-transform duration-500">
    </div>

    <!-- Content -->
    <div class="p-6 flex-1 space-y-3">
        <div v-if="post.featured" class="inline-flex items-center gap-1 px-2 py-1 bg-primary text-primary-content rounded text-xs font-bold">
            ⭐ Featured
        </div>

        <h3 class="text-lg md:text-xl font-bold text-base-content group-hover:text-primary transition-colors line-clamp-2">
            {{ post.title }}
        </h3>

        <div class="flex items-center gap-2 text-sm text-base-content/60">
            <time :datetime="formatDate(post.date, 'Y-m-d')">{{ formatDate(post.date, 'M d, Y') }}</time>
            <template v-if="post.estimated_reading_time">
            <span>•</span>
            <span>{{ post.estimated_reading_time }} min read</span>
            </template>
        </div>

        <p v-if="post.intro" class="text-sm text-base-content/70 line-clamp-2">
            {{ post.intro }}
        </p>
    </div>
</NuxtLink>
</template>
