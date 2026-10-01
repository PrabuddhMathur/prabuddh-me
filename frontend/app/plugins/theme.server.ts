// The old site's HTML always had <html data-theme="light">; its inline script then switched to
// the saved theme before the first paint. @nuxtjs/color-mode does that switch (same
// localStorage key and values) but only sets the attribute in the browser, so the server adds
// the default here. The browser-side attribute stays under color-mode's control.
export default defineNuxtPlugin(() => {
  useHead({ htmlAttrs: { 'data-theme': 'light' } })
})
