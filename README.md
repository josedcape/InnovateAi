# INNOVATE AI

Una plataforma avanzada de desarrollo de IA conversacional que integra tecnologías de voz de vanguardia, capacidades de OpenAI y funciones de asistente inteligente para flujos de trabajo de desarrollo de software y marketing.

## Características

- **Interfaz conversacional con avatar animado**: Interactúa con un asistente de IA que sincroniza sus respuestas de voz con un avatar de video para una experiencia más humana.
- **Síntesis de voz avanzada**: Utiliza Google Cloud Text-to-Speech para generar respuestas de voz naturales.
- **Múltiples agentes especializados**:
  - **Asistente principal**: Para consultas generales utilizando GPT-4o
  - **Búsqueda web**: Accede a información actualizada de Internet usando GPT-4o-search-preview
  - **Navegación autónoma**: Observa cómo la IA navega de forma autónoma usando el modelo computer-use-preview
  - **Búsqueda de archivos**: Consulta documentos subidos utilizando OpenAI vector store
- **Interfaz multilingüe**: Soporte para múltiples idiomas, con enfoque en español e inglés.
- **Reconocimiento de voz**: Conversaciones bidireccionales con capacidades de escucha activa.

## Tecnologías

- Python 3
- Flask + SQLAlchemy
- OpenAI SDK (GPT-4o, GPT-4o-search-preview, computer-use-preview)
- Google Cloud Text-to-Speech
- JavaScript para frontend interactivo
- HTML5 y CSS3 con diseño web responsivo
- Base de datos PostgreSQL

## Instalación

1. Clona este repositorio
2. Instala las dependencias: `pip install -r requirements.txt`
3. Configura las variables de entorno necesarias (ver `.env.example`)
4. Ejecuta la aplicación: `python main.py`

## Configuración de API Keys

La aplicación requiere las siguientes claves de API:
- `OPENAI_API_KEY`: Para acceder a los modelos de OpenAI
- `GOOGLE_API_KEY`: Para la síntesis de voz de Google (opcional, hay un fallback a gTTS)

## Licencia

Copyright © 2025 InnovateAI