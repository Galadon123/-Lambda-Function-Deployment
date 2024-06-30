const { NodeSDK } = require('@opentelemetry/sdk-node');
const { OTLPTraceExporter } = require('@opentelemetry/exporter-otlp-grpc');
const { getNodeAutoInstrumentations } = require('@opentelemetry/auto-instrumentations-node');
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

async function getEC2InstancePrivateIP(bucket, key) {
  const params = { Bucket: bucket, Key: key };
  const data = await s3.getObject(params).promise();
  const outputs = JSON.parse(data.Body.toString('utf-8'));
  return outputs.ec2_instance_private_ip; // Use the private IP
}

async function initializeOpenTelemetry() {
  const ec2InstancePrivateIP = await getEC2InstancePrivateIP('lambda-function-bucket-poridhi', 'pulumi-outputs.json');

  const traceExporter = new OTLPTraceExporter({
    url: `http://${ec2InstancePrivateIP}:4317`,
    credentials: grpc.credentials.createInsecure(),
  });

  const sdk = new NodeSDK({
    traceExporter,
    instrumentations: [getNodeAutoInstrumentations()],
  });

  await sdk.start();

  console.log('OpenTelemetry SDK initialized');
}

let otelInitialized = initializeOpenTelemetry();

app.get('/', (req, res) => {
  res.send('Hello, World!');
});

app.get('/trace', (req, res) => {
  res.send('This route is traced with OpenTelemetry!.');
  console.log('Trace route accessed');
});

exports.handler = async (event, context) => {
  await otelInitialized;
  return awsServerlessExpress.proxy(server, event, context);
};
