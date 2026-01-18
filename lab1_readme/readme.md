# Requirements File
## AutoML Platform for Model Selection and Training in Real Estate

---

## 1. Introduction

This document specifies the functional and non-functional requirements of the **AutoML Platform for Model Selection and Training** in the real estate domain. The system is designed to assist real estate professionals by automating machine learning workflows and providing meaningful insights without requiring technical expertise.

---

## 2. Problem Statement

Real estate professionals often rely on manual analysis and intuition despite having access to large volumes of data. This results in inaccurate pricing, inconsistent investment decisions, and difficulty in explaining recommendations to clients. Existing machine learning tools are complex and unsuitable for non-technical users. This system aims to solve these issues.

---

## 3. Objectives

- Automate machine learning model selection and training  
- Enable accurate prediction of real estate-related outcomes  
- Provide explainable predictions for transparency and trust  
- Support data-driven decision-making for real estate professionals  

---

## 4. Unique Differentiating Features

- **Automated Model Selection**  
  Automatically evaluates and selects the best-performing machine learning model.

- **Explainable Predictions**  
  Highlights influential features such as location, area (square feet), and number of bedrooms.

- **Decision-Support Recommendations**  
  Provides business-oriented suggestions for practical decision-making.

- **User-Friendly Interface**  
  Designed for real estate professionals with no prior technical knowledge.

---

## 5. System Users

- Real Estate Brokers  
- Property Dealers  
- Builders and Developers  
- Real Estate Analysts  

---

## 6. Supported Target Variables

- **Property Sale Price** (Regression)  
- **Rental Value** (Regression)  
- **Property Category** (Classification)  
- **Investment Risk Level** (Classification)  

---

## 7. Functional Requirements

### 7.1 Data Upload and Management

- **FR1: Dataset Upload**  
  The system shall allow users to upload real estate datasets in CSV format with the following specifications:
  - **Format:** Comma-separated values (CSV)
  - **Encoding:** UTF-8
  - **Structure:** First row contains column headers
  - **Maximum File Size:** 100 MB
  - **Supported Data Types:** Numeric (Integer, Float), Categorical (String), Date (ISO 8601)
  - **Validation:** System shall validate file format and reject invalid files with clear error messages

- **FR2: Dataset Preview**  
  The system shall display a preview of the uploaded dataset including:
  - First 10 rows of data
  - Column names and detected data types
  - Basic statistics (count, missing values, data type distribution)
  - Data quality summary (missing values %, outliers detected)

### 7.2 Data Preprocessing

- **FR3: Automatic Data Preprocessing**  
  The system shall automatically preprocess the dataset following this pipeline (in order):
  1. **Data Validation:** Check for required columns, validate data types and ranges
  2. **Missing Value Handling:**
     - Numeric fields: Impute with median value
     - Categorical fields: Impute with mode (most frequent value)
     - Report: Flag columns with > 30% missing values
  3. **Outlier Detection:** Identify and flag values > 3 standard deviations from mean
  4. **Feature Encoding:**
     - Categorical variables: One-Hot Encoding (create binary columns for each category)
     - Ordinal variables: Label Encoding (map to numeric values)
  5. **Feature Scaling:** Apply StandardScaler to numeric features (mean=0, std=1)
  6. **Feature Engineering:** Create derived features (e.g., price per square foot, age of property)
  7. **Data Quality Report:** Generate summary of all preprocessing actions taken
  - **Acceptance Criteria:** Preprocessing completes without data loss; report generated for user review

### 7.3 Target Variable Selection

- **FR4: Target Variable Selection**  
  The system shall allow users to select a target variable for prediction from the uploaded dataset:
  - Display list of available columns
  - Show data type and sample values for each column
  - Validate that selected column is appropriate for chosen prediction task
  - Store selection for model training phase

### 7.4 Model Training and Selection

- **FR5: Multiple Model Training**  
  The system shall train multiple machine learning models based on the target variable type:
  
  **For Regression Tasks (Property Sale Price, Rental Value):**
  - Linear Regression
  - Random Forest Regressor (100 trees, max_depth=10)
  - Gradient Boosting Regressor (XGBoost, n_estimators=100)
  - Support Vector Regressor (RBF kernel, C=1.0)
  - **Minimum:** Train at least 3 models per task
  
  **For Classification Tasks (Property Category, Investment Risk):**
  - Logistic Regression
  - Random Forest Classifier (100 trees, max_depth=10)
  - Gradient Boosting Classifier (XGBoost, n_estimators=100)
  - Support Vector Classifier (RBF kernel, C=1.0)
  - **Minimum:** Train at least 3 models per task
  
  **Training Configuration:**
  - Train/Test Split: 80% training, 20% testing
  - Cross-validation: 5-fold cross-validation for robustness
  - Hyperparameter tuning: Grid search for optimal parameters
  - **Acceptance Criteria:** All models trained successfully; training time logged

