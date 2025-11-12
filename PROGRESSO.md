# PROGRESSO - Ai Infinitus Transcript

## Mudanças neste ciclo
- Adicionada função `gerar_conteudo_social(transcricao, plataforma, tom, tamanho_legenda, qtd_hashtags)` em `app.py`.
- Integração automática após a transcrição nas abas:
  - **Áudio**: gera e exibe Título, Legenda e Hashtags assim que a transcrição conclui.
  - **Vídeo**: após extrair áudio e transcrever, gera e exibe Título, Legenda e Hashtags.
- Mantido o fluxo existente de UI, spinners e mensagens; nenhuma funcionalidade anterior foi alterada.

## Como usar (Windows, PowerShell)
1. Criar e ativar ambiente virtual:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
2. Instalar dependências:
   ```powershell
   pip install -r requirements.txt
   ```
3. Configurar variáveis de ambiente no arquivo `.env` (raiz do projeto):
   ```ini
   OPENAI_API_KEY=coloque_sua_chave_aqui
   # Opcional: trocar o modelo usado na geração de conteúdo social
   OPENAI_CONTENT_MODEL=gpt-4o-mini
   ```
4. Executar o app:
   ```powershell
   streamlit run app.py
   ```
5. Requisitos adicionais:
   - Para a aba **Vídeo**, é necessário ter **FFmpeg** instalado e disponível no PATH do sistema.

## Detalhes da geração de conteúdo social
- Idioma: pt-BR.
- Parâmetros padrão:
  - `plataforma`: Instagram
  - `tom`: engajador
  - `tamanho_legenda`: média
  - `qtd_hashtags`: 15 (mín. efetivo 10, máx. 30)
- Sanitização:
  - Transcrição truncada em ~8000 caracteres para otimizar custo/latência.
  - Hashtags normalizadas (sem espaços, com prefixo `#`, remoção de duplicatas).
- Fallbacks:
  - `Título sugerido` / `Legenda sugerida.` quando necessário.
- Modelo usado na geração: `OPENAI_CONTENT_MODEL` (default `gpt-4o-mini`).

## Próximos passos (planejados)
- Adicionar controles de UI para plataforma, tom, tamanho da legenda e quantidade de hashtags, além do botão "Regenerar".
- Adicionar botões de copiar e download `.txt` para o conteúdo gerado.

## Changelog
- 2025-11-12: Função de geração de conteúdo social criada e integrada nas abas Áudio e Vídeo.
