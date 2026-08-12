/**
 * Handler do mock -- formato confirmado: é exatamente o que o Postman
 * Desktop gera automaticamente a partir dos exemplos de resposta salvos na
 * collection (um `if` por endpoint, casando method + regex do pathname).
 * Node puro, sem framework/dependência.
 *
 * Se você adicionar exemplos novos na collection e regenerar o mock pela
 * UI do Postman, este arquivo é sobrescrito -- edite os exemplos na
 * collection, não aqui, pra não perder a mudança na próxima regeneração.
 */
const http = require('http');
const PORT = process.env.PORT || 4500;

const server = http.createServer((req, res) => {
  const url = new URL(req.url || '', 'http://localhost');
  const pathname = url.pathname;

  // @endpoint GET /health
  if (req.method === 'GET' && pathname === '/health') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    return res.end(JSON.stringify({ status: 'ok' }));
  }

  res.writeHead(404, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify({ error: 'Endpoint not defined' }));
});

server.listen(PORT);
