<script setup lang="ts">
import type { LocationQueryValue } from 'vue-router'
import type { SearchResponse } from '~/types/api'

// Old search/search.html. Reads ?query=, or ?q= (what the old header search box sent).
// The result count is the total, not the number of results on this page as before.
const route = useRoute()

// Like Django's request.GET.get(): the last value of a repeated parameter.
function param(value: LocationQueryValue | LocationQueryValue[] | undefined): string {
  return (Array.isArray(value) ? value.at(-1) : value) ?? ''
}

const searchQuery = computed(() => param(route.query.query) || param(route.query.q))

const { data, error } = await useApi<SearchResponse>('/api/v2/search/', {
  query: computed(() => ({ query: searchQuery.value, page: param(route.query.page) || undefined })),
})
if (error.value) {
  throw createError({ statusCode: 500, statusMessage: 'Search failed', fatal: true })
}

usePageSeo(() => ({ title: searchQuery.value ? `Search - ${searchQuery.value}` : 'Search' }))

function pageLink(page: number) {
  return { path: '/search/', query: { query: searchQuery.value, page } }
}
</script>

<template>
<div class="max-w-4xl mx-auto px-6 lg:px-12 py-12">
    <!-- Page Header -->
    <div class="mb-8 text-center">
        <h1 class="text-4xl md:text-5xl font-bold mb-4 text-base-content">Search</h1>
        <p class="text-lg text-base-content/70">Find posts, pages, and content across the site</p>
    </div>

    <!-- Enhanced Search Form -->
    <form action="/search/" method="get" class="mb-12" role="search">
        <div class="flex flex-col sm:flex-row gap-3">
            <div class="flex-1">
                <input type="text"
                       name="query"
                       :value="searchQuery || undefined"
                       class="input input-lg w-full min-h-[44px]"
                       placeholder="What are you looking for?"
                       aria-label="Search query"
                       required>
            </div>
            <button type="submit" class="btn btn-primary btn-lg gap-2 min-h-[44px]" aria-label="Search">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                Search
            </button>
        </div>
    </form>

    <!-- Search Results -->
    <template v-if="data?.results.length">
        <!-- Results count -->
        <div class="mb-6">
            <p class="text-base-content/70">
                Found <span class="font-semibold text-base-content">{{ data.count }}</span>
                result{{ pluralize(data.count) }} for
                "<span class="font-semibold text-primary">{{ searchQuery }}</span>"
            </p>
        </div>

        <!-- Results list with enhanced cards -->
        <div class="space-y-4">
            <article v-for="result in data.results" :key="result.id" class="relative flex flex-col rounded-box bg-base-100 border border-base-content/10 hover:border-primary/50 hover:shadow-lg transition-all duration-300">
                <div class="flex flex-auto flex-col gap-2 text-[0.875rem] p-6">
                    <h2 class="flex items-center gap-2 font-semibold text-xl md:text-2xl hover:text-primary transition-colors">
                        <NuxtLink :to="result.url" class="hover:underline">{{ result.title }}</NuxtLink>
                    </h2>
                    <p v-if="result.search_description" class="grow text-base-content/80 leading-relaxed line-clamp-2">
                        {{ result.search_description }}
                    </p>
                    <div class="flex flex-wrap gap-2 justify-between items-center mt-2">
                        <span class="inline-flex items-center justify-center gap-2 rounded-selector align-middle border border-current text-[0.875rem] w-fit px-[calc(0.75rem-1px)] h-6">
                            {{ result.type_label }}
                        </span>
                        <NuxtLink :to="result.url"
                           class="cursor-pointer underline text-primary hover:text-[color-mix(in_oklab,var(--color-primary)_80%,#000)] focus:outline-none focus-visible:outline-2 focus-visible:outline-solid focus-visible:outline-current focus-visible:outline-offset-2 text-sm gap-1 inline-flex items-center">
                            Read more
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                            </svg>
                        </NuxtLink>
                    </div>
                </div>
            </article>
        </div>

        <!-- Enhanced Pagination -->
        <div v-if="data.num_pages > 1" class="flex justify-center mt-12">
            <div class="join">
                <NuxtLink v-if="data.page > 1" :to="pageLink(data.page - 1)"
                   class="join-item btn btn-outline min-h-[44px]"
                   aria-label="Previous page">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
                    </svg>
                    <span class="hidden sm:inline">Previous</span>
                </NuxtLink>

                <button class="join-item btn btn-outline pointer-events-none min-h-[44px]">
                    Page {{ data.page }} of {{ data.num_pages }}
                </button>

                <NuxtLink v-if="data.page < data.num_pages" :to="pageLink(data.page + 1)"
                   class="join-item btn btn-outline min-h-[44px]"
                   aria-label="Next page">
                    <span class="hidden sm:inline">Next</span>
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                    </svg>
                </NuxtLink>
            </div>
        </div>
    </template>

    <!-- Enhanced No Results State -->
    <div v-else-if="searchQuery" class="text-center py-16 px-6">
        <div class="text-8xl mb-6">🔍</div>
        <h2 class="text-3xl font-bold mb-4 text-base-content">No results found</h2>
        <p class="text-lg text-base-content/70 mb-8 max-w-md mx-auto leading-relaxed">
            We couldn't find anything matching "<span class="font-semibold text-primary">{{ searchQuery }}</span>".
            Try different keywords or browse our content.
        </p>
        <div class="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <NuxtLink to="/search/" class="btn btn-primary gap-2 min-h-[44px]">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                New Search
            </NuxtLink>
            <NuxtLink to="/blog/" class="btn btn-outline gap-2 min-h-[44px]">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" />
                </svg>
                Browse Blog
            </NuxtLink>
        </div>
    </div>

    <!-- Initial State - No search performed yet -->
    <div v-else class="text-center py-16 px-6">
        <div class="text-8xl mb-6">📚</div>
        <h2 class="text-2xl font-bold mb-4 text-base-content">Start Your Search</h2>
        <p class="text-lg text-base-content/70 max-w-md mx-auto leading-relaxed">
            Enter keywords above to find posts, pages, and content across the site.
        </p>
    </div>
</div>
</template>
