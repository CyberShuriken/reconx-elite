// Parcel only inlines frontend environment variables when the property name is
// statically visible. Keep the supported keys explicit so production builds get
// the deployed values while Jest can still override process.env.
const frontendEnv = {
  VITE_API_URL: process.env.VITE_API_URL || "",
  VITE_API_BASE_URL: process.env.VITE_API_BASE_URL || "",
  VITE_WS_URL: process.env.VITE_WS_URL || "",
};

export function readFrontendEnv(key) {
  return frontendEnv[key] || "";
}

export function firstFrontendEnv(...keys) {
  for (const key of keys) {
    const value = readFrontendEnv(key);
    if (value) {
      return value;
    }
  }
  return "";
}
