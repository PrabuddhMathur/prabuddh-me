<script setup lang="ts">
import type { PostSummary } from '~/types/api'

// Old blog/blog_listing.html (variant 'listing') and blog/blog_archive.html (variant 'archive').
// The archive's breadcrumb <nav> sat outside its content block, so archives have none.
defineProps<{
  variant: 'listing' | 'archive'
  heading: string
  count: number
  posts: PostSummary[]
  page: number
  numPages: number
}>()

const STORAGE_KEY = 'blog-view-mode'

// Copies the saved view to <html data-blog-view> before the first paint; the CSS below does the rest.
useHead({
  script: [{
    key: 'blog-view-mode',
    innerHTML: `try{var v=localStorage.getItem('${STORAGE_KEY}');if(v==='list'||v==='masonry')document.documentElement.dataset.blogView=v}catch(e){}`,
  }],
})

const open = ref(false)

function readSaved(): string {
  try {
    return localStorage.getItem(STORAGE_KEY) === 'list' ? 'list' : 'masonry'
  }
  catch {
    return 'masonry'
  }
}

function switchView(view: 'masonry' | 'list') {
  document.documentElement.dataset.blogView = view
  try {
    localStorage.setItem(STORAGE_KEY, view)
  }
  catch {
    // Storage blocked: the choice only lasts for this page.
  }
  open.value = false
}

function closeMenu() {
  open.value = false
}

// A client-side navigation to a listing doesn't run the head script again.
onMounted(() => {
  document.documentElement.dataset.blogView = readSaved()
  document.addEventListener('click', closeMenu)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', closeMenu)
})
</script>

<template>
<!-- Breadcrumbs -->
<nav v-if="variant === 'listing'" class="max-w-7xl mx-auto px-4 md:px-6 lg:px-8 py-4" aria-label="Breadcrumb">
    <div class="max-w-4xl mx-auto">
        <ol class="flex items-center gap-2 text-sm text-base-content/60">
            <li><NuxtLink to="/" no-rel class="hover:text-base-content transition-colors">Home</NuxtLink></li>
            <li><span class="text-base-content/40">/</span></li>
            <li class="text-base-content font-medium">Blog</li>
        </ol>
    </div>
</nav>

<div class="max-w-7xl mx-auto px-4 md:px-6 lg:px-8" :class="variant === 'listing' ? 'py-8 lg:py-12' : 'py-12'">
    <!-- Header with view controls -->
    <div class="mb-12 max-w-4xl mx-auto" :class="variant === 'listing' ? '' : 'space-y-6'">
        <div class="flex items-center justify-between gap-4" :class="variant === 'listing' ? 'mb-6' : ''">
            <div>
                <h1
                    class="font-bold text-base-content mb-2"
                    :class="variant === 'listing' ? 'text-2xl md:text-4xl lg:text-5xl' : 'text-3xl lg:text-4xl'"
                >
                    {{ heading }}
                </h1>
                <p :class="variant === 'listing' ? 'text-lg text-base-content/60' : 'text-base-content/60'">{{ count }} post{{ pluralize(count) }}</p>
            </div>

            <!-- View mode dropdown -->
            <div class="relative flex-shrink-0">
                <button id="view-dropdown-toggle"
                        class="btn btn-outline gap-2"
                        aria-label="Change view mode"
                        @click.stop="open = !open">
                    <svg id="current-view-icon" xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path class="view-icon-masonry" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 5a1 1 0 011-1h4a1 1 0 011 1v7a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM14 5a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1V5zM4 16a1 1 0 011-1h4a1 1 0 011 1v3a1 1 0 01-1 1H5a1 1 0 01-1-1v-3zM14 14a1 1 0 011-1h4a1 1 0 011 1v5a1 1 0 01-1 1h-4a1 1 0 01-1-1v-5z" />
                        <path class="view-icon-list" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
                    </svg>
                    <span class="hidden sm:inline">View</span>
                    <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                    </svg>
                </button>

                <div id="view-dropdown-menu" class="absolute right-0 mt-2 w-48 bg-base-100 border border-base-content/20 rounded-lg shadow-2xl z-50 overflow-hidden" :class="{ hidden: !open }" @click.stop>
                    <button data-view="masonry" class="view-option w-full flex items-center gap-3 px-4 py-3 text-sm hover:bg-base-200 transition-colors text-left" @click="switchView('masonry')">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 5a1 1 0 011-1h4a1 1 0 011 1v7a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM14 5a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1V5zM4 16a1 1 0 011-1h4a1 1 0 011 1v3a1 1 0 01-1 1H5a1 1 0 01-1-1v-3zM14 14a1 1 0 011-1h4a1 1 0 011 1v5a1 1 0 01-1 1h-4a1 1 0 01-1-1v-5z" />
                        </svg>
                        <span>Masonry Grid</span>
                    </button>
                    <button data-view="list" class="view-option w-full flex items-center gap-3 px-4 py-3 text-sm hover:bg-base-200 transition-colors text-left" @click="switchView('list')">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
                        </svg>
                        <span>List View</span>
                    </button>
                </div>
            </div>
        </div>
    </div>

    <!-- Blog Posts - Masonry and List views, switched with html[data-blog-view] -->
    <template v-if="posts.length">
        <!-- List View -->
        <div id="view-list" class="view-container max-w-4xl mx-auto mb-12 space-y-6">
            <PostListItem v-for="post in posts" :key="post.id" :post="post" />
        </div>

        <!-- Masonry Grid - Default View - Mobile: 1 column, Tablet: 2 columns, Desktop: 3 columns -->
        <div id="view-masonry" class="view-container max-w-4xl mx-auto columns-1 md:columns-2 lg:columns-3 gap-6 mb-12">
            <div v-for="post in posts" :key="post.id" class="break-inside-avoid mb-6">
                <PostCard :post="post" />
            </div>
        </div>

        <!-- Pagination -->
        <div class="max-w-4xl mx-auto">
            <Pagination :page="page" :num-pages="numPages" />
        </div>
    </template>
    <template v-else-if="variant === 'listing'">
        <!-- Empty state -->
        <div class="max-w-4xl mx-auto text-center py-16 px-6">
            <div class="text-6xl mb-6">📝</div>
            <h3 class="text-2xl font-bold mb-3 text-base-content">No posts yet</h3>
            <p class="text-base-content/70 mb-8 max-w-md mx-auto">
                Check back soon for new content!
            </p>
            <NuxtLink to="/" no-rel class="btn btn-primary gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
                Back to Home
            </NuxtLink>
        </div>
    </template>
    <div v-else class="max-w-4xl mx-auto grid grid-flow-col grid-cols-[auto_minmax(auto,1fr)] items-center justify-start justify-items-start gap-4 px-4 py-3 rounded-box border border-info bg-info text-info-content text-start text-[0.875rem]/5 shadow-md">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="stroke-current shrink-0 w-6 h-6">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
        </svg>
        <span>No blog posts found.</span>
    </div>
</div>
</template>

<style>
/* The view switch: the saved choice is copied to <html data-blog-view> before paint. Masonry is the default. */
#view-list { display: none; }
html[data-blog-view="list"] #view-list { display: block; }
html[data-blog-view="list"] #view-masonry { display: none; }
#current-view-icon .view-icon-list { display: none; }
html[data-blog-view="list"] #current-view-icon .view-icon-masonry { display: none; }
html[data-blog-view="list"] #current-view-icon .view-icon-list { display: inline; }
</style>

