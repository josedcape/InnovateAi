#!/bin/bash

# Listar todos los archivos Python
echo "==== ARCHIVOS PYTHON ===="
find . -type f -name "*.py" -not -path "*/\.*" | sort

# Listar archivos HTML y JavaScript en templates y static
echo -e "\n==== ARCHIVOS HTML ===="
find ./templates -type f -name "*.html" | sort

echo -e "\n==== ARCHIVOS JavaScript ===="
find ./static -type f -name "*.js" | sort

echo -e "\n==== ARCHIVOS CSS ===="
find ./static -type f -name "*.css" | sort

echo -e "\n==== OTROS ARCHIVOS IMPORTANTES ===="
find . -name "*.md" -o -name "*.txt" -o -name "*.json" -o -name "*.toml" | grep -v node_modules | sort