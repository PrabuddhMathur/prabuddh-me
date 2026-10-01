<script setup lang="ts">
import type { StaticPageData } from '~/types/api'

// Old core/static_page.html. The API always sends last_updated; the page decides whether to show it.
defineProps<{ page: StaticPageData }>()
</script>

<template>
<div class="max-w-7xl mx-auto px-6 lg:px-12 py-12">
    <article class="max-w-4xl mx-auto">
        <!-- Breadcrumb Navigation -->
        <nav class="text-sm mb-8 text-base-content/60" aria-label="Breadcrumb">
            <ol class="flex items-center gap-2">
                <li><NuxtLink to="/" class="hover:text-base-content transition-colors">Home</NuxtLink></li>
                <li><span class="text-base-content/40">/</span></li>
                <li class="text-base-content font-medium">{{ page.title }}</li>
            </ol>
        </nav>

        <!-- Page Header -->
        <header class="mb-12">
            <h1 class="text-4xl md:text-5xl font-bold mb-6 leading-tight">{{ page.title }}</h1>

            <!-- Page Introduction -->
            <div v-if="page.intro" class="prose prose-lg max-w-none mb-8">
                <p class="text-xl text-base-content/80 leading-relaxed">{{ page.intro }}</p>
            </div>
        </header>

        <!-- Main Content - StreamField -->
        <div v-if="page.body.length" class="space-y-8">
            <StreamField :blocks="page.body" />
        </div>

        <!-- Last Updated Date -->
        <footer v-if="page.show_last_updated && page.last_updated" class="mt-16 pt-8 border-t border-base-200">
            <p class="text-sm text-base-content/60 text-center">
                Last updated: <time :datetime="formatDate(page.last_updated, 'Y-m-d')">{{ formatDate(page.last_updated, 'F j, Y') }}</time>
            </p>
        </footer>
    </article>
</div>
</template>
