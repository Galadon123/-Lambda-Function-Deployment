## EC2 Instance Setup for Grafana, Tempo, and OpenTelemetry Collector

### Step 1: Launch EC2 Instance
1. Launch an EC2 instance with the following specifications:
    - **AMI**: Ubuntu 20.04 LTS
    - **Instance Type**: t2.micro (or larger if needed)
    - **Subnet**: Public Subnet (10.0.1.0/24)
    - **Security Group**: 
        - Allow inbound traffic on ports 22 (SSH), 3000 (Grafana), 3200 (Tempo), 4317 (OTLP gRPC), 4318 (OTLP HTTP)

### Step 2: Connect to EC2 Instance
1. SSH into your EC2 instance:
    ```sh
    ssh -i /path/to/your-key.pem ubuntu@<ec2_instance_public_ip>
    ```

### Step 3: Install Docker
1. Update packages and install Docker:
    ```sh
    sudo apt-get update -y
    sudo apt-get install -y docker.io
    sudo systemctl start docker
    sudo systemctl enable docker
    sudo usermod -aG docker ubuntu
    ```

### Step 4: Install Docker Compose
1. Install Docker Compose:
    ```sh
    sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    ```

### Step 5: Set Up Directory Structure
1. Create a directory for your setup:
    ```sh
    mkdir ~/grafana-tempo-otel
    cd ~/grafana-tempo-otel
    ```

### Step 6: Create Configuration Files

#### `tempo.yaml`
Create `tempo.yaml` with the following content:
```yaml
auth_enabled: false

server:
  http_listen_port: 3200

ingester:
  trace_idle_period: 30s
  max_block_bytes: 5000000
  max_block_duration: 5m

storage:
  trace:
    backend: local
    local:
      path: /tmp/tempo/traces

compactor:
  compaction:
    block_retention: 48h

querier:
  frontend_worker:
    frontend_address: 127.0.0.1:9095
```

#### `otel-collector-config.yaml`
Create `otel-collector-config.yaml` with the following content:
```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: "0.0.0.0:4317"
      http:
        endpoint: "0.0.0.0:4318"

exporters:
  logging:
    loglevel: debug
  otlp:
    endpoint: "tempo:4317"  # Send traces to Tempo

service:
  pipelines:
    traces:
      receivers: [otlp]
      exporters: [logging, otlp]
```

#### `docker-compose.yml`
Create `docker-compose.yml` with the following content:
```yaml
version: '3'

services:
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin

  tempo:
    image: grafana/tempo:latest
    ports:
      - "3200:3200"
    command: ["tempo", "serve", "--config.file=/etc/tempo.yaml"]
    volumes:
      - ./tempo.yaml:/etc/tempo.yaml

  otel-collector:
    image: otel/opentelemetry-collector:latest
    command: ["--config=/etc/otel-collector-config.yaml"]
    volumes:
      - ./otel-collector-config.yaml:/etc/otel-collector-config.yaml
    ports:
      - "4317:4317"  # Expose the OTLP gRPC endpoint
      - "4318:4318"  # Expose the OTLP HTTP endpoint
```

### Step 7: Start Services
1. Navigate to the directory where you created the files and start the services using Docker Compose:
    ```sh
    cd ~/grafana-tempo-otel
    sudo docker-compose up -d
    ```

## Example Scenario: Trace Data Flow

1. **Application (Lambda Function)**:
    - Your application generates trace data and sends it to the OpenTelemetry Collector endpoint (`http://${ec2InstancePrivateIP}:4317`).

2. **OpenTelemetry Collector**:
    - The Collector receives the traces via the OTLP receiver.
    - The traces pass through the processing pipeline.
    - The `logging` exporter logs the trace data for debugging.
    - The `otlp` exporter sends the trace data to Tempo.

3. **Grafana Tempo**:
    - Tempo receives the trace data on its gRPC endpoint (`tempo:4317`).
    - Tempo processes and stores the traces in `/tmp/tempo/traces`.

4. **Grafana**:
    - Grafana queries Tempo to retrieve the stored trace data.
    - The traces are visualized in Grafana’s user interface, allowing you to analyze them.

api test:

```json
{
  "httpMethod": "GET",
  "path": "/",
  "headers": {
    "Content-Type": "application/json"
  },
  "body": null,
  "isBase64Encoded": false
}
```