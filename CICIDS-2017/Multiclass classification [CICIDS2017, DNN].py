import os
import glob
import time
import numpy as np
import pandas as pd
import seaborn as sn
import datetime as dt
import tensorflow as tf
import matplotlib.pyplot as plt

from os import path
from tensorflow import keras
from matplotlib.pyplot import *
from keras.models import Model
from sklearn.model_selection import train_test_split
from keras.layers import Input, Dense, Dropout, Flatten, Convolution1D, UpSampling1D, MaxPooling1D
from sklearn.preprocessing import OneHotEncoder, StandardScaler, LabelEncoder, label_binarize
from sklearn.metrics import confusion_matrix, precision_score, recall_score, accuracy_score, f1_score, multilabel_confusion_matrix

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
warnings.simplefilter(action='ignore', category=DeprecationWarning)

# gpus = tf.config.experimental.list_physical_devices('GPU')
# if gpus:
#   for gpu in gpus:
#     tf.config.experimental.set_memory_growth(gpu, True)
#     print(gpu, "\n")
# else:
#   print("No GPU device found")

# full dataset
path = r'/Users/ahmad/Documents/Master/Datasets/TrafficLabelling' # use your path
all_files = glob.glob(path + "/*.csv")
li = []
for filename in all_files:
    df = pd.read_csv(filename, encoding='cp1252', index_col=None, header=0)
    li.append(df)
    print("Read Completed for ", filename)
df = pd.concat(li, axis=0, ignore_index=True)
df = df.rename(columns={' Label': 'Label'})
# df.describe()
# df.head()
df.info()

print(df["Label"].value_counts())
print(df.shape)

data_clean = df.dropna().reset_index()
data_clean.drop_duplicates(keep='first', inplace = True)
data_clean['Label'].value_counts()
print("Read {} rows.".format(len(data_clean)))

data_clean=data_clean.drop('Flow ID',axis=1)
data_clean=data_clean.drop(' Source IP',axis=1)
data_clean=data_clean.drop(' Destination IP',axis=1)
data_clean=data_clean.drop(' Timestamp',axis=1)

data_clean.columns
data_clean = data_clean.dropna().reset_index()
labelencoder = LabelEncoder()
data_clean['Label'] = labelencoder.fit_transform(data_clean['Label'])
data_clean['Label'].value_counts()
print(data_clean.shape)

data_np = data_clean.to_numpy(dtype="float32")
data_np = data_np[~np.isinf(data_np).any(axis=1)]
X = data_np[:, :-1]
enc = OneHotEncoder()
Y = enc.fit_transform(data_np[:, -1].reshape(-1, 1)).toarray()

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

X_train, X_test, Y_train, Y_test = train_test_split(
    X_scaled, Y, test_size=0.1, random_state=33, shuffle=True)

_features = X.shape[1]
n_classes = Y.shape[1]

# DNN model
# Convolutional Encoder
input_img = Input(shape=(_features))

fc1 = Dense(256, activation='relu')(input_img)
do1 = Dropout(0.1)(fc1)

fc2 = Dense(128, activation='relu')(do1)
do2 = Dropout(0.1)(fc2)

fc3 = Dense(128, activation='relu')(do2)
do3 = Dropout(0.1)(fc3)

fc4 = Dense(n_classes, kernel_initializer='normal')(do3)

softmax = Dense(n_classes, activation='softmax', name='classification')(fc4)

model = Model(inputs=input_img, outputs=softmax)
model.summary()

opt = tf.keras.optimizers.legacy.Adam(learning_rate=0.0001)
model.compile(loss='categorical_crossentropy',optimizer=opt, metrics=['accuracy'])

start_fit = time.time()
history = model.fit(X_train, Y_train,
                              batch_size=128,
                              epochs=30,
                              verbose=True,
                              validation_data=(X_test, Y_test))    
end_fit = time.time()
fit_time = end_fit - start_fit
print("fit time: {:.2f} seconds".format(fit_time))

np.save('/Users/ahmad/Documents/Master/results/CICIDS-2017/History/[CICIDS2017] [DNN] Multiclass classification history.npy',history.history)

# Plot for training and validation loss
history_dict = history.history
loss_values = history_dict['loss']
val_loss_values = history_dict['val_loss']
acc = history_dict['accuracy']
val_acc = history_dict['val_accuracy']
start_by_epoch = 1
epochs = range(start_by_epoch, len(loss_values) + 1)

# Exploratory data analysis
plt.plot(epochs, acc[start_by_epoch-1:], label='Training accuracy', marker='x', markersize=2.5, mew=0.4, linewidth=0.8)
plt.plot(epochs, val_acc[start_by_epoch-1:], label='Validation accuracy', marker='x', markersize=2.5, mew=0.4, linewidth=0.8)
plt.xlabel('Epochs')
plt.ylabel('Accuracy')
plt.legend(['Training', 'Validation'], loc='lower right')
plt.grid()
ax = plt.gca()
plt.tight_layout()
ax.spines['bottom'].set_visible(True)
ax.spines['top'].set_visible(False)
ax.spines['left'].set_visible(False)
ax.spines['right'].set_visible(False)
plt.ylim(0.993,1)
plt.savefig('/Users/ahmad/Documents/Master/results/CICIDS-2017/figuers/[CICIDS2017] [DNN] Multiclass classification accuracy.eps', format='eps', dpi=1200)
plt.show()
plt.clf()

