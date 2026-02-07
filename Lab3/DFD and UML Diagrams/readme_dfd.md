Here is a comprehensive `README.md` section documenting the final **Level 0** and **Level 1 Data Flow Diagrams (DFDs)**. You can include this in your project report or repository to explain the architectural logic to your professor or evaluators.

---

# System Design: Data Flow Diagrams (DFD)

This section documents the logical architecture of the **Real Estate AutoML System**, illustrating how data moves between the user, the system processes, and the external storage entities.

## 1. Level 0 DFD: Context Diagram

**Objective:** To define the system boundary and interactions with external entities.

The Level 0 diagram depicts the **Real Estate AutoML System** as a single "Black Box" process (Process 0.0) that mediates interactions between the User and the external data repositories.

### **Key Components:**

* **External Entity - User / Real Estate Professional:**
* The primary source of input (credentials, datasets, new property data).
* The recipient of outputs (dashboards, predictions, explanation reports).


* **External Entity - User Database:**
* Acts as an external authentication provider.
* Validates "User Credentials" and returns an "Auth Confirmation."


* **External Entity - Model Registry:**
* Acts as the long-term storage for trained machine learning models.
* Receives the "Best Model" after training and provides the "Trained Model" during prediction.



### **Data Flow Summary:**

1. **Authentication:** Credentials flow to the system, are validated against the external **User Database**, and access is granted.
2. **Training:** The user uploads raw data; the system processes it and saves the best performing model into the **Model Registry**.
3. **Prediction:** The user inputs new property details; the system retrieves the model from the **Model Registry** to generate a price prediction.

---

## 2. Level 1 DFD: Functional Decomposition

**Objective:** To break down the main system into specific sub-processes, revealing internal logic and data handling strategies.

The Level 1 diagram decomposes the system into **5 distinct processes**, adhering to a direct-flow architecture (no intermediate dataset storage) and including an explainability module.

### **Processes:**

* **1.0 Login & Authenticate:**
* Handles user entry.
* Interacts directly with **D1 User Database** to verify credentials.
* **Output:** Auth Token / Access Grant.


* **2.0 Upload & Clean Data:**
* Accepts the raw `.csv` file from the user.
* Performs cleaning (handling missing values, encoding).
* **Design Note:** Features a **Direct Data Stream** to Process 3.0. We do not store the cleaned CSV to disk (removing the "Dataset Archive" store) to optimize storage and speed.


* **3.0 AutoML Training & Registry:**
* Receives the cleaned data stream.
* Trains multiple models and evaluates performance.
* **Output:** Saves the "Best Model" into **D3 Model Registry**.


* **4.0 Prediction:**
* Accepts new property data (e.g., a specific house listing).
* Loads the trained model from **D3**.
* **Output:** Generates a raw prediction (e.g., Price: $500,000).


* **5.0 Explainer (Insights):**
* **Input:** Receives the "Prediction Details" from Process 4.0 and "Model Metadata" (feature importance, weights) from **D3**.
* **Function:** Analyzes *why* the model made that specific prediction.
* **Output:** Delivers a human-readable "Explanation Report" to the user (e.g., *"Price is high due to Location weighting"*).



### **Data Stores:**

* **D1 User Database:** Stores username/password hashes for authentication.
* **D3 Model Registry:** Stores the serialized model files (Pickle/Joblib) and their associated metadata.

### **Key Design Highlights:**

* **Streaming Architecture:** By removing the intermediate Dataset Store (D2), the system reduces latency between Upload and Training.
* **Explainability:** The dedicated **Process 5.0** ensures the system meets the "White Box" requirement, helping real estate professionals trust the automated valuations.