- **FR6: Model Evaluation**  
  The system shall evaluate all trained models using appropriate performance metrics:
  
  **For Regression Models:**
  - Mean Absolute Error (MAE): Average absolute difference between predicted and actual values
  - Root Mean Squared Error (RMSE): Square root of average squared errors (penalizes large errors)
  - R² Score: Proportion of variance explained by the model (0-1 scale, higher is better)
  - Mean Absolute Percentage Error (MAPE): Average percentage error relative to actual values
  
  **For Classification Models:**
  - Accuracy: Percentage of correct predictions
  - Precision: True positives / (true positives + false positives)
  - Recall: True positives / (true positives + false negatives)
  - F1 Score: Harmonic mean of precision and recall
  - ROC-AUC Score: Area under the receiver operating characteristic curve (0-1 scale)
  
  **Evaluation Process:**
  - Evaluate on held-out test set (20% of data)
  - Generate confusion matrix for classification tasks
  - Generate residual plots for regression tasks
  - **Acceptance Criteria:** All metrics calculated and displayed; no NaN or infinite values

- **FR7: Automatic Model Selection**  
  The system shall automatically select the best-performing model using this logic:
  1. **Primary Selection Criterion:**
     - Regression: Highest R² Score
     - Classification: Highest F1 Score
  2. **Secondary Criterion (if tied):**
     - Regression: Lowest RMSE
     - Classification: Highest Accuracy
  3. **Model Metadata Storage:**
     - Algorithm name and version
     - Hyperparameters used
     - All performance metrics
     - Training date and time
     - Training data version/hash
  4. **Acceptance Criteria:** Selected model clearly identified; metadata stored for reproducibility

### 7.5 Prediction and Explanation

- **FR8: Generate Predictions**  
  The system shall generate predictions for new data using the selected model:
  - Accept new data in same format as training data
  - Apply same preprocessing pipeline as training data
  - Generate prediction with confidence score
  - Return prediction in standardized JSON format (see Section 7.5.2)
  - **Acceptance Criteria:** Predictions generated within 5 seconds for single record

- **FR9: Explainable Predictions**  
  The system shall provide explainable predictions by identifying key influencing features:
  
  **Explainability Method:** SHAP (SHapley Additive exPlanations) values
  
  **Output Specification:**
  - Top 5 most influential features for each prediction
  - Feature contribution value (numeric impact on prediction)
  - Contribution direction (positive/negative impact)
  - Confidence interval for each feature contribution (±X%)
  - Feature value in the prediction instance
  
  **Format Example:**
  ```
  Feature: Location
  Contribution: +$45,000
  Direction: Positive (increases predicted price)
  Confidence: 92%
  
  Feature: Area (sq ft)
  Contribution: +$32,000
  Direction: Positive (increases predicted price)
  Confidence: 88%
  ```
  
  **Acceptance Criteria:** Explanations generated for 100% of predictions; SHAP values validated

- **FR10: Decision-Support Recommendations**  
  The system shall generate decision-support recommendations including:
  
  1. **Model Confidence Assessment:**
     - Confidence Level: High (>85%), Medium (70-85%), Low (<70%)
     - Confidence Score: Numeric value 0-100%
     - Interpretation: What the confidence level means for decision-making
  
  2. **Feature Insights:**
     - Highlight which features most influenced the prediction
     - Explain how each top feature contributed to the result
     - Compare feature values to dataset averages
  
  3. **Actionable Business Recommendations:**
     - For Price Prediction: "Consider adjusting price by X% based on market factors and comparable properties"
     - For Risk Assessment: "This property shows HIGH risk due to [specific factors]. Recommend [action]"
     - For Category Prediction: "Property classified as [category]. Recommend [business action]"
  
  4. **Comparative Analysis:**
     - Show how prediction compares to similar properties in dataset
     - Percentile ranking (e.g., "Top 25% of properties by price")
     - Market positioning insights
  
  5. **Uncertainty Bounds:**
     - Display prediction range (±X%)
     - Lower bound and upper bound values
     - Interpretation of uncertainty
  
  **Acceptance Criteria:** Recommendations generated for all predictions; non-technical language used

