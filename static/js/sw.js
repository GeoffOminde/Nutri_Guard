// Dummy Service Worker
self.addEventListener("install", () => {
  console.log("Service Worker installed.");
});

self.addEventListener("fetch", (event) => {
  // Just pass requests through
  return;
});
