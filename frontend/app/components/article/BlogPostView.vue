<script setup lang="ts">
import type { BlogPageData } from '~/types/api'

// Old blog/blog_page.html: breadcrumbs, article header, StreamField body, tags, previous/next
// links and the image gallery.
const props = defineProps<{ page: BlogPageData }>()

const { data: site } = await useSiteSettings()

const featuredImage = computed(() => rendition(props.page.featured_image, 'display'))

// Deliberate fix (b): the post's line height really applies to the body paragraphs. "default"
// adds nothing (the rich text's own 1.75). Static class names, so Tailwind generates them.
const LINE_HEIGHT_CLASSES = {
  default: '',
  normal: 'prose-p:leading-normal',
  comfortable: 'prose-p:leading-[1.55]',
  relaxed: 'prose-p:leading-relaxed',
  spacious: 'prose-p:leading-[1.8]',
  loose: 'prose-p:leading-loose',
}
const lineHeightClass = computed(() => LINE_HEIGHT_CLASSES[props.page.line_height] ?? '')

// The gallery: the featured image, then every image block of the body, in order.
const galleryEntries = computed(() => {
  const entries: { id: string | null, url: string, caption: string, alt: string }[] = []
  const featured = props.page.featured_image
  if (featured) {
    entries.push({
      id: null,
      url: featured.renditions.full?.url ?? '',
      caption: props.page.featured_image_caption,
      alt: featured.title,
    })
  }
  for (const block of props.page.body) {
    if (block.type !== 'image' || !block.value.image) continue
    entries.push({
      id: block.id,
      url: block.value.image.renditions.full?.url ?? '',
      caption: block.value.caption,
      alt: block.value.alt_text || block.value.caption || 'Image',
    })
  }
  return entries
})

const gallery = ref<{ show: (index: number) => void }>()

function openGallery(blockId: string | null) {
  const index = galleryEntries.value.findIndex(entry => entry.id === blockId)
  if (index >= 0) gallery.value?.show(index)
}
provide(galleryKey, { open: openGallery })
</script>

<template>
<nav class="max-w-7xl mx-auto px-4 md:px-6 lg:px-8 py-4" aria-label="Breadcrumb">
    <div class="max-w-4xl mx-auto">
        <ol class="flex items-center gap-2 text-sm text-base-content/60">
            <li><NuxtLink to="/" class="hover:text-base-content transition-colors">Home</NuxtLink></li>
            <li><span class="text-base-content/40">/</span></li>
            <li><NuxtLink to="/blog/" class="hover:text-base-content transition-colors">Blog</NuxtLink></li>
            <li><span class="text-base-content/40">/</span></li>
            <li class="text-base-content font-medium truncate max-w-xs">{{ page.title }}</li>
        </ol>
    </div>
</nav>