plt.plot(epochs, loss_values[start_by_epoch-1:], label='Training Loss', marker='x', markersize=2.5, mew=0.4, linewidth=0.8)
plt.plot(epochs, val_loss_values[start_by_epoch-1:], label='Validation Loss', marker='x', markersize=2.5, mew=0.4, linewidth=0.8)
plt.xlabel('Epochs')
plt.ylabel('Loss')
plt.legend(['Training', 'Validation'], loc='upper right')
plt.grid()
ax = plt.gca()
plt.tight_layout()
ax.spines['bottom'].set_visible(True)
ax.spines['top'].set_visible(False)
ax.spines['left'].set_visible(False)
ax.spines['right'].set_visible(False)
plt.ylim(0,0.025)
plt.savefig('/Users/ahmad/Documents/Master/results/CICIDS-2017/figuers/[CICIDS2017] [DNN] Multiclass classification loss.eps', format='eps', dpi=1200)
plt.show()
plt.clf()

start_time = time.time()
pred = model.predict(X_test)
end_time = time.time()

inference_time = end_time - start_time
print("Inference time: {:.2f} seconds".format(inference_time))

# Convert predictions classes to one hot vectors 
pred = np.argmax(pred,axis=1)
# Convert validation observations to one hot vectors
y_test = Y_test.argmax(axis=1)

print(pred.shape)
print(y_test.shape)

''' ROC curve'''
# y_t = y_test.copy()
# y_p_c = pred.copy()

# np.save('/Users/ahmad/Documents/Master/results/CICIDS-2017/History/[CICIDS2017] [DNN] Multiclass classification y_t.npy',y_t)
# np.save('/Users/ahmad/Documents/Master/results/CICIDS-2017/History/[CICIDS2017] [DNN] Multiclass classification y_p_c.npy',y_p_c)

# n_classes = len(np.unique(y_t))
# y_t = label_binarize(y_t, classes=np.arange(n_classes))
# y_p_c = label_binarize(y_p_c, classes=np.arange(n_classes))

# # Compute ROC curve and ROC area for each class
# fpr = dict()
# tpr = dict()
# roc_auc = dict()
# lw=0.8

# for i in range(n_classes):
#     fpr[i], tpr[i], _ = roc_curve(y_t[:, i], y_p_c[:, i])
#     roc_auc[i] = auc(fpr[i], tpr[i])


# # Compute micro-average ROC curve and ROC area
# fpr["micro"], tpr["micro"], _ = roc_curve(y_t.ravel(), y_p_c.ravel())
# roc_auc["micro"] = auc(fpr["micro"], tpr["micro"])

# # First aggregate all false positive rates
# all_fpr = np.unique(np.concatenate([fpr[i] for i in range(n_classes)]))

# # Then interpolate all ROC curves at this points
# mean_tpr = np.zeros_like(all_fpr)
# for i in range(n_classes):
#   mean_tpr += np.interp(all_fpr, fpr[i], tpr[i])

# # Finally average it and compute AUC
# mean_tpr /= n_classes

# fpr["macro"] = all_fpr
# tpr["macro"] = mean_tpr
# roc_auc["macro"] = auc(fpr["macro"], tpr["macro"])

# # Plot all ROC curves
# # plt.figure(figsize=(30,25))
# plt.figure(dpi=600, figsize=(10,7))
# lw = 0.8
# plt.plot(fpr["micro"], tpr["micro"],
#   label="micro-average ROC curve (area = {0:0.2f})".format(roc_auc["micro"]),
#   color="deeppink", linestyle=":", linewidth=0.8,)

# plt.plot(fpr["macro"], tpr["macro"],
#   label="macro-average ROC curve (area = {0:0.2f})".format(roc_auc["macro"]),
#   color="navy", linestyle=":", linewidth=0.8,)

# for i in range(n_classes):
#     plt.plot(fpr[i], tpr[i],lw=0.8,
#              label='ROC curve of class {0} (area = {1:0.2f})'
#              ''.format(i, roc_auc[i]))
# plt.plot([0, 1], [0, 1], 'k--', lw=0.8)
# plt.xlim([-0.05, 1.05])
# plt.ylim([-0.05, 1.05])
# plt.xlabel('FP Rate')
# plt.ylabel('TP Rate')
# plt.legend(loc="lower right")
# plt.grid()
# ax = plt.gca()
# plt.tight_layout()
# ax.spines['bottom'].set_visible(True)
# ax.spines['top'].set_visible(False)
# ax.spines['left'].set_visible(True)
# ax.spines['right'].set_visible(False)
# plt.savefig('/Users/ahmad/Documents/Master/results/CICIDS-2017/figuers/[CICIDS2017] [DNN] Multiclass classification roc.eps', format='eps', dpi=1200)
# plt.show()
# plt.clf()

