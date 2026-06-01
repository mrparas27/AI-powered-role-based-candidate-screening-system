import numpy as np
from sqlalchemy.orm import Session
from backend.app.db import SessionLocal, init_db, KnowledgeChunkModel
from backend.app.rag import generate_embedding

# Textbook and Technical Data to Seed
SEED_DATA = [
    # ==== AI & ML ROLE TEXTBOOKS ====
    {
        "role_type": "ai_ml",
        "file_name": "Machine_Learning_Tom_Mitchell.txt",
        "chunks": [
            "Chapter 3: Decision Tree Learning. Decision tree learning is a method for approximating discrete-valued target functions, in which the learned function is represented by a decision tree. It is robust to noisy data and capable of learning disjunctive expressions. The core algorithm is ID3, which learns decision trees by constructing them top-down. The fundamental selection metric is Information Gain, based on the entropy measure from information theory. Entropy characterizes the impurity of an arbitrary collection of examples. Entropy(S) = - p_+ log_2 p_+ - p_- log_2 p_- where p_+ is the proportion of positive examples and p_- is the proportion of negative examples. Information Gain measures the expected reduction in entropy caused by partitioning the examples according to an attribute.",
            "Chapter 4: Artificial Neural Networks. Neural networks provide a robust approach to approximating real-valued, vector-valued, and discrete-valued target functions. The basic building block is the Perceptron, which takes a vector of real-valued inputs, calculates a linear combination of them, and outputs a 1 if the result is greater than some threshold, and -1 otherwise. To handle non-linear decision boundaries, Multi-layer Networks use sigmoid units. Sigmoid units calculate a linear combination of inputs and apply the continuous, differentiable logistic function: 1 / (1 + e^-net). Backpropagation is the standard training algorithm, employing gradient descent in the weight space to minimize the sum of squared errors between network outputs and target values.",
            "Chapter 6: Bayesian Learning. Bayesian learning algorithms are calculated based on probability theory. The core principle is Bayes Theorem: P(A|B) = P(B|A) * P(A) / P(B). In machine learning, we search for the Maximum A Posteriori (MAP) hypothesis: h_MAP = argmax P(D|h) * P(h). If we assume every hypothesis is equally likely, we seek the Maximum Likelihood (ML) hypothesis: h_ML = argmax P(D|h). The Naive Bayes Classifier assumes that attribute values are conditionally independent given the target value, which simplifies the joint probability calculation: P(a_1, a_2 ... a_n | v_j) = product P(a_i | v_j).",
            "Chapter 8: Instance-Based Learning. Instance-based learning methods, such as Nearest Neighbor (K-NN) and locally weighted regression, are lazy learning methods that delay generalization until a new query is received. In K-Nearest Neighbors, the classifier identifies the K instances closest to the query point based on Euclidean distance, and assigns the majority label of these neighbors. Locally weighted regression constructs a local approximation of the target function using nearby data weighted by distance. The main advantages are simple training and capability to represent complex target functions. The main disadvantage is high computational cost during classification and susceptibility to the curse of dimensionality."
        ]
    },
    {
        "role_type": "ai_ml",
        "file_name": "Hundred_Page_ML_Book_Andriy_Burkov.txt",
        "chunks": [
            "Chapter 3: Fundamental Algorithms - Support Vector Machines (SVM). SVM is a supervised learning algorithm that finds the optimal hyperplane that maximizes the margin between two classes. The margin is the distance between the separating hyperplane and the closest data points, called Support Vectors. For non-linearly separable data, SVM uses the Kernel Trick (such as RBF, polynomial kernels) to project features into a higher-dimensional space where a linear boundary can separate them. The optimization problem is solved using Lagrange multipliers and quadratic programming. The objective is to minimize 1/2 * ||w||^2 subject to the classification constraint, with slack variables C added to control the penalty for misclassified points (Soft Margin SVM).",
            "Chapter 5: Gradient Descent and Optimization. Gradient descent is a first-order iterative optimization algorithm used to minimize a loss function. It works by updating the weights in the opposite direction of the gradient of the loss function with respect to the weights: w = w - alpha * grad(L), where alpha is the learning rate. Stochastic Gradient Descent (SGD) updates weights after each individual sample, making it faster but noisy. Mini-batch Gradient Descent strikes a balance by updating weights using small batches of data. Advanced optimizers like Adam, RMSprop, and AdaGrad adjust the learning rate dynamically based on moving averages of past gradients and squared gradients.",
            "Chapter 7: Ensemble Learning. Ensemble methods combine multiple base models to create a stronger predictor. Bagging (Bootstrap Aggregating) trains multiple base estimators (like decision trees) in parallel on different bootstrapped samples of the training data and averages their predictions. Random Forest is an extension of bagging that additionally selects a random subset of features at each split to de-correlate the trees. Boosting trains models sequentially, where each new model focuses on correcting the errors made by previous models. Examples include Gradient Boosting Machines (GBM), XGBoost, and AdaBoost. Stacking combines diverse models using a meta-model that learns to combine their outputs."
        ]
    },
    # ==== DATA SCIENCE & APPLIED ML ROLE TEXTBOOKS ====
    {
        "role_type": "data_science",
        "file_name": "Intro_to_ML_with_Python_Muller.txt",
        "chunks": [
            "Chapter 2: Supervised Learning - Scikit-Learn API. The scikit-learn library provides a consistent API for building machine learning pipelines. Every estimator implements a fit(X, y) method to train the model, and a predict(X) method to make predictions. Features must be represented as a 2D NumPy array or Pandas DataFrame of shape (n_samples, n_features), and targets as a 1D array. Common preprocessing steps include MinMaxScaler (scaling features between 0 and 1) and StandardScaler (standardizing features to have zero mean and unit variance). Preprocessing must fit on the training set and transform both training and testing sets.",
            "Chapter 5: Model Evaluation and Improvement. Grid Search and Cross-Validation are vital for hyperparameter tuning. K-Fold Cross-Validation splits the dataset into K equal parts, training the model K times using K-1 folds as training data and the remaining fold for validation, which prevents overfitting to a single train-test split. Stratified K-Fold is used for classification to keep target class proportions equal across folds. Grid Search (GridSearchCV) automates evaluating a grid of parameter combinations using cross-validation to select the set of hyperparameters that maximize performance metrics (such as F1-score, ROC AUC, Precision, or Recall).",
            "Chapter 6: Pipelines and Feature Engineering. The Pipeline class in scikit-learn chains multiple preprocessing steps and an estimator into a single object. This prevents data leakage during cross-validation, as preprocessing parameters (like mean and variance from StandardScaler) are computed strictly inside each training fold and not across the entire dataset. Feature engineering techniques include one-hot encoding for categorical variables, polynomial features for capturing non-linear relationships, and binning to discretize continuous features."
        ]
    },
    {
        "role_type": "data_science",
        "file_name": "Master_ML_Algorithms_Brownlee.txt",
        "chunks": [
            "Chapter 4: Linear Regression and Logistic Regression. Linear Regression models the relationship between a scalar dependent variable y and one or more explanatory variables X using a linear function: y = beta_0 + beta_1 * X + e. Coefficients are estimated using Ordinary Least Squares (OLS) or Gradient Descent. Logistic Regression is used for binary classification, modeling the probability of the positive class using the logistic sigmoid function: p = 1 / (1 + e^-z) where z = beta_0 + beta_1 * X. The model parameters are estimated using Maximum Likelihood Estimation (MLE) to minimize the cross-entropy loss function.",
            "Chapter 10: Naive Bayes and Linear Discriminant Analysis (LDA). LDA is a classification method that assumes the input data features are normally distributed with the same covariance matrix across classes. LDA calculates Bayes theorem probabilities directly for each class, projecting data into a lower-dimensional space to maximize class separability. Naive Bayes simplifies this by assuming class-conditional independence of all features: P(X|class) = product P(x_i|class). It is fast, works well with text classification, but suffers if the independence assumption is severely violated.",
            "Chapter 15: Random Forest and Boosting Algorithms. Classification and Regression Trees (CART) are the basis of ensemble models. In Random Forests, variance is reduced by averaging the results of deep, unpruned decision trees trained on bootstrap samples, combined with random feature selection. In Gradient Boosting, bias is reduced by fitting shallow trees sequentially to the negative gradients (pseudo-residuals) of the loss function. Learning rate (shrinkage) is applied to scale the contribution of each tree to prevent overfitting."
        ]
    },
    # ==== BACKEND ROLE ENGINEERING CONCEPTS ====
    {
        "role_type": "backend",
        "file_name": "Backend_System_Design_Fundamentals.txt",
        "chunks": [
            "API Design: REST vs GraphQL. Representational State Transfer (REST) is an architectural style that relies on stateless, client-server communication using HTTP protocols. RESTful APIs represent resources as URIs (e.g. /api/users) and interact with them using standard HTTP methods: GET (read), POST (create), PUT (replace), PATCH (modify), and DELETE. REST APIs must respect constraints like uniform interface and statelessness. GraphQL is a query language for APIs that allows clients to request exactly the fields they need, reducing over-fetching and under-fetching, using a single endpoint (POST /graphql) and schema definitions.",
            "Database Indexing: B-Trees and Hash Indexes. An index is a database structure designed to speed up retrieval operations at the cost of additional storage and write performance overhead. B-Trees are self-balancing search trees that store sorted keys and support range queries, point lookups, and sorting in logarithmic O(log N) time. Hash Indexes use hash tables to map keys directly to row pointers, offering constant O(1) time complexity for exact lookups, but they do not support range queries. Database systems must carefully select columns to index, since every INSERT, UPDATE, or DELETE requires updating the indexes.",
            "Database Transactions and ACID Properties. A database transaction is a sequence of database operations executed as a single logical unit. Databases enforce ACID properties to guarantee data integrity: Atomicity (all operations succeed or all fail/rollback), Consistency (transactions transition database from one valid state to another, respecting constraints), Isolation (concurrent transactions execute independently without interference, managed via isolation levels like Read Committed, Repeatable Read, and Serializable), and Durability (once committed, changes survive system failures).",
            "Concurrency and Race Conditions. In multi-threaded backend applications, race conditions occur when multiple threads access and mutate shared resources concurrently, causing unpredictable data states. Solutions include Pessimistic Locking (blocking access to rows or resources using locks, like SELECT FOR UPDATE), Optimistic Locking (verifying data hasn't changed before updating using a version column, returning an error if a conflict is detected), and Distributed Locks (using services like Redis with Redlock or ZooKeeper to coordinate locks across multiple server nodes)."
        ]
    }
]

