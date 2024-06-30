const { NodeSDK } = require('@opentelemetry/sdk-node');
const { OTLPTraceExporter } = require('@opentelemetry/exporter-otlp-grpc');
const { getNodeAutoInstrumentations } = require('@opentelemetry/auto-instrumentations-node');
const { trace, context } = require('@opentelemetry/api');
const grpc = require('@grpc/grpc-js');
const AWS = require('aws-sdk');
const express = require('express');
const awsServerlessExpress = require('aws-serverless-express');
const awsServerlessExpressMiddleware = require('aws-serverless-express/middleware');

const s3 = new AWS.S3();
const app = express();
const server = awsServerlessExpress.createServer(app);

app.use(express.json());
app.use(awsServerlessExpressMiddleware.eventContext());

let otelInitialized = false;

async function getEC2InstancePrivateIP(bucket, key) {
  const params = { Bucket: bucket, Key: key };
  const data = await s3.getObject(params).promise();
  const outputs = JSON.parse(data.Body.toString('utf-8'));
  return outputs.ec2_instance_private_ip; // Use the private IP of the EC2 instance
}

async function initializeOpenTelemetry() {
  if (!otelInitialized) {
    console.log("Initializing OpenTelemetry...");
    try {
      const ec2InstancePrivateIP = await getEC2InstancePrivateIP('lambda-function-bucket-poridhi', 'pulumi-outputs.json');
      console.log(`Fetched EC2 instance private IP: ${ec2InstancePrivateIP}`);

      const traceExporter = new OTLPTraceExporter({
        url: `http://${ec2InstancePrivateIP}:4317`,
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

initializeOpenTelemetry(); // Start the initialization on cold start

app.get('/', (req, res) => {
  const currentSpan = trace.getTracer('default').startSpan('GET /');
  context.with(trace.setSpan(context.active(), currentSpan), () => {
    const traceId = currentSpan.spanContext().traceId;
    console.log(`Trace ID for GET /: ${traceId}`);
    res.send('Hello, World!');
    currentSpan.end();
  });
});

app.get('/trace', (req, res) => {
  const currentSpan = trace.getTracer('default').startSpan('GET /trace');
  context.with(trace.setSpan(context.active(), currentSpan), () => {
    const traceId = currentSpan.spanContext().traceId;
    console.log(`Trace ID for GET /trace: ${traceId}`);
    res.send('This route is traced with OpenTelemetry!');
    console.log('Trace route accessed');
    currentSpan.end();
  });
});

exports.handler = (event, context) => {
  console.log("Handler invoked");
  return awsServerlessExpress.proxy(server, event, context, 'PROMISE').promise;
};
