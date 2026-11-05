import { registerSW } from 'virtual:pwa-register';

export function registerPwa() {
  if (typeof window !== 'undefined' && 'serviceWorker' in navigator) {
    registerSW({
      immediate: true,
      onRegisteredSW(_swUrl, registration) {
        if (registration) {
          // Check for service worker updates periodically (every 1 hour)
          setInterval(() => {
            registration.update().catch(() => {});
          }, 60 * 60 * 1000);
        }
      },
      onRegisterError(error) {
        console.warn('PWA service worker registration note:', error);
      }
    });
  }
}
