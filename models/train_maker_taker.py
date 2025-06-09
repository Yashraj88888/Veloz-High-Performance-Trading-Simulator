import os
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, roc_auc_score
import joblib


csv_path = os.path.join(os.path.dirname(__file__), "../maker_taker_history.csv")
df = pd.read_csv(csv_path)



df["spread"] = df["best_ask"] - df["best_bid"]

#Aggressiveness: how deep into the spread the trade executed
def compute_aggr(row):
    if row["side"].lower() == "buy":
        return row["trade_price"] - row["best_bid"]
    else:
        return row["best_ask"] - row["trade_price"]

df["aggr"] = df.apply(compute_aggr, axis=1)
df["rel_aggr"] = df["aggr"] / df["spread"].replace(0, 1e-9)

# Depth ratio: trade size vs total top-5 depth
df["depth5"] = df["bid_depth5"] + df["ask_depth5"]
df["size_depth_ratio"] = df["trade_size"] / df["depth5"].replace(0, 1e-9)

#Prepare features/target
X = df[["rel_aggr", "size_depth_ratio"]]
y = df["is_taker"]

#Train/test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

#Train logistic regression
clf = LogisticRegression(max_iter=1000)
clf.fit(X_train, y_train)


y_pred = clf.predict(X_test)
y_prob = clf.predict_proba(X_test)[:, 1]
print(classification_report(y_test, y_pred))
print(f"ROC AUC: {roc_auc_score(y_test, y_prob):.4f}")


out_path = os.path.join(os.path.dirname(__file__), "maker_taker_model.pkl")
joblib.dump(clf, out_path, compress=3)
print(f"Saved classifier to {out_path}")
