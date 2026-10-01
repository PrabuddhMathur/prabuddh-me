<script setup lang="ts">
// Old core/components/pagination.html. The links keep only ?page=N, as the old relative links did.
defineProps<{ page: number, numPages: number, classes?: string }>()
const route = useRoute()
</script>

<template>
<nav v-if="numPages > 1" class="flex justify-center mt-12" :class="classes" aria-label="Pagination">
    <div class="flex gap-2">
        <NuxtLink
           v-if="page > 1"
           :to="{ path: route.path, query: { page: page - 1 } }"
           no-rel
           class="min-h-[44px] min-w-[44px] px-4 py-2 border border-base-content/10 hover:bg-base-200 hover:border-base-content/20 transition-colors rounded-lg flex items-center justify-center"
           aria-label="Previous page">
            <span class="hidden sm:inline">← Previous</span>
            <span class="sm:hidden">←</span>
        </NuxtLink>

        <span class="min-h-[44px] px-4 py-2 border border-base-content/10 bg-base-200 rounded-lg font-medium flex items-center justify-center">
            <span class="hidden sm:inline">Page {{ page }} of {{ numPages }}</span>
            <span class="sm:hidden">{{ page }}/{{ numPages }}</span>
        </span>

        <NuxtLink
           v-if="page < numPages"
           :to="{ path: route.path, query: { page: page + 1 } }"
           no-rel
           class="min-h-[44px] min-w-[44px] px-4 py-2 border border-base-content/10 hover:bg-base-200 hover:border-base-content/20 transition-colors rounded-lg flex items-center justify-center"
           aria-label="Next page">
            <span class="hidden sm:inline">Next →</span>
            <span class="sm:hidden">→</span>
        </NuxtLink>
    </div>
</nav>
</template>