### 7.6 Model Reusability

- **FR11: Model Reuse and Persistence**  
  The system shall allow users to reuse trained models for future predictions:
  - Store trained models with unique identifiers
  - Implement model versioning (MAJOR.MINOR.PATCH format)
  - Support loading previously trained models
  - Track model usage history and performance over time
  - Allow users to compare predictions across model versions
  - **Acceptance Criteria:** Models persist across sessions; can be loaded and used for new predictions

- **FR12: Model Versioning Strategy**  
  The system shall implement model versioning with the following approach:
  
  **Version Format:** MAJOR.MINOR.PATCH (e.g., 1.0.0)
  
  **Semantic Versioning Rules:**
  - **MAJOR:** Algorithm change (e.g., switching from Random Forest to XGBoost)
  - **MINOR:** Hyperparameter tuning or preprocessing pipeline changes
  - **PATCH:** Bug fixes or minor improvements
  
  **Metadata Stored per Version:**
  - Algorithm name and type
  - Hyperparameters used
  - Training date and time
  - Training data version/hash
  - All performance metrics (MAE, RMSE, R², Accuracy, F1, etc.)
  - Data preprocessing steps applied
  - Feature list and encoding scheme
  
  **Rollback Capability:**
  - Support reverting to previous model versions
  - Maintain history of all model versions
  - Track which version is currently active
  
  **Acceptance Criteria:** Version history maintained; rollback tested and working

---

## 8. Non-Functional Requirements

### 8.1 Performance Requirements

- **NFR1: Performance SLA**  
  The system shall meet the following performance requirements:
  
  | Dataset Size | Maximum Processing Time | Concurrent Jobs |
  |---|---|---|
  | Small (< 10K rows) | 30 seconds | 10 |
  | Medium (10K - 100K rows) | 5 minutes | 10 |
  | Large (100K - 1M rows) | 30 minutes | 5 |
  | Maximum dataset size | 1 GB | - |
  
  **Specific Performance Targets:**
  - Model training: Complete within specified time limits
  - Prediction generation: < 5 seconds per record
  - API response time: < 2 seconds for 95th percentile
  - Page load time: < 3 seconds
  - Form submission feedback: < 1 second
  
  **Acceptance Criteria:** Performance benchmarks met for all dataset sizes; monitoring in place

### 8.2 Usability Requirements

- **NFR2: Usability Standards**  
  The system shall meet the following usability requirements:
  
  **Accessibility:**
  - WCAG 2.1 Level AA compliance
  - Keyboard navigation support for all features
  - Screen reader compatibility (tested with NVDA, JAWS)
  - Color contrast ratio: Minimum 4.5:1 for text
  - Alternative text for all images and icons
  
  **User Experience:**
  - Page load time: < 3 seconds
  - Form submission feedback: < 1 second
  - Error messages: Clear, actionable, non-technical language
  - Consistent UI patterns across all pages
  - Responsive design for desktop and tablet (minimum 768px width)
  
  **Documentation and Support:**
  - In-app help tooltips for all features
  - Video tutorials for main workflows (upload, train, predict)
  - FAQ section with common questions
  - Contextual help on error messages
  
  **User Testing Criteria:**
  - Minimum 5 non-technical users per release
  - Task completion rate: > 90%
  - System Usability Scale (SUS) score: > 70
  - Time to complete main task: < 10 minutes
  
  **Acceptance Criteria:** WCAG 2.1 AA compliance verified; SUS score > 70

### 8.3 Security Requirements

