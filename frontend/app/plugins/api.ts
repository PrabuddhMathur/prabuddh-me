// $api: $fetch for the backend. The Nuxt server calls Wagtail directly (NUXT_BACKEND_URL);
// the browser calls same-origin /api/… (Caddy in production, the dev proxy in development).
export default defineNuxtPlugin(() => {
  const config = useRuntimeConfig()
  const api = $fetch.create({
    baseURL: import.meta.server ? config.backendUrl : '',
  })
  return { provide: { api } }
})
