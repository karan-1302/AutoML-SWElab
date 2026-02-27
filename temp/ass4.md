# Assignment 4: Software Architecture for Real Estate AutoML System

## I. Chosen Software Architecture Style
For the Real Estate AutoML System, the most appropriate choice is an **Event-Driven Microservices Architecture**.



### A. Justification by Granularity of Software Components
The architecture falls into this category because the system is decomposed into fine-grained, loosely coupled services based on specific domains, using asynchronous events to coordinate heavy tasks:
* **API Gateway Component:** Extremely lightweight granularity; strictly handles routing, rate limiting, and authenticating requests (using the `AuthManager` class) without executing business logic.
* **Synchronous Microservices:** Fine-grained services like the **Prediction Service** and **Explainability Service** that require low latency and immediate request/response cycles.
* **Asynchronous Microservices:** Compute-heavy services like the **Ingestion Service** and **AutoML Training Service** that are decoupled from the user interface via an Event Bus, processing jobs in the background.

### B. Justification for Best Choice
This architectural style is the optimal choice for the AutoML platform due to the following reasons:
* **Scalability:** The *AutoML Training Service* requires massive CPU/RAM utilization, while the *Web Dashboard* is lightweight. Microservices allow us to independently scale the training workers horizontally without over-provisioning the entire system.
* **Performance:** By introducing an Event Bus (e.g., Kafka or RabbitMQ), long-running tasks like model training run asynchronously. The user receives immediate UI feedback while the heavy processing happens in the background.
* **Maintainability:** Data scientists can update complex ML libraries (scikit-learn, SHAP) in the *Training* or *Explainer* services without risking regressions in the frontend or authentication codebases.
* **Fault Tolerance:** If a corrupted dataset crashes the *Data Processing Service*, the decoupled *Prediction Service* remains 100% operational. Additionally, using resilient object storage ensures no raw data is lost during a failure.

---

## II. Application Components Present in the Software

Based on the system's logical design and infrastructure needs, the software consists of the following application components:

### 1. Client & API Layer
* **Web Dashboard (Frontend):** A responsive UI for real estate professionals to upload `.csv` files, view progress, and read prediction explanation reports.
* **API Gateway (NGINX/Kong):** The single entry point that manages user sessions, secures endpoints, and routes incoming REST/GraphQL requests to the appropriate backend microservices.

### 2. Core Microservices (Business Logic)
* **Data Ingestion & Preprocessing Service:** Validates the uploaded `.csv` datasets, standardizes missing values/encoding, streams the raw data into cloud storage, and publishes a "DataReady" event.
* **AutoML Engine (Training Service):** The core AI orchestrator. It listens for training events, pulls the clean data, iterates through algorithms (Regression/Classification), and calculates performance metrics (RMSE/R²).
* **Prediction Service:** A highly available, low-latency API that retrieves the best trained model and serves instant property price predictions based on new user inputs.
* **Explainability Service:** A dedicated mathematical service that applies SHAP/LIME algorithms to prediction outputs, generating human-readable decision support summaries.

### 3. Data Storage & Communication Layer
* **Message Queue / Event Bus (RabbitMQ/Kafka):** The asynchronous backbone that decouples services, passing tasks from the API Gateway to the background worker services.
* **Raw Data Store (AWS S3 / MinIO):** Secure, scalable object storage for persisting the raw datasets uploaded by users to ensure fault tolerance.
* **Metadata Database (PostgreSQL):** A relational database tracking user profiles, system state, and training job logs.
* **Model Registry (MLflow):** A specialized storage component that handles the serialization, versioning, and retrieval of the trained `.pkl` or `.joblib` machine learning models.