#!/bin/sh
# Inyecta variables de entorno en config.js para que el frontend las reciba
# sin necesidad de hardcodear valores en el código fuente.
set -e

CONFIG_FILE="/usr/share/nginx/html/config.js"

cat > "$CONFIG_FILE" << EOF
// Configuración generada automáticamente al arrancar el contenedor.
// NO edites este archivo directamente — modifica las variables de entorno en docker-compose.
window.APP_CONFIG = {
  apiGatewayUrl: "",                // vacío = usa rutas relativas (/api/...) via Nginx proxy
  defaultApiKey: "${API_GATEWAY_KEY:-change-me-before-going-to-production}",
};
EOF

echo "[frontend] config.js generado correctamente."
