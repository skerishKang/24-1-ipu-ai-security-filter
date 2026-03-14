const DEFAULT_CONFIG = {
  apiBaseUrl: "http://127.0.0.1:8241",
};

export function getRuntimeConfig() {
  const runtimeConfig = window.IPU_RUNTIME_CONFIG ?? {};
  return {
    ...DEFAULT_CONFIG,
    ...runtimeConfig,
  };
}

export function getManualPreviewUrl() {
  const config = getRuntimeConfig();
  return `${config.apiBaseUrl}/api/v1/mode/manual-preview`;
}

export function getManualPreviewFileUrl() {
  return `${getManualPreviewUrl()}/file`;
}