def seed_database():
    """Seeds the database with technical concepts for all roles."""
    init_db()
    db = SessionLocal()
    
    # Check if database is already seeded
    existing_chunks = db.query(KnowledgeChunkModel).count()
    if existing_chunks > 0:
        print(f"Database already contains {existing_chunks} chunks. Skipping seeding.")
        db.close()
        return

    print("Seeding textbook summaries and technical knowledge base...")
    total_inserted = 0
    
    for book in SEED_DATA:
        role_type = book["role_type"]
        file_name = book["file_name"]
        chunks = book["chunks"]
        
        print(f"Processing {file_name} for role {role_type}...")
        for i, chunk_text in enumerate(chunks):
            # Generate embedding
            print(f"  Generating embedding for chunk {i+1}/{len(chunks)}...")
            embedding = generate_embedding(chunk_text)
            embedding_blob = np.array(embedding, dtype=np.float32).tobytes()
            
            db_chunk = KnowledgeChunkModel(
                chunk_text=chunk_text,
                file_name=file_name,
                role_type=role_type,
                embedding=embedding_blob
            )
            db.add(db_chunk)
            total_inserted += 1
            
    db.commit()
    db.close()
    print(f"Successfully seeded database with {total_inserted} high-quality chunks!")

if __name__ == "__main__":
    seed_database()
