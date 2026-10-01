<script setup lang="ts">
import type { LinkItem } from '~/types/api'

// Old core/components/mobile-menu.html, a daisyUI "dropdown dropdown-end" with a
// "menu dropdown-content" list. daisyUI opened it on :focus-within; here a click opens it,
// and a click outside, Escape, leaving it with the keyboard or navigating closes it.
defineProps<{ links: LinkItem[] }>()

const route = useRoute()
const open = ref(false)
const trigger = ref<HTMLElement | null>(null)
const menu = ref<HTMLElement | null>(null)

function toggle() {
  open.value = !open.value
}

// While open the trigger has pointer-events: none (as in daisyUI), so clicking it again lands
// on the wrapper and closes the menu like any other click outside the list.
function onDocumentClick(event: MouseEvent) {
  const target = event.target as Node
  if (open.value && !menu.value?.contains(target) && !trigger.value?.contains(target)) open.value = false
}

function onDocumentKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') open.value = false
}

function onFocusOut(event: FocusEvent) {
  const next = event.relatedTarget as Node | null
  if (next && !menu.value?.contains(next) && !trigger.value?.contains(next)) open.value = false
}

onMounted(() => {
  document.addEventListener('click', onDocumentClick)
  document.addEventListener('keydown', onDocumentKeydown)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', onDocumentClick)
  document.removeEventListener('keydown', onDocumentKeydown)
})

watch(() => route.fullPath, () => {
  open.value = false
})
</script>

<template>
  <div class="relative inline-block" @focusout="onFocusOut">
    <div
      ref="trigger"
      tabindex="0"
      role="button"
      class="h-11 w-11 hover:bg-base-200 rounded-lg transition-colors flex items-center justify-center focus:outline-none"
      :class="{ 'pointer-events-none': open }"
      aria-label="Open menu"
      :aria-expanded="open"
      @click="toggle"
      @keydown.enter.prevent="toggle"
      @keydown.space.prevent="toggle"
    >
      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
      </svg>
    </div>
    <!-- menu + dropdown-content: daisyUI's effective styles, then the old utilities. -->
    <ul
      ref="menu"
      tabindex="0"
      class="flex flex-col flex-wrap text-[0.875rem] absolute end-0 translate-0 focus:outline-none motion-safe:animate-[dropdown_0.2s] motion-safe:transition-[opacity,scale,display] motion-safe:transition-discrete motion-safe:duration-200 starting:opacity-0 starting:scale-95 mt-3 z-[1] p-2 bg-base-100 border border-base-200 rounded-lg w-52 shadow-lg"
      :class="open ? 'opacity-100 scale-100' : 'hidden origin-top opacity-0 scale-95'"
    >
      <li v-for="link in links" :key="link.url" class="relative flex shrink-0 flex-col flex-wrap items-stretch">
        <NuxtLink
          :to="link.url"
          no-rel
          class="grid-flow-col gap-2 rounded-field px-3 py-1.5 text-start content-start text-balance select-none transition-[color,background-color,box-shadow] duration-200 ease-[cubic-bezier(0,0,0.2,1)] hover:bg-base-content/10 focus-visible:bg-base-content/10 focus-visible:text-base-content focus-visible:outline-none active:bg-neutral active:text-neutral-content active:outline-none min-h-[44px] flex items-center"
          :class="{ 'font-semibold': route.path === link.url }"
        >{{ link.text }}</NuxtLink>
      </li>
    </ul>
  </div>
</template>
