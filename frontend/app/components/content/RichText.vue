<script setup lang="ts">
// Rich-text HTML from the API (trusted CMS content, so v-html is fine) plus the old
// core/js/spoiler.js: click, Enter or Space on a spoiler toggles it. Attributes go on the root
// <div> (class and so on), as the old templates put the classes on the wrapper.
const props = defineProps<{ html: string }>()

const SPOILER_SELECTOR = '.spoiler[data-spoiler="true"]'

// The old script added these accessibility attributes when the page loaded; adding them to the
// HTML string puts them in the server-rendered markup too.
const SPOILER_ATTRS = ' role="button" tabindex="0" aria-label="Spoiler text - click to reveal" aria-pressed="false"'
const content = computed(() => props.html.replace(/<span\b[^>]*>/g, (tag) => {
  const isSpoiler = /\bclass="(?:[^"]*\s)?spoiler(?:\s[^"]*)?"/.test(tag) && /\bdata-spoiler="true"/.test(tag)
  return isSpoiler && !/\brole=/.test(tag) ? tag.slice(0, -1) + SPOILER_ATTRS + '>' : tag
}))

function toggleSpoiler(spoiler: HTMLElement) {
  spoiler.classList.toggle('revealed')
  const revealed = spoiler.classList.contains('revealed')
  spoiler.setAttribute('aria-label', revealed ? 'Spoiler text - revealed, click to hide' : 'Hidden spoiler text - click to reveal')
  spoiler.setAttribute('aria-pressed', revealed ? 'true' : 'false')
  spoiler.dispatchEvent(new CustomEvent('spoiler:toggled', {
    detail: { element: spoiler, revealed, text: spoiler.textContent },
    bubbles: true,
  }))
}

function onClick(event: MouseEvent) {
  const target = event.target
  if (!(target instanceof Element)) return

  const spoiler = target.closest<HTMLElement>(SPOILER_SELECTOR)
  if (spoiler) {
    event.preventDefault()
    toggleSpoiler(spoiler)
    return
  }

  // Internal links navigate client-side (plain same-tab left clicks only).
  const link = target.closest('a')
  if (!link || event.defaultPrevented || event.button !== 0) return
  if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return
  if ((link.target && link.target !== '_self') || link.hasAttribute('download')) return
  const href = link.getAttribute('href')
  if (!isInternalUrl(href)) return
  event.preventDefault()
  navigateTo(href)
}

function onKeydown(event: KeyboardEvent) {
  if (event.key !== 'Enter' && event.key !== ' ') return
  const spoiler = event.target instanceof Element ? event.target.closest<HTMLElement>(SPOILER_SELECTOR) : null
  if (!spoiler) return
  event.preventDefault()
  toggleSpoiler(spoiler)
}

// Prevents text selection on double and triple clicks of a spoiler.
function onMousedown(event: MouseEvent) {
  if (event.detail > 1 && event.target instanceof Element && event.target.closest(SPOILER_SELECTOR)) {
    event.preventDefault()
  }
}
</script>

<template>
<div @click="onClick" @keydown="onKeydown" @mousedown="onMousedown" v-html="content"></div>
</template>
