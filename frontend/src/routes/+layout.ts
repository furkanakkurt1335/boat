// Disable SSR — required for adapter-static + Tauri.
// The app is already 100% client-rendered (no +page.server.ts anywhere),
// so this only makes the constraint explicit.
export const ssr = false;
export const prerender = false;
