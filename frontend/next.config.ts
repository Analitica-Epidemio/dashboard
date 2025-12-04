import type { NextConfig } from "next";

// Import env validation at build time
import "./src/env";

const nextConfig: NextConfig = {
  // Genera build standalone para Docker (imagen más pequeña)
  output: "standalone",
};

export default nextConfig;
