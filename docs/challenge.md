# 0.1 Desafio Técnico - Assistente IA Toro

## Objetivo

Criar uma aplicação backend simples que permita a um usuário enviar perguntas e receber respostas de uma IA. As perguntas e respostas devem ser armazenadas e os usuários notificados sobre as respostas.

## Descrição do Desafio

Você deve desenvolver um sistema composto por um back-end (serverless), integrações com a AWS e aplicação de boas práticas de Clean Code.

## Backend: Arquitetura Serverless

A aplicação deve utilizar **AWS Lambda**, **SNS** e **DynamoDB** para criar um fluxo de processamento assíncrono:

1. **Recepção e Registro (Lambda + API Gateway)**
   - Expor endpoints (REST ou GraphQL) para receber perguntas
   - Registrar a pergunta no DynamoDB com status "pendente"
   - Acionar um tópico SNS para processamento assíncrono

2. **Processamento (Lambda + SNS)**
   - Lambda inscrito no tópico SNS deve consumir a pergunta
   - Consultar uma API de IA (AWS Bedrock, OpenAI, HuggingFace, etc.)
   - Salvar resposta no DynamoDB, alterando status para "respondido"
   - Publicar notificação no SNS informando que a resposta está disponível

3. **Notificação (Lambda + SNS)**
   - Sempre que uma pergunta for respondida, enviar notificação via SNS
   - Lambda responsável por alertar o usuário (pode ser apenas um log ou mensagem simples)

4. **Armazenamento (DynamoDB)**
   - Utilizar uma tabela para guardar perguntas, respostas, id do usuário e status

## Frontend: Interface Simples

Uma interface web simples para que o usuário:

1. **Faça login** (autenticação simulada, não precisa ser real)
2. **Envie perguntas**
3. **Visualize o histórico** de perguntas e respostas
4. **Veja notificações** de que sua resposta chegou

**Importante sobre o frontend**:
- Não é necessário implementar estilo ou preocupar com a UI/UX
- Não é obrigatório utilizar framework e pode ser feito utilizando JS e HTML puro
- O frontend deve consumir as respostas em tempo real (pode ser polling simples)

## Clean Code

Seu código deve:
- Ser limpo e organizado
- Ter funções e componentes pequenos, coesos e bem nomeados
- Incluir documentação de decisões de arquitetura e instruções para execução
- Fornecer pelo menos um teste unitário por função principal

## Requisitos para Entrega

- Repositório no Github com instruções de setup e README explicativo
- Documentação descrevendo como suas decisões valorizam Clean Code e escalabilidade

## Pontos Extras

1. **Tecnologias**
   - Utilizar TypeScript ou Python no back-end
   - Utilizar AWS CDK ou Serverless Framework para provisionamento da infraestrutura

2. **Documentação e Deploy**
   - Documentar propostas de melhorias para escalabilidade
   - Disponibilizar deploy demonstrável (pode ser em sandbox/pessoal)

---

<div align="center">
  <a href="../README.md">
    <img src="https://img.shields.io/badge/⬅️_Back_to_Home-0A66C2?style=for-the-badge" alt="Back to Home"/>
  </a>
</div>
