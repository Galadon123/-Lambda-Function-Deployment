## EC2 Instance Setup for Grafana, Tempo, and OpenTelemetry Collector

### Step 1: Connect to EC2 Instance using AWS Console
1. Launch an EC2 instance with the following specifications:
    - **AMI**: Ubuntu 20.04 LTS
    - **Instance Type**: t2.micro (or larger if needed)
    - **Subnet**: Public Subnet (10.0.1.0/24)
    - **Security Group**: 
        - Allow inbound traffic on ports 22 (SSH), 3000 (Grafana), 3200 (Tempo), 4317 (OTLP gRPC), 4318 (OTLP HTTP)
2. Use the AWS Management Console to connect to the EC2 instance:
    - Open the EC2 console at https://console.aws.amazon.com/ec2/.
    - In the navigation pane, choose **Instances**.
    - Select the instance and choose **Connect**.
    - Follow the instructions to connect to your instance using the EC2 Instance Connect method.

### Step 2: Install Docker
1. Update packages and install Docker:
    ```sh
    sudo apt-get update -y
    sudo apt-get install -y docker.io
    sudo systemctl start docker
    sudo systemctl enable docker
    sudo usermod -aG docker ubuntu
    ```

### Step 3: Install Docker Compose
1. Install Docker Compose:
    ```sh
    sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    ```

### Step 4: Set Up Directory Structure
1. Create a directory for your setup:
    ```sh
    mkdir ~/grafana-tempo-otel
    cd ~/grafana-tempo-otel
    ```

### Step 5: Create Configuration Files

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

processors:
  batch:

exporters:
  otlp:
    endpoint: "tempo:4317"
    tls:
      insecure: true

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [otlp]
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

### Step 6: Start Services
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

## Grafana Setup for Traces with Tempo

### Step 1: Access Grafana
1. Open a web browser and navigate to `http://<ec2_instance_public_ip>:3000`.
2. Log in with the default credentials:
    - **Username**: admin
    - **Password**: admin

### Step 2: Add Tempo Data Source
1. In the Grafana UI, go to **Configuration** (gear icon) > **Data Sources**.
2. Click on **Add data source**.
3. Select **Tempo** from the list of available data sources.

### Step 3: Configure Tempo Data Source
1. Set the **HTTP URL** to `http://tempo:3200`.
2. Click **Save & Test** to ensure the connection to Tempo is successful.

### Step 4: Create a Dashboard
1. Go to **Create** (plus icon) > **Dashboard**.
2. Click on **Add new panel**.

### Step 5: Query Traces
1. In the query editor, select the Tempo data source.
2. Use TraceQL to query the traces. For example:
    ```traceql
    {}
    ```
3. Adjust the query as needed to visualize the trace data.

### Step 6: Save Dashboard
1. Click **Apply** to save the panel.
2. Click **Save Dashboard** to save the dashboard with a meaningful name.


By following these steps, you can set up an EC2 instance to host Grafana, Tempo, and the OpenTelemetry Collector, enabling you to visualize and analyze trace data generated by your application.