- **NFR3: Security and Data Protection**  
  The system shall implement comprehensive security measures:
  
  **Data Encryption:**
  - In Transit: HTTPS/TLS 1.2 or higher for all communications
  - At Rest: AES-256 encryption for stored datasets and models
  - Key Management: Secure key storage with rotation every 90 days
  
  **User Authentication and Authorization:**
  - Authentication Methods:
    - Username/password with email verification
    - Optional: OAuth 2.0 (Google, Microsoft)
    - Multi-factor authentication (MFA) for admin accounts
  - Session Management:
    - Session timeout: 30 minutes of inactivity
    - Secure session tokens (JWT with expiration)
    - Logout clears all session data
  - Authorization:
    - Users can only access their own datasets and models
    - Role-based access control (RBAC): Admin, User roles
    - Admin role for system management and user administration
  
  **Data Retention and Deletion:**
  - Datasets retained for 90 days after upload
  - Users can delete datasets on demand (immediate deletion)
  - Automatic purge of inactive accounts after 1 year
  - Secure deletion: Data overwritten before removal
  
  **Compliance and Audit:**
  - GDPR compliance for EU users (data subject rights, consent management)
  - CCPA compliance for California users
  - Data residency: [Specify region - e.g., US, EU, etc.]
  - Audit logging: All data access logged with timestamp, user, action
  - Audit log retention: Minimum 1 year
  
  **Acceptance Criteria:** Security audit passed; encryption verified; audit logs functional

### 8.4 Scalability Requirements

- **NFR4: Scalability and Extensibility**  
  The system shall support scalability and future expansion:
  
  **Model Registry and Management:**
  - Centralized model storage with versioning
  - Support for adding new algorithms without code changes
  - Model metadata: Algorithm, hyperparameters, performance metrics, training date
  - Model discovery: Search and filter models by type, performance, date
  
  **Extensibility Architecture:**
  - Plugin architecture for custom models
  - Configuration-driven model selection (no code changes needed)
  - Support for custom preprocessing steps
  - Custom metric support for domain-specific evaluation
  
  **Infrastructure Scalability:**
  - Horizontal scaling for API servers (stateless design)
  - Distributed training for large datasets (optional)
  - Caching layer for frequently used models (Redis or similar)
  - Database indexing for fast queries
  
  **Future Capacity Planning:**
  - Support up to 100 concurrent users
  - Support datasets up to 10 GB
  - Support 50+ ML algorithms
  - Support multiple target variables simultaneously
  
  **Acceptance Criteria:** System handles 100 concurrent users; supports 50+ algorithms

### 8.5 Reliability Requirements

- **NFR5: Reliability and Error Handling**  
  The system shall meet the following reliability requirements:
  
  **Uptime and Availability:**
  - Uptime SLA: 99.5% availability (maximum 3.6 hours downtime per month)
  - Planned maintenance: Scheduled during low-usage windows
  - Incident response: Critical issues resolved within 4 hours
  
  **Error Handling and Validation:**
  - Graceful degradation for missing values (imputation, not failure)
  - Validation errors with clear, actionable messages
  - Automatic retry for transient failures (up to 3 attempts)
  - Fallback mechanisms for non-critical features
  
  **Data Validation:**
  - Check for required columns before processing
  - Validate data types and ranges
  - Detect and flag outliers (> 3 standard deviations)
  - Warn users about data quality issues
  
  **Recovery and Backup:**
  - Automatic backup of trained models (daily)
  - Rollback capability for failed training jobs
  - Data integrity checks on load (checksums, validation)
  - Recovery time objective (RTO): < 1 hour
  - Recovery point objective (RPO): < 1 hour
  
  **Monitoring and Alerting:**
  - System health monitoring (CPU, memory, disk usage)
  - Error rate monitoring and alerting
  - Performance monitoring and alerting
  - User activity logging
  
  **Acceptance Criteria:** 99.5% uptime achieved; recovery procedures tested

---

## 9. Data Specifications

### 9.1 Input Data Schema

The system shall accept datasets with the following specifications:

**Required Columns (Minimum):**
- Property ID (unique identifier, String or Integer)
- Location (address or coordinates, String)
- Area (square feet, Numeric - Integer or Float)
- Bedrooms (count, Integer)
- Bathrooms (count, Integer or Float)
- Year Built (numeric, Integer)
- Property Type (categorical, String)
- [Target Variable] (depends on selected prediction task)

**Data Type Constraints:**
- Numeric fields: Integer or Float (range: -999,999,999 to 999,999,999)
- Categorical fields: String (maximum 100 characters)
- Date fields: ISO 8601 format (YYYY-MM-DD)
- Boolean fields: True/False or 0/1

**Data Quality Requirements:**
- No duplicate rows (checked by Property ID)
- Missing values: Maximum 30% per column
- Outliers: Flagged if > 3 standard deviations
- Data consistency: Logical relationships maintained (e.g., Year Built < Current Year)

**Example Input Schema:**
```
Property_ID, Location, Area_SqFt, Bedrooms, Bathrooms, Year_Built, Property_Type, Price
1001, "123 Main St, NYC", 2500, 4, 2.5, 1995, "Single Family", 750000
1002, "456 Oak Ave, LA", 1800, 3, 2, 2005, "Condo", 550000
```

