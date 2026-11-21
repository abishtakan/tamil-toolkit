import { registerSW } from 'virtual:pwa-register';

export function registerPwa() {
  if (typeof window === 'undefined' || !('serviceWorker' in navigator)) return;

  if (import.meta.env.DEV) {
    navigator.serviceWorker
      .getRegistrations()
      .then((registrations) => Promise.all(registrations.map((reg) => reg.unregister())))
      .catch(() => {});
    return;
  }

  registerSW({
    immediate: true,
    onRegisteredSW(_swUrl, registration) {
      if (registration) {
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
