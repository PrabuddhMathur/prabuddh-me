import tailwindcss from '@tailwindcss/vite'

// This file runs in Node. Typed here so the project needs no @types/node just for this.
declare const process: { env: Record<string, string | undefined> }

// Read here (not only through runtimeConfig) because the dev proxy target below
// is fixed when the dev server starts.
const backendUrl = process.env.NUXT_BACKEND_URL ?? 'http://localhost:8000'

// docker-compose.dev.yaml sets this. Folders shared from the host into the container don't
// deliver file-change events, so without polling the dev server never sees new or edited files.
const usePolling = process.env.CHOKIDAR_USEPOLLING === 'true'

export default defineNuxtConfig({
  compatibilityDate: '2026-10-01',
  devtools: { enabled: true },

  modules: ['@nuxtjs/color-mode'],
  css: ['~/assets/css/main.css'],
  vite: {
    plugins: [tailwindcss()],
    server: { watch: { usePolling, interval: 500 } },
  },
  // Nuxt's own watcher (new and removed pages, components, composables).
  watchers: { chokidar: { usePolling, interval: 500 } },
  // Tailwind and Vite already minify the CSS. Nuxt's extra cssnano pass would also round
  // Tailwind's line heights (calc(1.25 / 0.875) becomes 1.42857), moving text by fractions of
  // a pixel compared with the old site, whose CSS kept the calc().
  postcss: {
    plugins: { cssnano: false },
  },

  // Components are used by file name only (<PostCard>, not <ListingPostCard>),
  // so every component file name must be unique.
  components: [{ path: '~/components', pathPrefix: false }],

  // Keep whitespace between elements like plain HTML does (Vue drops it by default when it
  // contains a line break). The templates are ports of the old HTML, where a line break
  // between two inline elements renders as a space, e.g. "Home / Blog" in breadcrumbs.
  vue: {
    compilerOptions: { whitespace: 'preserve' },
  },

  // The old site kept the theme in localStorage.theme ('light' or 'dim') and put it
  // on <html data-theme="…">. Same key and values, so returning visitors keep theirs.
  colorMode: {
    preference: 'light',
    fallback: 'light',
    dataValue: 'theme',
    classSuffix: '',
    storageKey: 'theme',
  },

  runtimeConfig: {
    // Where the Nuxt server reaches Wagtail (NUXT_BACKEND_URL). Browsers use same-origin /api/.
    backendUrl: 'http://localhost:8000',
    public: {
      // Public address of the site, for canonical and Open Graph URLs (NUXT_PUBLIC_SITE_URL).
      siteUrl: 'http://localhost:3000',
    },
  },

  routeRules: {
    // The old author archive redirected to the listing (there is only one author).
    '/blog/author/**': { redirect: { to: '/blog/', statusCode: 302 } },
  },

  // In production Caddy sends these paths to Wagtail before they reach Nuxt.
  $development: {
    routeRules: {
      // Hand the backend's redirects to the browser, as Caddy does, instead of following them
      // here: the newsletter's forms without JavaScript and its unsubscribe link rely on them.
      '/api/**': { proxy: { to: `${backendUrl}/api/**`, fetchOptions: { redirect: 'manual' } } },
      '/media/**': { proxy: `${backendUrl}/media/**` },
      '/documents/**': { proxy: `${backendUrl}/documents/**` },
    },
  },

  app: {
    head: {
      htmlAttrs: { lang: 'en' },
      // The old <body> also had "min-h-screen flex flex-col"; that lives on the layout root now.
      bodyAttrs: { class: 'bg-base-100' },
      // The old site's font links, unchanged.
      link: [
        { rel: 'preconnect', href: 'https://fonts.googleapis.com' },
        { rel: 'preconnect', href: 'https://fonts.gstatic.com', crossorigin: '' },
        {
          href: 'https://fonts.googleapis.com/css2?family=Hedvig+Letters+Serif:opsz,wght@12..24,400;12..24,500;12..24,700&family=Hedvig+Letters+Sans:wght@400;500;700&display=swap',
          rel: 'stylesheet',
        },
      ],
    },
  },
})
