import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
import matplotlib.pyplot as plt

# Generate data
x = np.linspace(0.01, 1, 100)  # Avoid log(0) which is undefined
y = np.log(x)

# Define the model
model = Sequential([
    Dense(10, input_dim=1, activation='relu'),  # Hidden layer with 10 neurons
    Dense(10, input_dim=1, activation='relu'),  # Hidden layer with 10 neurons
    Dense(1)  # Output layer with 1 neuron
])

# Compile the model
model.compile(optimizer='adam', loss='mean_squared_error')

# Train the model
model.fit(x, y, epochs=500, verbose=0)

# Predict using the model
y_pred = model.predict(x)

# Plot the results
plt.figure(figsize=(10, 6))
plt.plot(x, y, label='True log curve')
plt.plot(x, y_pred, label='Predicted log curve', linestyle='--')
plt.xlabel('x')
plt.ylabel('log(x)')
plt.legend()
plt.title('Estimating Log Curve using TensorFlow')
plt.show()
