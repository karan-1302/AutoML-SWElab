# Assignment 5: Deployment & Interaction Architecture



## I. Hosting Application Components

### 1. Host Sites 
To optimize compute resources and ensure a responsive user experience, the system utilizes a **Hybrid Compute and Composable Cloud Architecture**. The application components are distributed across specialized managed platforms:

* **Local Compute Node (Training Environment):** The heavy, resource-intensive tasks—such as bulk data ingestion, data cleaning, and executing the `AutoMLTrainer` algorithms—are executed locally. 
  * *Rationale:* Model training is CPU/RAM intensive. Executing this locally prevents cloud compute bottlenecks, isolates long-running tasks from the live web server, and allows us to bundle the preprocessing rules and the model into a single unified pipeline artifact.
* **DagsHub (Model Registry):** Hosts our managed MLflow server.
  * *Rationale:* Acts as the central bridge between our local training environment and our cloud serving environment. It provides strict version control for our serialized machine learning models (e.g., `.pkl` files) and tracks performance metrics.
* **Vercel (Frontend Web Dashboard):** Hosts the React user interface.
  * *Rationale:* Vercel provides an advanced Edge Network (CDN) highly optimized for serving static web applications. It ensures fast, global load times for the dashboard.
* **Render (Backend API Gateway & Prediction Service):** Hosts our always-on Python microservices.
  * *Rationale:* Render provides native support for containerized Python web services. It allows the Prediction Service to remain continuously active, holding the machine learning model in memory to serve real-time predictions with sub-second latency.
* **Supabase (Metadata Database):** Hosts the PostgreSQL relational database.
  * *Rationale:* Provides a highly scalable, fully managed database for storing user profiles, active sessions, and historical prediction logs. 

### 2. Deployment Strategy
The deployment follows a Continuous Integration / Continuous Deployment (CI/CD) pipeline coupled with a decoupled ML artifact lifecycle:

* **Step 1: Source Control & Versioning:** All frontend and backend codebase is pushed on GitHub.
* **Step 2: Model Artifact Deployment (The ML Pipeline):** The local training script generates a Scikit-Learn Pipeline (bundling both the data preprocessor and the predictive model). This artifact is pushed directly via API to the **DagsHub** MLflow registry.
* **Step 3: Web Infrastructure Configuration:** We link our GitHub repositories directly to Vercel and Render. We extract the connection URLs for our Database (Supabase) and our Model Registry (DagsHub) and inject them into Render and Vercel as highly secure **Environment Variables**.
* **Step 4: Automated CI/CD:** Vercel and Render are configured to automatically trigger a build and deployment whenever new code is pushed to the `main` branch. 
* **Step 5: API Routing & Service Bootstrapping:** When the Prediction Service boots up on Render, its startup script automatically authenticates with DagsHub, downloads the latest model artifact, and loads it into memory. The API Gateway is configured to route all incoming `/predict` requests to this service.

### 3. Security Measures
* **Data in Transit (HTTPS/TLS):** Both Vercel and Render automatically provision and manage SSL certificates. All communication between the user's browser, the API Gateway, and the Prediction Service is fully encrypted.
* **Authentication & Authorization (JWT):** The API Gateway enforces security using JSON Web Tokens (JWT). When a user logs in, they receive a signed token. Every subsequent request (e.g., requesting a price prediction) must include this token in the HTTP header; otherwise, the Gateway will reject the request with a 401 Unauthorized error.
* **Database Protection:** We utilize Supabase's built-in **Row Level Security (RLS)**. This database-level firewall ensures that a real estate agent can only query or view prediction logs that belong strictly to their specific User ID.

---

## II. End-User Access & Interactions

### 1. How End Users Access the Services
End users (Real Estate Professionals) do not need to install any local software to use the live system. They access the platform through a standard web browser by navigating to the custom public domain hosted by Vercel (e.g., `https://real-estate-automl.com`). 

The React-based frontend manages the graphical user interface. When the user inputs property features (e.g., 3 bedrooms, 2000 sq ft, Downtown) and clicks "Predict," the frontend seamlessly transmits this data via asynchronous REST API calls over HTTPS to the backend API Gateway hosted on Render. 



### 2. Pictorial Representation of System Interactions
Below is the sequence diagram illustrating the operational flow when a user requests a property price prediction from the live cloud system. *(The model has already been trained locally and stored in the registry prior to this sequence).*

```mermaid
sequenceDiagram
    autonumber
    actor User as Real Estate Professional
    participant UI as Web Dashboard (Vercel)
    participant Gateway as API Gateway (Render)
    participant AuthDB as PostgreSQL DB (Supabase)
    participant Predictor as Prediction Service (Render)
    participant Registry as MLflow Registry (DagsHub)

    Note over Predictor,Registry: Server Boot-Up Phase
    Predictor->>Registry: Fetch latest "Best Model" Pipeline
    Registry-->>Predictor: Returns serialized .pkl artifact
    Predictor->>Predictor: Loads Pipeline into active memory

    Note over User,Predictor: Live User Interaction Phase
    User->>UI: Logs into Dashboard
    UI->>Gateway: POST /auth/login (Credentials)
    Gateway->>AuthDB: Validate user hash
    AuthDB-->>Gateway: Valid User
    Gateway-->>UI: Returns JWT Session Token

    User->>UI: Enters raw property details & clicks "Predict"
    UI->>Gateway: POST /api/predict (Raw Data + JWT)
    Gateway->>Gateway: Validate JWT Signature
    Gateway->>Predictor: Route property data to Predictor
    
    Predictor->>Predictor: Pipeline automatically cleans raw data
    Predictor->>Predictor: Model calculates estimated price
    Predictor-->>Gateway: Returns Price (e.g., $450,000)
    
    Gateway-->>UI: JSON Response with Price
    UI-->>User: Displays Estimated Value on Screen