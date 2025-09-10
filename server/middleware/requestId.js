const { randomUUID } = require('crypto');

const requestIdHeaderName = 'x-request-id';

function requestIdMiddleware(req, res, next) {
  const incomingId = req.header(requestIdHeaderName);
  req.id = incomingId || randomUUID();
  res.setHeader(requestIdHeaderName, req.id);
  next();
}

module.exports = { requestIdMiddleware, requestIdHeaderName };

