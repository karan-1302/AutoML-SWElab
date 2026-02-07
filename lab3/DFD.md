# Data Flow Diagrams for Real Estate AutoML

Here are the Data Flow Diagrams (DFD) for the AutoML System.

## Level 0 DFD - Context Diagram

This diagram shows the interaction between the System and external entities.

```mermaid
graph TD
    %% Entities
    User[Real Estate Professional]
    Client[Client / Investor]
    MarketSrc[External Market Data API]

    %% System
    System(AutoML Real Estate System)

    %% Flows
    User -->|1. Upload Dataset| System
    User -->|2. Select Target Variable| System
    User -->|3. Request Prediction| System
    
    System -->|4. Data Preview| User
    System -->|5. Price Prediction| User
    System -->|6. Explanation (SHAP/LIME)| User
    System -->|7. Decision Support Recs| User
    
    System -->|8. Investment Reports| Client
    MarketSrc -->|9. Real-time Trends| System

    style System fill:#f9f,stroke:#333,stroke-width:2px
```

## Level 1 DFD - Detailed Decomposition

This diagram breaks down the system into its core functional processes and data stores.

```mermaid
graph TD
    %% External Entities
    User[Real Estate Professional]
    
    %% Processes
    P1(1.0 Data Ingestion & Validation)
    P2(2.0 Data Preprocessing)
    P3(3.0 AutoML Training Engine)
    P4(4.0 Model Selection & Eval)
    P5(5.0 Prediction Service)
    P6(6.0 Explainer Engine)
    
    %% Data Stores
    Store1[(D1: Raw Datasets)]
    Store2[(D2: Processed Data)]
    Store3[(D3: Model Registry)]
    Store4[(D4: Hist. Predictions)]

    %% Flows from User
    User -->|Upload CSV/JSON| P1
    User -->|Validation Feedback| P1
    
    %% Process Data Flows
    P1 -->|Valid Data| Store1
    Store1 -->|Fetch Raw| P2
    P2 -->|Cleaned & Scaled Data| Store2
    
    Store2 -->|Training Batches| P3
    P3 -->|Candidate Models| P4
    P4 -->|Metrics (RMSE/R2)| P3
    P4 -->|Best Model| Store3
    
    %% Prediction Flows
    User -->|Input Features| P5
    Store3 -->|Load Best Model| P5
    P5 -->|Raw Prediction| P6
    P5 -->|Result| User
    P5 -->|Save Result| Store4
    
    P6 -->|Influence Factors| User
    Store4 -->|Retraining Feedback| P3
```

## Extra Functionalities Included
1. **Feedback Loop**: Historical predictions stored in `D4` can be used to retrain models, ensuring the system improves over time.
2. **Explainer Engine**: Explicit process `P6` to handle SHAP/LIME explanations, separating it from raw prediction for better clarity.
3. **Market Integration**: Added external market data source in Level 0 to make the system dynamic.
