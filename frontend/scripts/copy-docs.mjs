import { copyFile, mkdir } from "node:fs/promises";
await mkdir("dist/api-docs", { recursive: true });
for (const name of ["swagger-ui-bundle.js", "swagger-ui.css"])
  await copyFile(
    "node_modules/swagger-ui-dist/" + name,
    "dist/api-docs/" + name,
  );