### 9.2 Output Format Specification

**Prediction Response Format (JSON):**
```json
{
  "prediction_id": "uuid-12345",
  "target_variable": "Property Sale Price",
  "predicted_value": 450000,
  "prediction_unit": "USD",
  "confidence_level": "High",
  "confidence_score": 0.92,
  "prediction_range": {
    "lower_bound": 420000,
    "upper_bound": 480000,
    "margin_of_error_percent": 6.7
  },
  "top_features": [
    {
      "rank": 1,
      "name": "Location",
      "contribution": 45000,
      "contribution_percent": 10.0,
      "direction": "positive",
      "confidence": 0.95,
      "feature_value": "Manhattan"
    },
    {
      "rank": 2,
      "name": "Area",
      "contribution": 32000,
      "contribution_percent": 7.1,
      "direction": "positive",
      "confidence": 0.88,
      "feature_value": 2500
    }
  ],
  "recommendations": [
    "Consider adjusting price by +5% based on market factors",
    "This property is in the top 25% by price for the area",
    "Recommend marketing to luxury segment"
  ],
  "model_info": {
    "algorithm": "Random Forest Regressor",
    "version": "1.2.0",
    "training_date": "2024-01-15"
  },
  "timestamp": "2024-01-20T10:30:00Z"
}
```

**Classification Prediction Response Format (JSON):**
```json
{
  "prediction_id": "uuid-12346",
  "target_variable": "Investment Risk Level",
  "predicted_class": "HIGH",
  "class_probabilities": {
    "LOW": 0.15,
    "MEDIUM": 0.25,
    "HIGH": 0.60
  },
  "confidence_score": 0.60,
  "top_features": [
    {
      "rank": 1,
      "name": "Location",
      "contribution": 0.35,
      "direction": "increases_risk"
    }
  ],
  "recommendations": [
    "This property shows HIGH risk due to location and market conditions",
    "Recommend additional due diligence before investment"
  ],
  "timestamp": "2024-01-20T10:30:00Z"
}
```

---

## 10. API and Interface Specification

### 10.1 Core API Endpoints

**Authentication Endpoints:**
- `POST /api/auth/login` - User authentication (username/password or OAuth)
- `POST /api/auth/logout` - User logout
- `POST /api/auth/register` - User registration
- `POST /api/auth/refresh-token` - Refresh session token

**Dataset Management Endpoints:**
- `POST /api/datasets/upload` - Upload dataset (multipart/form-data)
- `GET /api/datasets` - List user's datasets
- `GET /api/datasets/{id}` - Get dataset details
- `GET /api/datasets/{id}/preview` - Preview dataset (first 10 rows)
- `DELETE /api/datasets/{id}` - Delete dataset

**Model Training Endpoints:**
- `POST /api/training/start` - Start model training job
- `GET /api/training/{id}/status` - Get training job status
- `GET /api/training/{id}/results` - Get training results and metrics
- `GET /api/models` - List available trained models
- `GET /api/models/{id}` - Get model details and metadata

**Prediction Endpoints:**
- `POST /api/predictions` - Generate prediction
- `GET /api/predictions/{id}` - Get prediction details
- `GET /api/predictions/{id}/explain` - Get detailed explanation (SHAP values)
- `GET /api/predictions/history` - Get prediction history

**System Endpoints:**
- `GET /api/health` - System health check
- `GET /api/metrics` - System performance metrics

### 10.2 User Interface Workflows

**Main Workflows:**
1. **Upload Workflow:** Login → Upload Dataset → Preview Data → Confirm Upload
2. **Training Workflow:** Select Dataset → Choose Target Variable → Start Training → Monitor Progress → View Results
3. **Prediction Workflow:** Select Model → Input Data → Generate Prediction → View Explanation → Get Recommendations
4. **Model Management Workflow:** View Models → Compare Performance → Select Active Model → View History

---

## 11. Testing Requirements

### 11.1 Test Coverage

- **Unit Tests:** Minimum 80% code coverage
- **Integration Tests:** All API endpoints tested
- **End-to-End Tests:** Main user workflows tested
- **Performance Tests:** Load testing with 100 concurrent users
- **Security Tests:** Penetration testing and vulnerability scanning

### 11.2 Acceptance Criteria

