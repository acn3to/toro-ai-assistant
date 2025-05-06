"""
Shared constants used throughout the project.
"""

STATUS_PENDING = "pending"
STATUS_PROCESSING = "processing"
STATUS_COMPLETED = "completed"
STATUS_ERROR = "error"

DEFAULT_TABLE_NAME = "toro-ai-assistant-questions"
DEFAULT_CONNECTIONS_TABLE = "toro-websocket-connections"
DEFAULT_PROCESS_TOPIC = "toro-ai-assistant-process-topic"
DEFAULT_NOTIFY_TOPIC = "toro-ai-assistant-notify-topic"

DEFAULT_INFERENCE_PROFILE_ID = "us.amazon.nova-pro-v1:0"
DEFAULT_MAX_TOKENS = 4096
DEFAULT_TEMPERATURE = 0.1
DEFAULT_TOP_P = 0.9
DEFAULT_VECTOR_SEARCH_RESULTS = 10

DEFAULT_PROMPT_TEMPLATE = (
    "Você é um assistente de investimentos da Toro especializado em responder "
    "perguntas usando SOMENTE as informações fornecidas no contexto abaixo. "
    "IMPORTANTE: Você NÃO deve usar seu conhecimento geral ou informações que "
    "não estejam explicitamente presentes nos documentos abaixo. "
    "Se os documentos não contiverem informações suficientes para responder à pergunta, "
    "você deve responder: 'Não tenho informações suficientes "
    "para responder a essa pergunta.' "
    "Suas respostas devem ser baseadas EXCLUSIVAMENTE no conteúdo dos documentos, "
    "sem adicionar conhecimento externo. "
    "\n\n"
    "INSTRUÇÕES DE FORMATAÇÃO:\n"
    "1. Quando apresentar listas ou enumerações, use quebras de linha entre os itens.\n"
    "2. Para listas numeradas, coloque cada número em uma nova linha, seguido do texto do item.\n"
    "3. Utilize marcadores (como • ou -) em nova linha para listas não numeradas.\n"
    "4. Destaque títulos e subtítulos em negrito usando ** (dois asteriscos).\n"
    "5. Mantenha sempre uma formatação clara e legível, com parágrafos bem definidos.\n\n"
    "CONTEXTO:"
    "\n$search_results$\n\n"
    "Pergunta: $query$\n\n"
    "Resposta (usando APENAS as informações do CONTEXTO acima e seguindo as instruções de formatação):"
)
