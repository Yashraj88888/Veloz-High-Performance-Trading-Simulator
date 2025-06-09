import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score
import joblib



df = pd.read_csv("slippage_history.csv")


df["slippage"] = (df["exec_price"] - df["mid_price_at_submit"]) / df["mid_price_at_submit"] 


features = ["spread", "depth5", "vol24h", "order_size"]
X = df[features]
y = df["slippage"]

#Split into train/test sets
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

#Train the OLS Linear Regression model
model = LinearRegression(n_jobs=-1)  
model.fit(X_train, y_train)         


y_pred = model.predict(X_test)
print("Test MAE:  ", mean_absolute_error(y_test, y_pred))  
print("Test R²:   ", r2_score(y_test, y_pred))             

#5‐fold cross‑validation
cv_r2 = cross_val_score(model, X, y, cv=5, scoring="r2").mean()
print("CV R²:     ", cv_r2)                               

#Serialize the trained model for production use
joblib.dump(model, "slippage_model.pkl", compress=3)       
