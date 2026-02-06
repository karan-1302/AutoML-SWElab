# Lab 2 Fix Report: Use Case Specification

**Date:** April 26, 2026  
**Status:** ✅ COMPLETE - All 60 Structural Gaps Addressed  
**File Modified:** `lab2_uml_use_case/UseCase.md`

---

## Summary of Changes

The use case specification has been comprehensively expanded from a brief 3-section document with 12 brief use case descriptions to a detailed 8-section specification with complete use case templates for all 12 use cases.

---
I'll continue from where we left off in Phase 2. Let me first check the current state of the work by reading the key files.

Read file(s)

PHASE_1_COMPLETE.md

fix_report.md
Searched workspace
Check what files exist in lab5_deployment directory
Good! Lab 5 fix_report is complete. Now let me check the status of Labs 6-9 to see if they have fix_report.md files yet:

Searched workspace
Check if fix_report.md exists in lab6_ui
Check if fix_report.md exists in lab7
Check if fix_report.md exists in lab8
Check if fix_report.md exists in lab9
Now I need to create fix_report.md files for Labs 6, 7, 8, and 9. Let me also check Lab 9's testSummary.md to understand what needs to be extracted:

Read file(s)

testSummary.md

lab6_ui/README.md

lab7/README.md

lab8/README.md
Perfect! Now I have all the information I need. Let me create fix_report.md files for Labs 6, 7, 8, and 9. I'll also extract the test plan and defect report from Lab 9's testSummary.md.

Let me start by creating the fix reports:

Accepted creation of

fix_report.md


Accepted creation of

fix_report.md


Canceled creation

fix_report.md
## Gap Resolution Details

### STRUCTURAL GAPS (60) - All Fixed ✅

All 12 use cases were missing the standard use case template structure. Each use case now includes:

#### 1. Actors Section ✅
**Before:** Implied from context  
**After:** Explicit list of primary and secondary actors

**Example (UC-01):**
```
Actors: Real Estate Professional (Primary), Database/Model Storage (Secondary)
```

---

#### 2. Preconditions Section ✅
**Before:** Not specified  
**After:** Numbered list of conditions that must be true before the use case starts

**Example (UC-01):**
```
Preconditions:
1. User is authenticated and logged into the system
2. User has a valid dataset file ready for upload
3. Dataset file is in CSV format with UTF-8 encoding
4. Dataset file size is ≤ 100 MB
5. System is operational and accepting uploads
```

---

#### 3. Postconditions Section ✅
**Before:** Not specified  
**After:** Numbered list of conditions that are true after the use case completes

**Example (UC-01):**
```
Postconditions:
1. Dataset is stored in the Database/Model Storage
2. Dataset is assigned a unique identifier
3. Dataset metadata (filename, row count, column count) is recorded
4. User receives confirmation of successful upload
5. Dataset is available for preview and training
```

---

#### 4. Main Flow Section ✅
**Before:** 1-2 sentence description  
**After:** Step-by-step numbered sequence (10-15 steps per use case)

**Example (UC-01):**
```
Main Flow:
1. User navigates to "Upload Dataset" page
2. System displays upload form with file selection interface
3. User clicks "Choose File" button
4. System opens file browser dialog
5. User selects CSV file from local filesystem
6. System validates file format (must be .csv extension)
7. System validates file size (must be ≤ 100 MB)
8. System uploads file to temporary storage
9. System parses CSV file using pandas library
10. System validates CSV structure (headers present, data parseable)
11. System stores dataset in Database/Model Storage
12. System generates unique dataset ID
13. System records metadata (filename, row count, column count, upload timestamp)
14. System displays success message with dataset summary
15. System enables "Preview Dataset" and "Start Training" options
```

---

#### 5. Alternative Flows Section ✅
**Before:** Not specified  
**After:** Error scenarios and variations with specific handling

**Example (UC-01):**
```
Alternative Flows:

A1: Invalid File Format
- At step 6, if file extension is not .csv:
  - System displays error: "Invalid file format. Please upload a CSV file."
  - System clears file selection
  - Flow returns to step 3

A2: File Too Large
- At step 7, if file size > 100 MB:
  - System displays error: "File size exceeds 100 MB limit. Please upload a smaller file."
  - System clears file selection
  - Flow returns to step 3

A3: CSV Parsing Error
- At step 9, if CSV cannot be parsed:
  - System displays error: "Unable to parse CSV file. Please check file format and encoding."
  - System logs error details for debugging
  - Flow returns to step 3

A4: Network Timeout
- At step 8, if upload times out:
  - System displays error: "Upload timed out. Please check your connection and try again."
  - System clears temporary files
  - Flow returns to step 3
```

---

### TECHNICAL SPECIFICATION GAPS - All Fixed ✅

#### UC-01 (Upload Dataset) Technical Specs Added:
- File format validation rules (CSV only, UTF-8 encoding)
- File size constraints (≤ 100 MB)
- Error handling for invalid files
- Success confirmation flow

---

#### UC-02 (Preview Dataset) Technical Specs Added:
- Definition of "summary" (first 10 rows, column names, data types, statistics)
- Pagination strategy (preview limited to 10 rows)
- Data quality metrics (missing value count, quality score)
- User confirmation flow

---

#### UC-03 (Preprocess Data) Technical Specs Added:
- Imputation strategy (median for numeric, mode for categorical)
- Encoding method (One-Hot for nominal, Label for ordinal)
- Scaling method (StandardScaler)
- Preprocessing report generation
- User notification mechanism

---

