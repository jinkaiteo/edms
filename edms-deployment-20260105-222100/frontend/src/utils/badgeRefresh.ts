/**
 * Global badge refresh utility
 * Simple alternative to context - uses window events
 */

export const triggerBadgeRefresh = () => {
  // Trigger custom event that Layout component listens to
  const event = new CustomEvent('badgeRefresh');
  window.dispatchEvent(event);
  console.log('🔄 Badge refresh triggered via global event');
};