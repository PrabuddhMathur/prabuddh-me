import type { InjectionKey } from 'vue'

/** What a blog post provides to its image blocks, so their buttons open the gallery. */
export interface GalleryContext {
  /** Opens the gallery at the image block with this StreamField block id. */
  open: (blockId: string) => void
}

/**
 * provide(galleryKey, …) on the blog post page; inject(galleryKey, null) in ImageBlock.
 * Outside a blog post nothing is provided, and the image button does nothing (as before).
 */
export const galleryKey: InjectionKey<GalleryContext> = Symbol('gallery')