<div class="max-w-7xl mx-auto px-6 md:px-6 lg:px-8 py-8 lg:py-12">
    <article class="max-w-4xl mx-auto">
        <header class="mb-12 space-y-6">
            <h1 class="text-4xl md:text-5xl lg:text-6xl font-bold text-base-content leading-tight">
                {{ page.title }}
            </h1>
            
            <div v-if="page.featured" class="inline-flex">
                <div class="inline-flex h-7 w-fit items-center justify-center gap-2 rounded-selector border border-primary bg-primary px-[calc(0.25rem*3.5-1px)] align-middle text-[1rem] text-primary-content shadow-md">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                    </svg>
                    Featured Post
                </div>
            </div>
            
            <div class="flex flex-col md:flex-row md:flex-wrap gap-3 md:gap-4 md:items-center text-base text-base-content/70">
                <div class="flex items-center gap-2">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                    </svg>
                    <span class="font-medium">{{ site?.author.name }}</span>
                </div>
                <span class="hidden md:inline">•</span>
                <PostMeta :date="page.date" :reading-time="page.estimated_reading_time" show-icons />
            </div>

            <figure v-if="page.featured_image" class="mt-8 -mx-6 md:mx-0">
                <button @click="openGallery(null)"
                        class="block cursor-pointer group relative w-full overflow-hidden rounded-lg shadow-xl hover:shadow-2xl transition-shadow duration-300"
                        :data-full-url="rendition(page.featured_image, 'full')?.url"
                        :data-caption="page.featured_image_caption"
                        :data-alt="page.featured_image.title"
                        aria-label="View full size image">
                    <img :src="featuredImage?.url"
                         :alt="page.featured_image.title"
                         class="w-full h-auto object-cover group-hover:opacity-95 transition-opacity">
                    <div class="absolute inset-0 bg-black/0 group-hover:bg-black/10 transition-colors duration-300"></div>
                </button>
                <figcaption v-if="page.featured_image_caption" class="text-sm text-center text-base-content/60 mt-4 italic">
                    {{ page.featured_image_caption }}
                </figcaption>
            </figure>

            <div v-if="page.intro" class="text-xl text-base-content/90 leading-relaxed p-8 bg-gradient-to-r from-base-200 to-base-300 border-l-4 border-primary rounded-r-lg mt-8 shadow-md">
                {{ page.intro }}
            </div>
        </header>

        <div class="my-8 flex h-4 flex-row items-center self-stretch whitespace-nowrap before:h-0.5 before:w-full before:grow before:bg-base-content/10 before:content-[''] after:h-0.5 after:w-full after:grow after:bg-base-content/10 after:content-['']"></div>

        <div class="space-y-8">
            <div class="prose prose-lg lg:prose-xl max-w-none prose-headings:font-bold prose-h2:text-3xl prose-h2:mt-12 prose-h2:mb-6 prose-h3:text-2xl prose-h3:mt-8 prose-h3:mb-4 prose-a:text-primary prose-a:no-underline hover:prose-a:underline prose-blockquote:border-l-4 prose-blockquote:border-primary prose-blockquote:bg-base-200 prose-blockquote:py-2 prose-blockquote:px-6 prose-blockquote:rounded-r-lg prose-code:bg-base-200 prose-code:px-2 prose-code:py-1 prose-code:rounded prose-img:rounded-lg prose-img:shadow-lg" :class="lineHeightClass">
            <StreamField :blocks="page.body" />
            </div>

            <div v-if="page.tags.length" class="pt-8 border-t border-base-content/10">
                <div class="flex flex-wrap items-center gap-3">
                    <span class="text-base-content/70 font-semibold flex items-center gap-2">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                        </svg>
                        Tags:
                    </span>
                    <PostTags :tags="page.tags" show-inline />
                </div>
            </div>
        </div>

        <div v-if="page.previous_post || page.next_post" class="grid grid-cols-1 md:grid-cols-2 gap-6 py-12 mt-12 border-t border-base-content/10">
            <div>
                <NuxtLink v-if="page.previous_post" :to="page.previous_post.url"
                   class="relative flex flex-col rounded-box bg-base-200 hover:bg-base-300 shadow-md hover:shadow-xl transition-all duration-300 group h-full">
                    <div class="flex flex-auto flex-col p-6 text-[0.875rem] gap-3">
                        <span class="text-sm text-base-content/60 flex items-center gap-2">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
                            </svg>
                            Previous Post
                        </span>
                        <h4 class="flex items-center gap-2 font-semibold text-lg group-hover:text-primary transition-colors">
                            {{ page.previous_post.title }}
                        </h4>
                        <p v-if="page.previous_post.intro" class="grow text-sm text-base-content/70 line-clamp-2">{{ truncateWords(page.previous_post.intro, 15) }}</p>
                    </div>
                </NuxtLink>
            </div>
            
            <div :class="{ 'md:col-start-2': !page.previous_post }">
                <NuxtLink v-if="page.next_post" :to="page.next_post.url"
                   class="relative flex flex-col rounded-box bg-base-200 hover:bg-base-300 shadow-md hover:shadow-xl transition-all duration-300 group h-full">
                    <div class="flex flex-auto flex-col p-6 text-[0.875rem] gap-3 text-right">
                        <span class="text-sm text-base-content/60 flex items-center justify-end gap-2">
                            Next Post
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                            </svg>
                        </span>
                        <h4 class="flex items-center gap-2 font-semibold text-lg group-hover:text-primary transition-colors justify-end">
                            {{ page.next_post.title }}
                        </h4>
                        <p v-if="page.next_post.intro" class="grow text-sm text-base-content/70 line-clamp-2">{{ truncateWords(page.next_post.intro, 15) }}</p>
                    </div>
                </NuxtLink>
            </div>
        </div>
    </article>
</div>

<ImageGallery ref="gallery" :images="galleryEntries" />
</template>
