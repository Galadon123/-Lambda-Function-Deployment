const { NodeSDK } = require('@opentelemetry/sdk-node');
const { OTLPTraceExporter } = require('@opentelemetry/exporter-otlp-grpc');
const { getNodeAutoInstrumentations } = require('@opentelemetry/auto-instrumentations-node');
const { trace, context } = require('@opentelemetry/api');
const grpc = require('@grpc/grpc-js');
const express = require('express');
const awsServerlessExpress = require('aws-serverless-express');
const awsServerlessExpressMiddleware = require('aws-serverless-express/middleware');

const app = express();
const server = awsServerlessExpress.createServer(app);

app.use(express.json());
app.use(awsServerlessExpressMiddleware.eventContext());

let otelInitialized = false;

async function initializeOpenTelemetry() {
  if (!otelInitialized) {
    console.log("Initializing OpenTelemetry...");
    try {
      const traceExporter = new OTLPTraceExporter({
        url: 'http://localhost:4317',  // Replace with your collector's URL
        credentials: grpc.credentials.createInsecure(),
      });

      const sdk = new NodeSDK({
        traceExporter,
        instrumentations: [getNodeAutoInstrumentations()],
      });

      await sdk.start();
      otelInitialized = true;
      console.log('OpenTelemetry SDK initialized');
    } catch (error) {
      console.error("Error initializing OpenTelemetry:", error);
    }
  }
}

// Initialize OpenTelemetry outside the handler to ensure it runs on cold start
initializeOpenTelemetry();

app.get('/', (req, res) => {
  const currentSpan = trace.getTracer('default').startSpan('GET /');
  context.with(trace.setSpan(context.active(), currentSpan), () => {
    const traceId = currentSpan.spanContext().traceId;
    console.log(`Trace ID for GET /: ${traceId}`);
    res.send(`Hello, World! Trace ID: ${traceId}`);
    currentSpan.end();
  });
});

app.get('/trace', (req, res) => {
  const currentSpan = trace.getTracer('default').startSpan('GET /trace');
  context.with(trace.setSpan(context.active(), currentSpan), () => {
    const traceId = currentSpan.spanContext().traceId;
    console.log(`Trace ID for GET /trace: ${traceId}`);
    res.send(`This route is traced with OpenTelemetry! Trace ID: ${traceId}`);
    console.log('Trace route accessed');
    currentSpan.end();
  });
});

exports.handler = (event, context) => {
  console.log("Handler invoked");
  return awsServerlessExpress.proxy(server, event, context, 'PROMISE').promise;
};
