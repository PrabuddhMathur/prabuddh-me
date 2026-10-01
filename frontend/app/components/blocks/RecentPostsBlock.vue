<script setup lang="ts">
import type { PostSummary, RecentPostsBlock } from '~/types/api'

// Old core/blocks/recent_posts_block.html. The posts come with the block (no extra fetch).
// Dates use first_published_at ("Jan 10, 2025"). The old `post.author` never existed: dropped.
const props = defineProps<{ block: RecentPostsBlock }>()

const value = computed(() => props.block.value)

// Django's date:'c' for a UTC datetime.
function isoDate(post: PostSummary): string {
  return (post.first_published_at ?? '').replace(/Z$/, '+00:00')
}
</script>

<template>
<section class="my-12">
    <div class="flex items-center mb-8">
        <h2 class="text-3xl font-bold text-base-content">{{ value.title }}</h2>
        <div class="flex-1 h-px bg-base-300 ml-4"></div>
    </div>
    
    <div
        :class="{
            'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6': value.layout_style === 'grid',
            'grid grid-cols-1 md:grid-cols-2 gap-6': value.layout_style === 'cards',
            'space-y-4': value.layout_style === 'list',
        }"
    >
        <template v-for="post in value.posts" :key="post.id">
            <article v-if="value.layout_style === 'list'" class="relative flex flex-row items-stretch rounded-box bg-base-100 shadow-md hover:shadow-lg transition-shadow duration-300">
                <figure v-if="value.show_featured_image && post.featured_image" class="flex items-center justify-center overflow-hidden rounded-s-[inherit] w-32 flex-shrink-0">
                    <img :src="rendition(post.featured_image, 'thumb')?.url" :alt="post.featured_image.title" :width="rendition(post.featured_image, 'thumb')?.width" :height="rendition(post.featured_image, 'thumb')?.height" class="w-full h-full object-cover" />
                </figure>
                
                <div class="flex flex-auto flex-col gap-2 p-4 text-[0.875rem]">
                    <h3 class="flex items-center gap-2 font-semibold text-lg">
                        <NuxtLink :to="post.url" class="cursor-pointer no-underline hover:underline focus:outline-none focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-current">{{ post.title }}</NuxtLink>
                    </h3>
                    
                    <p v-if="value.show_excerpt && post.intro" class="grow text-sm text-base-content/70">{{ truncateWords(post.intro, 15) }}</p>
                    
                    <div class="flex flex-wrap items-center justify-between gap-2">
                        <div class="text-xs text-base-content/60 space-x-2">
                            <time v-if="value.show_date && post.first_published_at" :datetime="isoDate(post)">
                                {{ formatDate(post.first_published_at, 'M d, Y') }}
                            </time>
                        </div>
                        
                        <NuxtLink :to="post.url" class="btn btn-outline btn-xs">Read</NuxtLink>
                    </div>
                </div>
            </article>
            
            <article v-else class="relative flex flex-col rounded-box bg-base-100 shadow-xl hover:shadow-2xl transition-shadow duration-300">
                <figure v-if="value.show_featured_image && post.featured_image" class="flex items-center justify-center overflow-hidden rounded-t-[inherit] h-48">
                    <img
                        v-if="value.layout_style === 'grid'"
                        :src="rendition(post.featured_image, 'grid')?.url"
                        :alt="post.featured_image.title"
                        :width="rendition(post.featured_image, 'grid')?.width"
                        :height="rendition(post.featured_image, 'grid')?.height"
                        class="w-full h-full object-cover" />
                    <img
                        v-else
                        :src="rendition(post.featured_image, 'cards')?.url"
                        :alt="post.featured_image.title"
                        :width="rendition(post.featured_image, 'cards')?.width"
                        :height="rendition(post.featured_image, 'cards')?.height"
                        class="w-full h-full object-cover" />
                </figure>
                
                <div class="flex flex-auto flex-col gap-2 p-6 text-[0.875rem]">
                    <h3 class="flex items-center gap-2 text-[1.125rem] font-semibold">
                        <NuxtLink :to="post.url" class="cursor-pointer no-underline hover:underline focus:outline-none focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-current">{{ post.title }}</NuxtLink>
                    </h3>
                    
                    <p v-if="value.show_excerpt && post.intro" class="grow text-base-content/70">{{ truncateWords(post.intro, 20) }}</p>
                    
                    <div class="flex flex-wrap items-center justify-between gap-2 mt-4">
                        <div class="text-sm text-base-content/60 space-x-2">
                            <time v-if="value.show_date && post.first_published_at" :datetime="isoDate(post)">
                                {{ formatDate(post.first_published_at, 'M d, Y') }}
                            </time>
                        </div>
                        
                        <NuxtLink :to="post.url" class="btn btn-primary btn-sm">Read More</NuxtLink>
                    </div>
                </div>
            </article>
        </template>
        <div v-if="!value.posts.length" class="text-center py-12 col-span-full">
            <div class="text-base-content/50 text-lg">
                <svg class="w-16 h-16 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                </svg>
                <p>No blog posts available yet.</p>
                <p class="text-sm mt-2">Check back soon for new content!</p>
            </div>
        </div>
    </div>
</section>
</template>
