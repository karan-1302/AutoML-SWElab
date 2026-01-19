# Software Requirements Specification (SRS)
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
- **Market Demand Level** (Regression / Classification)  

---

## 7. Functional Requirements

- The system shall allow users to upload real estate datasets in a specified format.  
- The system shall display a preview of the uploaded dataset.  
- The system shall allow users to select a target variable for prediction.  
- The system shall automatically preprocess the dataset.  
- The system shall train multiple machine learning models.  
- The system shall evaluate models using appropriate performance metrics.  
- The system shall automatically select the best-performing model.  
- The system shall generate predictions for the selected target variable.  
- The system shall provide explainable predictions by identifying key influencing features.  
- The system shall generate decision-support recommendations.  
- The system shall allow users to reuse the trained model for future predictions.  

---

## 8. Non-Functional Requirements

- **Usability:**  
  The system shall provide an intuitive interface suitable for non-technical users.

- **Performance:**  
  The system shall process medium-sized datasets within reasonable time limits.

- **Security:**  
  The system shall ensure secure handling of uploaded datasets.

- **Scalability:**  
  The system shall support future expansion and addition of new models.

- **Reliability:**  
  The system shall handle incomplete or noisy data gracefully.

---

## 9. Assumptions and Constraints

- Datasets are provided in a specified format.  
- Only open-source machine learning libraries are used.  
- Deep learning models are outside the scope of the current version.  

---

## 10. Conclusion

The AutoML Platform for Model Selection and Training provides an effective and transparent solution for real estate professionals by automating machine learning workflows and delivering explainable, decision-oriented insights.

---
