from collections import namedtuple
import numpy as np
import matplotlib.pyplot as plt

from dlvc.models.linear import LinearClassifier
from dlvc.batches import BatchGenerator
from dlvc.test import Accuracy
from dlvc.datasets.pets import PetsDataset
from dlvc.dataset import Subset
import dlvc.ops as ops

TrainedModel = namedtuple('TrainedModel', ['model', 'accuracy'])


train_data = PetsDataset("cifar-10-batches-py/", Subset.TRAINING)
val_data = PetsDataset("cifar-10-batches-py/", Subset.VALIDATION)
test_data = PetsDataset('cifar-10-batches-py/', Subset.VALIDATION)


op = ops.chain([
    ops.vectorize(),
    ops.type_cast(np.float32),
    ops.add(-127.5),
    ops.mul(1/127.5),
])

train_batches = BatchGenerator(train_data, 50, False, op)
val_batches = BatchGenerator(val_data, 50, False, op)
test_batches = BatchGenerator(test_data, 50, False, op)

def train_model(lr: float, momentum: float) -> TrainedModel:
    '''
    Trains a linear classifier with a given learning rate (lr) and momentum.
    Computes the accuracy on the validation set.
    Returns both the trained classifier and accuracy.
    '''

    clf = LinearClassifier(input_dim=3072,  num_classes=train_data.num_classes(), lr=lr, momentum=momentum, nesterov=False)

    n_epochs = 10
    for i in range(n_epochs):
        for batch in train_batches:            
            clf.train(batch.data,batch.label)

    accuracy = Accuracy()
    for batch in val_batches:
        prediction = clf.predict(batch.data)
        accuracy.update(prediction, batch.label)


    return TrainedModel(clf, accuracy)


# grid search
## options
lr_options = [0.1, 0.01, 0.001, 0.0001]
momentum_options = [0, 0.1, 0.01, 0.001, 0.0001]
models = []
best_model = TrainedModel(None, Accuracy())



# loop over all combinations
for lr in lr_options:
    for momentum in momentum_options:
        print('Training with parameters: lr={}, momentum={}'.format(lr, momentum), end='\r')
        model = train_model(lr, momentum)
        models.append(model)

for model in models:
    if model.accuracy.__gt__(best_model.accuracy):
        best_model = model
    
test_accuracy = Accuracy()
for batch in test_batches:
    prediction = best_model.model.predict(batch.data)
    test_accuracy.update(prediction, batch.label)

print('Best Model:')
print('Parameters: lr={}, momentum={}'.format(best_model.model.lr, best_model.model.momentum))
print('Test Accuracy = {}'.format(test_accuracy.accuracy()))


fig = plt.figure()
ax = fig.gca(projection='3d')

# Make data.
X = np.array()
Y = np.array()
Z = np.array()

for model in models:
    X = np.append(model.model.lr)
    Y = np.append(model.model.momentum)
    Z = np.append(model.accuracy.accuracy())

# Plot the surface.
surf = ax.plot_surface(X, Y, Z, cmap=cm.coolwarm,
                       linewidth=0, antialiased=False)

# Customize the z axis.
ax.set_zlim(0., 1.)
ax.zaxis.set_major_formatter(FormatStrFormatter('%.02f'))

# Add a color bar which maps values to colors.
fig.colorbar(surf, shrink=0.5, aspect=5)

plt.savefig('accuracy_plot.png')