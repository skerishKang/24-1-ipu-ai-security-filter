export function createSessionId() {
  const time = new Date().toISOString().replaceAll(/[-:.TZ]/g, "").slice(0, 14);
  const random = Math.random().toString(36).slice(2, 8);
  return `ipu-${time}-${random}`;
}
