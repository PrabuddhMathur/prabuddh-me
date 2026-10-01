<script setup lang="ts">
import type { SiteSettings } from '~/types/api'

// Old core/includes/header.html.
const props = defineProps<{ header: SiteSettings['header'] }>()

const route = useRoute()
const sticky = computed(() => props.header.header_style === 'sticky')
const logo = computed(() => (props.header.show_logo ? rendition(props.header.logo, 'logo') : undefined))

// Sticky header: hidden while scrolling down past 100px, shown again when scrolling up
// (the old inline script, which set style.transform directly).
const navbar = ref<HTMLElement | null>(null)
let lastScrollTop = 0
let isScrolling = false

function onScroll() {
  if (isScrolling) return
  isScrolling = true
  window.requestAnimationFrame(() => {
    const currentScroll = window.pageYOffset || document.documentElement.scrollTop
    if (navbar.value) {
      if (currentScroll <= 100) navbar.value.style.transform = 'translateY(0)'
      else if (currentScroll > lastScrollTop) navbar.value.style.transform = 'translateY(-100%)'
      else if (currentScroll < lastScrollTop) navbar.value.style.transform = 'translateY(0)'
    }
    lastScrollTop = currentScroll <= 0 ? 0 : currentScroll
    isScrolling = false
  })
}

onMounted(() => {
  if (sticky.value) window.addEventListener('scroll', onScroll, { passive: true })
})

onBeforeUnmount(() => {
  window.removeEventListener('scroll', onScroll)
})
</script>

<template>
  <nav
    id="main-navbar"
    ref="navbar"
    class="bg-base-100 border-b border-base-200"
    :class="{ 'sticky top-0 z-50 transition-transform duration-300': sticky }"
  >
    <div class="max-w-7xl mx-auto px-6 lg:px-12 py-4 flex items-center justify-between">
      <!-- Logo / Site Title -->
      <NuxtLink to="/" class="text-lg font-semibold tracking-tight hover:text-base-content/70 transition-colors">
        <img
          v-if="logo"
          :alt="header.logo?.title"
          class="inline-block"
          :height="logo.height"
          :src="logo.url"
          :width="logo.width"
        >
        <template v-else>{{ header.site_title }}</template>
      </NuxtLink>

      <!-- Desktop Navigation Links -->
      <div class="hidden lg:flex items-center gap-8">
        <NuxtLink
          v-for="link in header.navigation"
          :key="link.url"
          :to="link.url"
          no-rel
          class="text-sm font-medium hover:text-base-content transition-colors"
          :class="route.path === link.url ? 'text-base-content border-b-2 border-base-content pb-1' : 'text-base-content/90'"
        >{{ link.text }}</NuxtLink>
      </div>

      <!-- Right Side Actions -->
      <div class="flex items-center gap-2">
        <!-- Search Bar. The old input was named "q", which the search page ignored; "query" works. -->
        <form v-if="header.show_search" action="/search/" method="get" class="hidden md:block">
          <input type="text" name="query" placeholder="Search..." class="input input-sm w-40 focus:w-56 transition-all" aria-label="Search">
        </form>

        <!-- Theme Toggle Button -->
        <ThemeToggle v-if="header.show_theme_toggle" />

        <!-- Mobile Menu Button -->
        <div class="lg:hidden">
          <MobileMenu :links="header.navigation" />
        </div>
      </div>
    </div>
  </nav>
</template>