**Functional Testing:**
- All functional requirements (FR1-FR12) have passing test cases
- All non-functional requirements (NFR1-NFR5) have passing test cases
- Edge cases tested (empty datasets, missing values, outliers)
- Error handling tested (invalid inputs, network failures)

**Performance Testing:**
- Response time < 2 seconds for 95th percentile
- System handles 100 concurrent users without degradation
- Dataset processing meets SLA targets

**Security Testing:**
- Authentication and authorization working correctly
- Data encryption verified
- SQL injection and XSS vulnerabilities tested
- OWASP Top 10 vulnerabilities addressed

**User Acceptance Testing:**
- 5+ non-technical users complete main workflows
- Task completion rate > 90%
- SUS score > 70

---

## 12. Assumptions and Constraints

### 12.1 Assumptions

- Datasets are provided in CSV format with proper structure
- Only open-source machine learning libraries are used (scikit-learn, XGBoost, etc.)
- Deep learning models are outside the scope of the current version
- Users have basic computer literacy (can upload files, navigate web interface)
- Internet connectivity is available for all users

### 12.2 Constraints

- Maximum dataset size: 1 GB
- Maximum concurrent users: 100
- Supported algorithms: Limited to scikit-learn and XGBoost
- No real-time streaming data support
- No GPU acceleration in current version

---

## 13. Acceptance Criteria Summary

| Requirement | Acceptance Criteria | Status |
|---|---|---|
| FR1: Dataset Upload | CSV format validated; file size < 100 MB | To Implement |
| FR2: Dataset Preview | First 10 rows displayed; statistics shown | To Implement |
| FR3: Data Preprocessing | All 7 steps completed; report generated | To Implement |
| FR4: Target Selection | Valid column selected; stored for training | To Implement |
| FR5: Model Training | 3+ models trained; all metrics calculated | To Implement |
| FR6: Model Evaluation | All metrics computed; no NaN values | To Implement |
| FR7: Model Selection | Best model identified; metadata stored | To Implement |
| FR8: Predictions | Generated within 5 seconds; JSON format | To Implement |
| FR9: Explainability | SHAP values computed; top 5 features shown | To Implement |
| FR10: Recommendations | Generated for all predictions; non-technical | To Implement |
| FR11: Model Reuse | Models persist; can be loaded and used | To Implement |
| FR12: Versioning | Version history maintained; rollback works | To Implement |
| NFR1: Performance | SLA targets met for all dataset sizes | To Implement |
| NFR2: Usability | WCAG 2.1 AA; SUS score > 70 | To Implement |
| NFR3: Security | Encryption verified; audit logs functional | To Implement |
| NFR4: Scalability | 100 concurrent users; 50+ algorithms | To Implement |
| NFR5: Reliability | 99.5% uptime; recovery procedures tested | To Implement |

---

## 14. Conclusion

The AutoML Platform for Model Selection and Training provides an effective and transparent solution for real estate professionals by automating machine learning workflows and delivering explainable, decision-oriented insights. This comprehensive requirements document specifies all functional and non-functional requirements with concrete details, acceptance criteria, and implementation guidance to enable successful development and deployment.

---

## Appendix A: Glossary

- **SHAP:** SHapley Additive exPlanations - a method for explaining machine learning predictions
- **CSV:** Comma-Separated Values - a text file format for tabular data
- **WCAG:** Web Content Accessibility Guidelines - standards for web accessibility
- **SUS:** System Usability Scale - a standardized usability measurement scale
- **SLA:** Service Level Agreement - commitment to system performance and availability
- **GDPR:** General Data Protection Regulation - EU data protection regulation
- **CCPA:** California Consumer Privacy Act - California data protection law
- **JWT:** JSON Web Token - a secure token format for authentication
- **RBAC:** Role-Based Access Control - authorization based on user roles
- **RTO:** Recovery Time Objective - maximum acceptable downtime
- **RPO:** Recovery Point Objective - maximum acceptable data loss

---

## Appendix B: References

- scikit-learn Documentation: https://scikit-learn.org/
- XGBoost Documentation: https://xgboost.readthedocs.io/
- SHAP Documentation: https://shap.readthedocs.io/
- WCAG 2.1 Guidelines: https://www.w3.org/WAI/WCAG21/quickref/
- GDPR Compliance Guide: https://gdpr-info.eu/
- OWASP Top 10: https://owasp.org/www-project-top-ten/

