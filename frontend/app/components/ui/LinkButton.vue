<script setup lang="ts">
// Old core/components/button.html: an outlined link that fills on hover.
withDefaults(defineProps<{
  url: string
  text: string
  size?: 'xs' | 'sm' | 'md' | 'lg'
  /** Opens in a new tab (target="_blank" rel="noopener noreferrer"). */
  external?: boolean
  /** Extra classes, appended like the old `classes` parameter. */
  classes?: string
}>(), {
  size: 'md',
  external: false,
  classes: '',
})
</script>

<template>
  <NuxtLink
    :to="url"
    class="inline-block border border-base-content hover:bg-base-content hover:text-base-100 transition-colors font-medium"
    :class="[
      size === 'xs' ? 'text-xs px-3 py-1.5'
      : size === 'sm' ? 'text-sm px-4 py-2'
        : size === 'lg' ? 'text-lg px-8 py-4'
          : 'px-6 py-3',
      classes,
    ]"
    :target="external ? '_blank' : undefined"
    :rel="external ? 'noopener noreferrer' : undefined"
    :no-rel="external ? undefined : true"
  >{{ text }}</NuxtLink>
</template>
