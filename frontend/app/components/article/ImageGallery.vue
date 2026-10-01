<script setup lang="ts">
// Old blog_page.html image gallery: a native <dialog> opened with showModal(), previous/next
// buttons (shown when there is more than one image), arrow keys, counter, caption and a 150 ms
// fade between images. Escape, the close button and the backdrop close it natively.
interface GalleryImage {
  url: string
  caption: string
  alt: string
}

const props = defineProps<{ images: GalleryImage[] }>()

const dialog = ref<HTMLDialogElement>()
// What is on screen: the image and its position (the counter changes together with the image).
const shown = ref<{ image: GalleryImage, index: number }>()
const faded = ref(false)
let index = 0

function show(at: number) {
  if (!props.images.length) return
  index = at
  shown.value = { image: props.images[at]!, index: at }
  faded.value = false
  dialog.value?.showModal()
}

function step(direction: 1 | -1) {
  const count = props.images.length
  if (count <= 1) return
  index = (index + direction + count) % count
  const next = { image: props.images[index]!, index }
  faded.value = true
  setTimeout(() => {
    shown.value = next
    faded.value = false
  }, 150)
}

function onKeydown(event: KeyboardEvent) {
  if (event.key === 'ArrowLeft') {
    event.preventDefault()
    step(-1)
  } else if (event.key === 'ArrowRight') {
    event.preventDefault()
    step(1)
  }
}

defineExpose({ show })
</script>

<template>
<dialog
    id="image_gallery_modal"
    ref="dialog"
    class="group/modal pointer-events-none invisible fixed inset-0 z-[999] m-0 grid h-full max-h-none w-full max-w-none items-center justify-items-center overflow-clip overscroll-contain bg-transparent p-0 text-inherit [scrollbar-gutter:auto] [transition:visibility_0.3s_allow-discrete,background-color_0.3s_ease-out,opacity_0.1s_ease-out] backdrop:hidden open:pointer-events-auto open:visible open:bg-[oklch(0%_0_0/0.4)] open:opacity-100 open:[transition:visibility_0s_allow-discrete,background-color_0.3s_ease-out,opacity_0.1s_ease-out]"
    aria-label="Image gallery"
    @keydown="onKeydown"
>
    <div class="relative col-start-1 row-start-1 max-h-screen w-11/12 max-w-7xl overflow-y-auto overscroll-contain rounded-box bg-base-300 p-0 opacity-0 [box-shadow:oklch(0%_0_0/0.25)_0px_25px_50px_-12px] [scale:95%] [transition:translate_0.3s_ease-out,scale_0.3s_ease-out,opacity_0.2s_ease-out_0.05s,box-shadow_0.3s_ease-out] group-open/modal:opacity-100 group-open/modal:[scale:100%]">
        <form method="dialog">
            <button class="absolute right-4 top-4 z-50 btn btn-sm btn-circle bg-base-100/90 hover:bg-base-100 border-0 shadow-lg" aria-label="Close gallery">✕</button>
        </form>
        
        <button id="gallery_prev" 
                class="absolute left-4 top-1/2 -translate-y-1/2 z-40 btn btn-circle btn-lg bg-base-100/90 hover:bg-base-100 border-0 shadow-lg"
                :style="{ display: images.length > 1 ? 'flex' : 'none' }"
                aria-label="Previous image"
                @click.prevent.stop="step(-1)">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
            </svg>
        </button>
        
        <button id="gallery_next" 
                class="absolute right-4 top-1/2 -translate-y-1/2 z-40 btn btn-circle btn-lg bg-base-100/90 hover:bg-base-100 border-0 shadow-lg"
                :style="{ display: images.length > 1 ? 'flex' : 'none' }"
                aria-label="Next image"
                @click.prevent.stop="step(1)">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
        </button>
        
        <div class="p-8">
            <img id="gallery_image" 
                 :src="shown?.image.url ?? ''" 
                 :alt="shown?.image.alt ?? ''" 
                 :style="{ opacity: faded ? 0 : 1 }"
                 class="w-full h-auto max-h-[70vh] object-contain rounded-lg shadow-2xl mx-auto [transition:opacity_0.15s_ease-in-out]">
            
            <div id="gallery_caption" class="mt-4 text-center text-sm text-base-content/80" :class="{ hidden: !shown?.image.caption }">{{ shown?.image.caption }}</div>
            
            <div id="gallery_counter" class="mt-4 text-center text-sm text-base-content/60">{{ shown ? `${shown.index + 1} / ${images.length}` : '' }}</div>
        </div>
    </div>
    <form method="dialog" class="col-start-1 row-start-1 z-[-1] grid self-stretch justify-self-stretch text-transparent [&_button]:cursor-pointer">
        <button>close</button>
    </form>
</dialog>
</template>

<style>
/* daisyUI's modal darkened the page's own background too while a modal was open. */
:root:has(dialog[open]) {
  background-color: color-mix(in srgb, var(--root-bg, var(--color-base-100)), oklch(0% 0 0) 40%);
}
</style>
