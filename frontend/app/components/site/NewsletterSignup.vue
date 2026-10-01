<script setup lang="ts">
// Old core/sections/newsletter-signup.html. The card/card-body classes are replaced by
// daisyUI's effective styles. Not connected to any service: submitting does nothing
// (the old form posted to "#" without a CSRF token and failed).
</script>

<template>
  <div class="relative flex flex-col rounded-box bg-gradient-to-br from-primary/5 to-secondary/5 border border-primary/10">
    <div class="flex flex-auto flex-col gap-2 p-6 text-[0.875rem] text-center items-center">
      <h3 class="text-2xl font-bold mb-2">Stay Updated</h3>
      <p class="grow text-base-content/70 mb-4">Get new posts delivered to your inbox</p>
      <form class="gap-4" method="post" action="#" @submit.prevent>
        <input
          type="email"
          name="email"
          placeholder="your@email.com"
          class="input w-full mb-4"
          required
          aria-label="Email address"
        >
        <button type="submit" class="btn btn-primary">Subscribe</button>
      </form>
    </div>
  </div>
</template>
