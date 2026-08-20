# YoshiBot

YoshiBot é um bot de automação e administração para Discord desenvolvido em Python com discord.py, criado para gerenciar uma comunidade real e atualmente executado 24/7 em ambiente cloud.

Este projeto foi desenvolvido por mim como uma solução prática para administração, atendimento, moderação e automações do servidor Yoshizinho City.

**Testar no Discord:** https://discord.gg/2AHxXhb8Sh

## Projeto em produção

O bot está atualmente em funcionamento em um servidor real de Discord e hospedado 24/7 na Discloud.

**Testar no Discord:** https://discord.gg/2AHxXhb8Sh

## Funcionalidades

- Sistema de tickets com categorias para dúvida, sorteio, denúncia e tag criador
- Modal/formulário antes da abertura de tickets que exigem resumo
- Tickets numerados com contador persistente
- Transcript automático antes do fechamento de tickets
- Histórico e logs de tickets
- Sistema de infrações com registro em canal privado do Discord
- Anti-spam com detecção de flood, mensagens repetidas, excesso de menções, convites de Discord e links suspeitos
- Sistema progressivo de punições com aviso, timeout e expulsão
- Cargo automático para novos membros
- Mensagem de boas-vindas
- Logs de entrada e saída de membros
- Sistema automático de Booster com cargo especial e logs
- Sistema de cargos por reação
- Painel de ajuda baseado no nível/cargo do usuário
- Sistema de permissões para comandos administrativos e consultas de staff
- Canal armadilha/honeypot com expulsão automática
- Controle de envio de mídia por canal
- Monitoramento automático de YouTube via YouTube Data API v3
- Notificação de vídeos e lives
- Sistema de logs
- Estatísticas e status operacional do bot
- Comandos administrativos e consultas de histórico
- Persistência de estado e registros usando canais privados do Discord
- Deploy 24/7 na Discloud

## Comandos

| Comando | Acesso | Descrição |
|---------|--------|-----------|
| `!ajuda` | Todos | Exibe a central de ajuda, adaptada ao cargo/nível do usuário. Também disponível como `!help` e `!comandos`. |
| `!regras` | Todos | Publica o painel de regras do servidor. |
| `!divulgacao` | Todos | Publica informações sobre divulgação e solicitação da tag Creator. |
| `!cargos` | Todos | Publica o painel de escolha de cargos por reação. |
| `!ticket` | Administração | Publica a Central de Atendimento com seleção de categoria de ticket. Requer permissão `Gerenciar servidor`. |
| `!armadilha` | Administração | Publica o aviso/configuração do canal armadilha. Requer permissão `Gerenciar servidor`. |
| `!status` | Administração | Mostra ping, módulos carregados, status do monitor do YouTube, tickets abertos e uptime. Requer permissão `Gerenciar servidor`. |
| `!ticketinfo <id>` | Staff/Admin | Consulta informações de um ticket específico no histórico. |
| `!tickets <membro>` | Staff/Admin | Lista tickets registrados de um membro. |
| `!infracoes <membro>` | Staff/Admin | Lista infrações registradas de um membro. |
| `!historico <membro>` | Staff/Admin | Mostra um resumo de tickets, infrações, booster e datas do membro. |
| `!stats` | Staff/Admin | Exibe estatísticas gerais do servidor e dos sistemas do bot. |
| `!testvideo` | Testes/desenvolvimento | Dispara manualmente uma notificação de vídeo usando o último vídeo encontrado no YouTube. |
| `!testlive` | Testes/desenvolvimento | Dispara manualmente uma notificação de live usando o último vídeo encontrado no YouTube. |

## Arquitetura

O projeto utiliza uma arquitetura modular baseada em Cogs do discord.py. Cada módulo concentra uma área funcional do bot, enquanto `main.py` inicializa o cliente, configura intents e carrega os Cogs.

```text
YoshiBot/
├── main.py
├── config.py
├── requirements.txt
├── discloud.config
├── cogs/
│   ├── ajuda.py
│   ├── antispam.py
│   ├── armadilha.py
│   ├── booster.py
│   ├── cargos.py
│   ├── consultas.py
│   ├── entradaEsaida.py
│   ├── erros.py
│   ├── informacoes.py
│   ├── midia.py
│   ├── status.py
│   ├── ticket.py
│   └── youtube.py
├── utils/
│   ├── discord_db.py
│   ├── logs.py
│   └── transcript.py
├── img/
│   └── yoshi_overlay_fade.gif
└── docs/
    └── screenshots/
```

## Tecnologias

- Python
- discord.py
- asyncio
- aiohttp
- python-dotenv
- YouTube Data API v3
- Discloud
- Git/GitHub

## Destaques técnicos

- Arquitetura modular baseada em Cogs, separando tickets, moderação, YouTube, cargos, logs e consultas.
- Programação assíncrona com `async`/`await` para lidar com eventos do Discord e chamadas externas.
- Consumo da YouTube Data API v3 com `aiohttp` para monitoramento automático de vídeos e lives.
- Gerenciamento de eventos do Discord como entrada/saída de membros, reações, mensagens e atualização de booster.
- Controle de permissões para comandos administrativos e consultas de staff.
- Uso de Views persistentes, Buttons, Selects e Modals no sistema de tickets.
- Automações de moderação com registro de infrações e punições progressivas.
- Geração automática de transcripts antes do fechamento de tickets.
- Tratamento centralizado de erros de comandos com envio de logs.
- Persistência de contador e registros utilizando canais privados do próprio Discord.
- Deploy em produção 24/7 na Discloud.

## Screenshots

A pasta `docs/screenshots/` está preparada para imagens do projeto. Não há screenshots públicos adicionados neste repositório para evitar exposição acidental de tokens, dados privados de usuários ou conteúdo sensível de tickets.

Sugestões de screenshots para adicionar depois:

- Central de tickets
- Ticket aberto
- Modal de abertura
- Logs
- `!ajuda`
- `!status`
- `!stats`
- Painel da Discloud mostrando o bot online

Antes de adicionar imagens, verifique se elas não exibem tokens, `.env`, API keys, informações privadas de usuários ou conteúdo privado de denúncias/tickets.

## Configuração local

1. Instale as dependências:

```bash
pip install -r requirements.txt
```

2. Crie um arquivo `.env` local com base em `.env.example`:

```env
DISCORD_TOKEN=
YOUTUBE_API_KEY=
```

3. Execute o bot:

```bash
python main.py
```

## Variáveis de ambiente

| Variável | Descrição |
|----------|-----------|
| `DISCORD_TOKEN` | Token do bot no Discord. |
| `YOUTUBE_API_KEY` | Chave da YouTube Data API v3 usada pelo monitor de vídeos e lives. |

## Segurança

Este repositório não deve incluir `.env`, tokens, chaves de API, senhas, cookies, credenciais ou arquivos privados. IDs públicos de canais, cargos e servidor do Discord foram mantidos no código porque fazem parte da configuração operacional do bot.

## Licença

Este projeto está licenciado sob a licença MIT. Consulte o arquivo `LICENSE`.
