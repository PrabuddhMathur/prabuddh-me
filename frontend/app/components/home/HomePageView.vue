<script setup lang="ts">
import type { HomePageData } from '~/types/api'

// Old home/home_page.html. The old featured and recent cards asked for `post.hero_image` and
// `post.excerpt`, which blog posts never had, so those cards never showed an image or an
// excerpt. They still don't.
const props = defineProps<{ page: HomePageData }>()

const { data: site } = await useSiteSettings()

const heroImage = computed(() => rendition(props.page.hero_image, 'hero'))
const authorImage = computed(() => rendition(site.value?.author.image, 'sidebar'))

const heroTextClass = computed(() => [
  props.page.hero_text_horizontal === 'center' ? 'mx-auto text-center'
  : props.page.hero_text_horizontal === 'right' ? 'ml-auto text-right' : '',
  props.page.hero_text_vertical === 'top' ? ''
  : props.page.hero_text_vertical === 'bottom' ? 'mt-auto' : 'my-auto',
])
</script>

<template>
<div class="min-h-screen">
    <!-- Hero Section -->
    <section v-if="page.hero_title || page.hero_image" class="relative bg-base-200 overflow-hidden" :class="{ 'bg-cover bg-center': heroImage }"
             :style="heroImage ? { backgroundImage: `url('${heroImage.url}')` } : undefined">
        <div v-if="heroImage" class="absolute inset-0 bg-base-100/20"></div>
        <div class="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 lg:py-24">
            <div class="max-w-2xl" :class="heroTextClass">
                <h1 v-if="page.hero_title" class="text-4xl lg:text-5xl xl:text-6xl font-bold text-base-content mb-6 leading-tight break-words">
                    {{ page.hero_title }}
                </h1>
                <p v-if="page.hero_subtitle" class="text-xl lg:text-2xl text-base-content/70 mb-8 leading-relaxed break-words tracking-wide">
                    {{ page.hero_subtitle }}
                </p>
                <LinkButton v-if="page.hero_cta_text && page.hero_cta_link" :url="page.hero_cta_link" :text="page.hero_cta_text" size="md" />
            </div>
        </div>
    </section>

    <!-- Main Content Layout -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div class="max-w-4xl mx-auto">
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-12">

                <!-- Main Content Column -->
                <div class="lg:col-span-2 space-y-12 lg:space-y-16">
                    <!-- StreamField Content (each block wrapped in <div class="block-{type}">, like {{ page.body }}) -->
                    <div v-if="page.body.length" class="space-y-8">
                        <StreamField :blocks="page.body" wrap />
                    </div>

                    <!-- Featured Posts Section -->
                    <section v-if="page.show_featured_posts && page.featured_posts.length" class="featured-posts">
                        <h2 class="text-3xl font-bold text-base-content mb-8">
                            {{ page.featured_posts_title }}
                        </h2>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <article v-for="post in page.featured_posts" :key="post.id" class="relative flex flex-col bg-base-100 shadow-md hover:shadow-lg transition-shadow duration-300 rounded-lg overflow-hidden border border-base-content/10 hover:border-base-content/20 group">
                                <div class="p-6">
                                    <h3 class="text-xl font-semibold mb-3 leading-tight">
                                        <NuxtLink :to="post.url" class="hover:text-base-content/70 transition-colors">
                                            {{ post.title }}
                                        </NuxtLink>
                                    </h3>

                                    <!-- Post Meta -->
                                    <div class="mb-3">
                                        <PostMeta :date="post.date" :reading-time="post.estimated_reading_time" />
                                    </div>

                                    <!-- Post Tags -->
                                    <PostTags :tags="post.tags" :max-tags="3" show-inline />
                                </div>
                            </article>
                        </div>
                    </section>

                    <!-- Recent Posts Section -->
                    <section v-if="page.show_recent_posts && page.recent_posts.length" class="recent-posts">
                        <h2 class="text-3xl font-bold text-base-content mb-8">
                            {{ page.recent_posts_title }}
                        </h2>
                        <div class="space-y-4">
                            <article v-for="post in page.recent_posts" :key="post.id" class="relative group flex gap-4 sm:gap-6 p-4 sm:p-6 border border-base-content/10 rounded-lg shadow-sm hover:shadow-md hover:border-base-content/20 transition-all duration-300">
                                <NuxtLink :to="post.url" class="absolute inset-0 z-0" :aria-label="`Read ${post.title}`"></NuxtLink>

                                <div class="flex-1 min-w-0">
                                    <h3 class="text-lg font-semibold mb-2 group-hover:text-base-content/70 transition-colors leading-tight">
                                        {{ post.title }}
                                    </h3>

                                    <!-- Post Meta -->
                                    <div class="mb-2">
                                        <PostMeta :date="post.date" :reading-time="post.estimated_reading_time" />
                                    </div>

                                    <!-- Post Tags -->
                                    <PostTags :tags="post.tags" :max-tags="2" show-inline />
                                </div>
                            </article>
                        </div>

                        <!-- View All Posts Button -->
                        <div class="text-center mt-8">
                            <LinkButton url="/blog/" text="View All Posts" size="md" />
                        </div>
                    </section>
                </div>

                <!-- Sidebar -->
                <aside class="lg:col-span-1">
                    <div class="sticky top-24 space-y-8">

                        <!-- Author Bio Card -->
                        <div v-if="page.show_author_sidebar && site?.author.name" class="relative flex flex-col bg-base-100 border-2 border-base-content/10 hover:border-base-content/20 rounded-xl p-8 shadow-sm transition-colors">
                            <div v-if="authorImage" class="mb-6 flex justify-center">
                                <img :alt="site.author.image?.title" class="w-32 h-32 rounded-full object-cover ring-2 ring-base-content/10 shadow-sm" :height="authorImage.height" :src="authorImage.url" :width="authorImage.width">
                            </div>

                            <div class="text-center">
                                <h3 class="text-2xl font-bold mb-2 text-base-content">
                                    {{ site.author.name }}
                                </h3>
                                <p v-if="site.author.title" class="text-sm font-medium text-base-content/70 mb-4 tracking-wide uppercase">
                                    {{ site.author.title }}
                                </p>

                                <div v-if="site.author.bio_short" class="border-t border-base-content/10 pt-4 mt-4">
                                    <p class="text-sm text-base-content/80 leading-relaxed">
                                        {{ site.author.bio_short }}
                                    </p>
                                </div>

                                <!-- Social Links Component -->
                                <div v-if="site.author.social_links.length" class="mt-6 pt-6 border-t border-base-content/10">
                                    <SocialLinks :links="site.author.social_links" size="md" layout="horizontal" classes="justify-center" />
                                </div>
                            </div>
                        </div>

                    </div>
                </aside>

            </div>
        </div>
    </div>
</div>
</template>
