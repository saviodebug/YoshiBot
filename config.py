import os

from dotenv import load_dotenv


load_dotenv()


DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")


# Canal do YouTube (yoshimta)
YOUTUBE_CHANNEL_ID = "UCoGzGUp3JhGsFLspSE69OXw"


# Canal do Discord que recebe os avisos (do youtube)
DISCORD_CHANNEL_ID = 1085662423299653684


# Cargo que recebe a notificação (notificacoes)
CARGO_NOTIFICACAO_ID = 1085662246732042329


# Cargo mencionado no embed de regras (cargo de membros)
CARGO_MEMBROS_ID = 1085662246732042328

ARMADILHA_CHANNEL_ID = 1539644765837197372


CANAIS_MIDIA_PERMITIDOS = {
    1085662261433094224,  # imagens-memes
    1085662358489268335,  # chat-fundadores
    1085662371982352545,  # anuncio
    1085662423299653684,  # divulgacao
}

# =========================================================
# LOGS
# =========================================================

# Automod / moderação

AUTOMOD_CHANNEL_ID = 1085662370489176084

# canal de logs
TICKET_LOG_CHANNEL_ID = 1085662359688839340

# Canal de logs de mensagens deletadas
LOG_DELETADOS_CHANNEL_ID = 1085662359688839340

# Canal de logs de voz
LOG_VOZ_CHANNEL_ID = 1085662359688839340

# Canal de logs de cargos e apelidos
LOG_MEMBROS_CHANNEL_ID = 1085662359688839340


# =========================================================
# BOAS-VINDAS
# =========================================================

# Canal onde aparece a mensagem de boas-vindas
WELCOME_CHANNEL_ID = 1085662402814672906

# Canal de regras
RULES_CHANNEL_ID = 1085662421613555813

# Canal onde o usuário escolhe cargos
CARGOS_CHANNEL_ID = 1085899683639070810

# =========================================================
# BANCO DE DADOS PELO DISCORD
# =========================================================

LOG_TICKETS_CHANNEL_ID = 1540015003439210516
LOG_INFRACOES_CHANNEL_ID = 1540015114676207626
LOG_BOOSTERS_CHANNEL_ID = 1540015178983149678
LOG_SISTEMA_CHANNEL_ID = 1540015246176030853
