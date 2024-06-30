const { NodeSDK } = require('@opentelemetry/sdk-node');
const { OTLPTraceExporter } = require('@opentelemetry/exporter-otlp-grpc');
const { getNodeAutoInstrumentations } = require('@opentelemetry/auto-instrumentations-node');
const grpc = require('@grpc/grpc-js');
const AWS = require('aws-sdk');
const express = require('express');
const awsServerlessExpress = require('aws-serverless-express');

const s3 = new AWS.S3();
const app = express();

app.use(express.json());

async function getEC2InstanceIP(bucket, key) {
  const params = { Bucket: bucket, Key: key };
  const data = await s3.getObject(params).promise();
  const outputs = JSON.parse(data.Body.toString('utf-8'));
  return outputs.ec2_instance_ip;
}

async function initializeOpenTelemetry() {
  const ec2InstanceIP = await getEC2InstanceIP('lambda-function-bucket-poridhi', 'pulumi-outputs.json');

  const traceExporter = new OTLPTraceExporter({
    url: `http://${ec2InstanceIP}:4317`,
    credentials: grpc.credentials.createInsecure(),
  });

  const sdk = new NodeSDK({
    traceExporter,
    instrumentations: [getNodeAutoInstrumentations()],
  });

  sdk.start();
}

initializeOpenTelemetry();

app.get('/', (req, res) => {
  res.send('Hello, World!');
});

app.get('/trace', (req, res) => {
  res.send('This route is traced with OpenTelemetry.');
});

const server = awsServerlessExpress.createServer(app);

exports.handler = (event, context) => {
  awsServerlessExpress.proxy(server, event, context);
};