score = metrics.accuracy_score(y_test, pred)
rscore = recall_score(y_test, pred, average='weighted')
ascore = precision_score(y_test, pred, average='weighted')
ascore_macro = precision_score(y_test, pred, average='macro')
f1score= f1_score(y_test, pred, average='weighted') #F1 = 2 * (precision * recall) / (precision + recall) for manual

print("Validation score: {}".format(score))
print("Recall score: {}".format(rscore))
print("Precision score: {}".format(ascore))
print("Precision score macro: {}".format(ascore_macro))
print("F1 Measure score: {}".format(f1score))

confMat = confusion_matrix(y_test, pred)
print(confMat)
cm_df = pd.DataFrame(confMat)
labels = ['BENIGN', 'Bot', 'DDoS', 'DoS GoldenEye', 'DoS Hulk', 'DoS Slowhttptest', 
          'DoS slowloris', 'FTP-Patator', 'Heartbleed', 'Infiltration', 'PortScan',
          'SSH-Patator', 'Web Attack – Brute Force', 'Web Attack – Sql Injection',
          'Web Attack – XSS']

plt.figure(figsize=(30,15))
sn.set(font_scale=2.4)
sn.heatmap(cm_df, annot=True, annot_kws={"size":22}, fmt='g', xticklabels=labels, yticklabels=labels, cmap='Blues')

#sn.heatmap(cm_df, annot=True, annot_kws={"size":12}, fmt='g', xticklabels=labels, yticklabels=labels)
plt.ylabel('Actual Class')
plt.xlabel('Predicted Class')   
plt.savefig('/Users/ahmad/Documents/Master/results/CICIDS-2017/figuers/[CICIDS2017] [DNN] Multiclass classification confusion matrix.eps', bbox_inches="tight", format='eps', dpi=1200) 
plt.show() 
# plt.figure(figsize = (30,25))
# sn.set(font_scale=2.4)
# sn.heatmap(confMat, annot=True, fmt='.2f',cmap='Blues')

TP = np.diagonal(confMat)
FP = confMat.sum(axis=0) - TP
FN = confMat.sum(axis=1) - TP
TN = confMat.sum() - (TP + FP + FN)

def _report(TN, FP, FN, TP):
    TPR = TP/(TP+FN) if (TP+FN)!=0 else 0
    TNR = TN/(TN+FP) if (TN+FP)!=0 else 0
    PPV = TP/(TP+FP) if (TP+FP)!=0 else 0
    report = {'TP': TP, 'TN': TN, 'FP': FP, 'FN': FN, 
              'TPR': TPR, 'Recall': TPR, 'Sensitivity': TPR,
              'TNR' : TNR, 'Specificity': TNR,
              'FPR': FP/(FP+TN) if (FP+TN)!=0 else 0,
              'FNR': FN/(FN+TP) if (FN+TP)!=0 else 0,
              'PPV': PPV, 'Precision': PPV,
              'F1 Score': 2*(PPV*TPR)/(PPV+TPR),
              'Accuracy': (TP+TN)/(TP+FP+FN+TN)
             }
    return report

def multi_classification_report(y_true, y_pred, labels=None, encoded_labels=True, as_frame=False):
    """
    Args:
        y_true (ndarray)
        y_pred (ndarray)
        labels (list)
        encoded_labels (bool): Need to be False if labels are not one hot encoded
        as_fram (bool): If True, return type will be DataFrame
        
    Return:
        report (dict)
    """
    
    conf_labels = None if encoded_labels else labels
    
    conf_mat = multilabel_confusion_matrix(y_test, y_pred, labels=conf_labels)
    report = dict()
    if labels == None:
        counter = np.arange(len(conf_mat))
    else:
        counter = labels
        
    for i, name in enumerate(counter):
        TN, FP, FN, TP = conf_mat[i].ravel()
        report[name] = _report(TN, FP, FN, TP)
    
    if as_frame:
        return pd.DataFrame(report)
    return report

def summarized_classification_report(y_true, y_pred, as_frame=False):
    """
    Args:
        y_true (ndarray)
        y_pred (ndarray)
        as_fram (bool): If True, return type will be DataFrame
        
    Return:
        report (dict)
    """

    report = dict()
    
    avg_list = ['micro', 'macro', 'weighted']
    for avg in avg_list:
        acc = accuracy_score(y_true, y_pred)
        pre = precision_score(y_true, y_pred, average=avg)
        re = recall_score(y_true, y_pred, average=avg)
        f1 = f1_score(y_true, y_pred, average=avg)
        report[avg] = {'Accuracy': acc,
                       'Precision': pre,
                       'Recall': re,
                       'F1 Score': f1}
    if as_frame:
        return pd.DataFrame(report)
    return report

mcr = multi_classification_report(y_test, pred, labels=labels, encoded_labels=True, as_frame=True)
scr = summarized_classification_report(y_test, pred, as_frame=True)

# proposed model
mcr.to_csv(r'/Users/ahmad/Documents/Master/results/csvs/CICIDS2017] [DNN] Multiclass classification report.csv')
scr.to_csv(r'/Users/ahmad/Documents/Master/results/csvs/[CICIDS2017] [DNN] Summarized multiclass classification report.csv')






















