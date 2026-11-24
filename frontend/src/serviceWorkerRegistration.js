// Registro del Service Worker para soporte PWA
export function register() {
  if ('serviceWorker' in navigator && (window.location.protocol === 'https:' || window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')) {
    window.addEventListener('load', () => {
      const swUrl = `${process.env.PUBLIC_URL || ''}/service-worker.js`;
      navigator.serviceWorker
        .register(swUrl)
        .then((registration) => {
          console.log('ServiceWorker registrado exitosamente con scope:', registration.scope);
        })
        .catch((error) => {
          console.warn('Error durante el registro del ServiceWorker:', error);
        });
    });
  }
}

export function unregister() {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.ready
      .then((registration) => {
        registration.unregister();
      })
      .catch((error) => {
        console.error(error.message);
      });
  }
}