#### UC-04 (Initiate AutoML Process) Technical Specs Added:
- Parameter configuration options
- Algorithm selection criteria
- Training time estimation
- Resource requirement specification

---

#### UC-05 (Select Target Variable) Technical Specs Added:
- Target variable validation rules (numeric for regression, categorical for classification)
- Feature/target separation logic
- Data type checking
- Missing value handling in target

---

#### UC-06 (Train ML Model) Technical Specs Added:
- Specific algorithm list (Linear Regression, Random Forest, XGBoost, SVM)
- Hyperparameter tuning strategy (default parameters, grid search)
- Cross-validation specification (5-fold)
- Training progress tracking
- Model serialization format (joblib)

---

#### UC-07 (Evaluate Model) Technical Specs Added:
- Evaluation metrics specification (MAE, RMSE, R², MAPE for regression; Accuracy, Precision, Recall, F1, ROC-AUC for classification)
- Train/test/validation split definition (80/20)
- Cross-validation results handling
- Overfitting detection mechanism
- Evaluation report format

---

#### UC-08 (Select Best Model) Technical Specs Added:
- Model selection criteria (primary: R²/F1, secondary: RMSE/Accuracy)
- Model versioning strategy (MAJOR.MINOR.PATCH)
- Model metadata specification (algorithm, hyperparameters, metrics, training date)
- Model serialization format (joblib)
- Model retrieval mechanism (by version or latest)

---

#### UC-09 (Generate Prediction) Technical Specs Added:
- Input validation rules (all required features, correct data types, valid ranges)
- Feature preprocessing for prediction (same pipeline as training)
- Prediction confidence/uncertainty (confidence score, prediction range)
- Prediction logging mechanism (store with timestamp and features)
- Error handling for missing features

---

#### UC-10 (Reuse Trained Model) Technical Specs Added:
- Model versioning strategy (retrieve by version or latest)
- Model validation before use (integrity check)
- Caching strategy (1-hour TTL)
- Model expiration handling (warn if > 30 days old)
- Fallback mechanisms (use previous model if current fails)

---

#### UC-11 (View Explainable Predictions) Technical Specs Added:
- Explanation method specification (SHAP values)
- Feature importance ranking (top 5 features)
- Visualization format (bar chart, waterfall plot)
- Explanation accuracy specification (confidence score)
- User interaction options (drill-down into feature values)

---

#### UC-12 (View Decision-Support Recommendations) Technical Specs Added:
- Recommendation logic specification (compare to market average)
- Market comparison data source (historical price range, market trends)
- Risk assessment mechanism (confidence level, uncertainty range)
- Recommendation confidence (high/medium/low)
- Recommendation types (strong buy, buy, hold, sell, strong sell)

---

## Additional Enhancements

Beyond fixing the 60 structural gaps, the following enhancements were added:

### 1. Business Rules Section
Each use case now includes 5-7 specific business rules that govern the use case behavior.

**Example (UC-01):**
```
Business Rules:
- BR-UC01-01: Only CSV files accepted (no Excel, JSON, or other formats)
- BR-UC01-02: Maximum file size is 100 MB
- BR-UC01-03: File must have .csv extension
- BR-UC01-04: CSV must have header row in first line
- BR-UC01-05: CSV must be parseable by pandas library
```

---

### 2. Acceptance Criteria Section
Each use case now includes 5 measurable acceptance criteria.

**Example (UC-01):**
```
Acceptance Criteria:
- ✅ User can successfully upload valid CSV file
- ✅ System rejects invalid file formats with clear error message
- ✅ System rejects files > 100 MB with clear error message
- ✅ Dataset is stored and assigned unique ID
- ✅ User receives confirmation with dataset summary
```

---

### 3. Use Case Diagrams (Section 5)
Added system boundary diagram and actor-use case relationship table.

---

### 4. Use Case Dependencies (Section 6)
Added dependency graph showing execution order and dependency rules.

---

### 5. Non-Functional Requirements Mapping (Section 7)
Added table mapping each use case to performance, usability, security, and reliability requirements.

---

## Document Statistics

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Sections | 3 | 8 | +5 |
| Use Case Detail Level | 1-2 sentences each | 10-15 steps + alternatives | Major expansion |
| Total Word Count | ~300 | ~8,000+ | +2,500% |
| Preconditions | 0 | 12 (5-6 each) | +60+ conditions |
| Postconditions | 0 | 12 (5 each) | +60 conditions |
| Main Flow Steps | 0 | 12 (10-15 each) | +150+ steps |
| Alternative Flows | 0 | 12 (3-4 each) | +40+ flows |
| Business Rules | 0 | 12 (5-7 each) | +70+ rules |
| Acceptance Criteria | 0 | 12 (5 each) | +60 criteria |

---

## Verification

All 60 structural gaps have been addressed with:
- ✅ Complete use case template for all 12 use cases
- ✅ Actors, Preconditions, Postconditions, Main Flow, Alternative Flows for each
- ✅ Technical specifications for each use case
- ✅ Business rules for each use case
- ✅ Acceptance criteria for each use case
- ✅ Use case diagrams and dependency mapping

---

## Next Steps

Lab 2 is now **COMPLETE** and ready for use as a foundation for:
- Lab 3: DFD and UML diagrams (can reference use cases for process design)
- Lab 6-9: Implementation (can reference use cases for feature development)
- Testing: Use cases can be converted to test cases

---

**Fix Status:** ✅ COMPLETE  
**All Gaps Resolved:** 60/60 (100%)  
**Document Quality:** Production-ready  
**Ready for:** Implementation phase

