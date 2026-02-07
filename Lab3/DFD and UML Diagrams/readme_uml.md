The 7 key classes identified for the Real Estate AutoML System:
+ Public

- Private

# Protected

1. Class: User
Responsibility: Represents the Real Estate Professional interacting with the system.

Attributes:

- userId: String

- username: String

- passwordHash: String

- role: String (e.g., "Broker", "Analyst")

Methods:

+ login(credentials): Boolean

+ uploadDataset(filePath): Dataset

+ requestPrediction(propertyData): float

+ viewExplanation(): void

2. Class: AuthManager
Responsibility: Handles security and access control (Process 1.0).

Attributes:

- activeSessions: Dictionary

Methods:

+ verifyCredentials(user, pass): Boolean

+ generateToken(userId): String

+ logout(userId): void

3. Class: Dataset
Responsibility: Holds the raw and cleaned data (Process 2.0).

Attributes:

- rawData: DataFrame

+ targetVariable: String

- isCleaned: Boolean

Methods:

+ loadFromCSV(path): void

+ preprocess(): void (Handles missing values/encoding)

+ getTrainingSplit(): tuple

4. Class: AutoMLTrainer
Responsibility: Manages the training loop and selection logic (Process 3.0).

Attributes:

- modelList: List<MLModel>

- performanceLog: Dictionary

Methods:

+ trainAll(data): void

+ evaluateModels(metric): void

+ selectBestModel(): MLModel

5. Class: MLModel (Abstract Base Class)
Responsibility: A generic template for any machine learning algorithm.

Attributes:

# modelID: String

# hyperParameters: Dictionary

+ accuracyScore: float

Methods:

+ train(features, labels): void (Abstract)

+ predict(features): float (Abstract)

6. Class: ModelRegistry
Responsibility: Handles saving and loading trained models (Data Store D3).

Attributes:

- storagePath: String

- registryDB: Database

Methods:

+ saveModel(modelObject): Boolean

+ loadModel(modelID): MLModel

+ getMetadata(modelID): Dictionary

7. Class: Explainer
Responsibility: Generates insights for the user (Process 5.0).

Attributes:

- explainerType: String (e.g., "SHAP", "LIME")

Methods:

+ generateReport(prediction, model): JSON

+ getFeatureImportance(model): Dictionary

Q2. UML Class Diagram
This diagram depicts the relationships (Inheritance, Composition, Association) and cardinality required by the assignment.

Key Relationships shown:

Inheritance (<|--): RegressionModel and ClassificationModel inherit from the abstract MLModel.

Composition (*--): The AutoMLTrainer owns the Dataset (if the trainer is destroyed, the current training session's data context is gone).

Association (-->): The User uses the AuthManager to log in.

Aggregation (o--): The ModelRegistry stores valid MLModels (but models can exist independently in memory before saving).