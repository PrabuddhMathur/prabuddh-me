<script setup lang="ts">
import type { SiteSettings } from '~/types/api'

// Old core/includes/footer.html. The daisyUI "footer" class is replaced by its effective
// styles: a grid whose child keeps gap-2 (it adds to the space-y-8 margins) and is only as
// wide as its content (place-items: start), centred by mx-auto.
const props = defineProps<{
  footer: SiteSettings['footer']
  authorName: string
}>()

const copyright = computed(() => {
  const parts: string[] = []
  if (props.footer.show_year) parts.push(`© ${new Date().getUTCFullYear()}`)
  if (props.authorName) parts.push(props.authorName)
  if (props.footer.copyright_text) parts.push(`• ${props.footer.copyright_text}`)
  return parts.join(' ')
})
</script>

<template>
  <footer class="grid w-full grid-flow-row place-items-start gap-x-4 gap-y-10 text-[0.875rem] leading-[1.25rem] bg-base-200 border-t border-base-300 mt-12">
    <div class="justify-items-start gap-2 max-w-4xl mx-auto px-6 py-8 flex flex-col items-center text-center space-y-8">
      <NewsletterSignup v-if="footer.show_newsletter" />

      <div v-if="footer.show_quick_links && footer.links.length">
        <h3 class="text-lg font-semibold mb-4">Quick Links</h3>
        <nav class="flex flex-wrap justify-center gap-x-3 gap-y-2" aria-label="Footer navigation">
          <template v-for="(link, index) in footer.links" :key="index">
            <NuxtLink :to="link.url" no-rel class="text-sm text-base-content/70 hover:text-primary transition-colors">{{ link.text }}</NuxtLink>
            <span v-if="index < footer.links.length - 1" class="text-base-content/40" aria-hidden="true">•</span>
          </template>
        </nav>
      </div>

      <div>
        <p class="text-sm text-base-content/60">{{ copyright }}</p>
      </div>
    </div>
  </footer>
</template>
