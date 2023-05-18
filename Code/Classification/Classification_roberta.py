# -*- coding: utf-8 -*-
"""685_CP_classification_roberta.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1R8zl4W5QlKOljkiqdr2CcJ__b0dDnuS_
"""

from google.colab import drive
drive.mount('/content/gdrive', force_remount=True)

!pip install datasets
from datasets import load_dataset

!pip install transformers

import pandas as pd
import sklearn
from sklearn import metrics

train_df = pd.read_csv('../Datasets/Classification/train-0.2.csv',sep = ',')
test_df = pd.read_csv('../Datasets/Classification/test-0.2.csv',sep = ',')

train_df = train_df.loc[:,['Hypothesis','Type','Source']]
train_df = train_df[train_df['Type'] !=  'CreativeParaphrase']
train_df['Type'].replace(['Metaphor', 'Idiom','Simile','Sarcasm'],[0,1,2,3], inplace=True)

test_df = test_df.loc[:,['Hypothesis','Type','Source']]
test_df = test_df[test_df['Type'] !=  'CreativeParaphrase']
test_df['Type'].replace(['Metaphor', 'Idiom','Simile','Sarcasm'],[0,1,2,3], inplace=True)

len(test_df
    )

import torch
import random
import numpy as np


# Confirm that the GPU is detected

assert torch.cuda.is_available()

# Get the GPU device name.
device_name = torch.cuda.get_device_name()
n_gpu = torch.cuda.device_count()
print(f"Found device: {device_name}, n_gpu: {n_gpu}")
device = torch.device("cuda")

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from google.colab import auth
from oauth2client.client import GoogleCredentials
# Authenticate and create the PyDrive client.
auth.authenticate_user()
gauth = GoogleAuth()
gauth.credentials = GoogleCredentials.get_application_default()
drive = GoogleDrive(gauth)
print('success!')

import os
import zipfile

# Download helper functions file
helper_file = drive.CreateFile({'id': '16HW-z9Y1tM3gZ_vFpJAuwUDohz91Aac-'})
helper_file.GetContentFile('helpers.py')
print('helper file downloaded! (helpers.py)')

from helpers import tokenize_and_format, flat_accuracy

train_df = train_df.sample(frac=1).reset_index(drop=True)

texts = train_df.Hypothesis.values
labels = train_df.Type.values

### tokenize_and_format() is a helper function provided in helpers.py ###
input_ids, attention_masks = tokenize_and_format(texts)

# Convert the lists into tensors.
input_ids = torch.cat(input_ids, dim=0)
attention_masks = torch.cat(attention_masks, dim=0)
labels = torch.tensor(labels)

test_df = test_df.sample(frac=1).reset_index(drop=True)

test_texts = test_df.Hypothesis.values
test_labels = test_df.Type.values

### tokenize_and_format() is a helper function provided in helpers.py ###
test_input_ids, test_attention_masks = tokenize_and_format(test_texts)

# Convert the lists into tensors.
test_input_ids = torch.cat(test_input_ids, dim=0)
test_attention_masks = torch.cat(test_attention_masks, dim=0)
test_labels = torch.tensor(test_labels)

# Print sentence 0, now as a list of IDs.
print('Original: ', texts[0])
print('Token IDs:', input_ids[0])

train_total = len(train_df)
test_total = len(test_df)
num_train = int(train_total * .9)
num_val = int(train_total * .1)

# make lists of 3-tuples (already shuffled the dataframe in cell above)

train_set = [(input_ids[i], attention_masks[i], labels[i]) for i in range(num_train)]
val_set = [(input_ids[i], attention_masks[i], labels[i]) for i in range(num_train, num_val+num_train)]
train_set_total = [(input_ids[i], attention_masks[i], labels[i]) for i in range(train_total)]

test_set = [(test_input_ids[i], test_attention_masks[i], test_labels[i]) for i in range(test_total)]

train_text = [texts[i] for i in range(num_train)]
val_text = [texts[i] for i in range(num_train, num_val+num_train)]
train_text_total = [texts[i] for i in range(train_total)]
test_text = [test_texts[i] for i in range(test_total)]

from transformers import RobertaForSequenceClassification, AdamW, BertConfig

model = RobertaForSequenceClassification.from_pretrained(
    "roberta-base", # Use the 12-layer BERT model, with an uncased vocab.
    num_labels = 4, # The number of output labels.   
    output_attentions = False, # Whether the model returns attentions weights.
    output_hidden_states = False, # Whether the model returns all hidden-states.
)

# Tell pytorch to run this model on the GPU.
model.cuda()

batch_size = 64
optimizer = AdamW(model.parameters(),
                  lr = 2e-5, # args.learning_rate - default is 5e-5
                  eps = 1e-8, # args.adam_epsilon  - default is 1e-8
                  correct_bias = True
                )
epochs = 30



# function to get validation accuracy
# ADDED A PARAMETER FOR THE TEXT WHOSE PERFORMANCE IS BEING TESTED FOR FURTHER ANALYSIS
def get_validation_performance(val_set,val_text):
    # Put the model in evaluation mode
    model.eval()

    # Tracking variables 
    total_eval_accuracy = 0
    total_eval_loss = 0

    num_batches = int(len(val_set)/batch_size) + 1

    total_correct = 0

    for i in range(num_batches):

      end_index = min(batch_size * (i+1), len(val_set))

      batch = val_set[i*batch_size:end_index]
      
      if len(batch) == 0: continue

      input_id_tensors = torch.stack([data[0] for data in batch])
      input_mask_tensors = torch.stack([data[1] for data in batch])
      label_tensors = torch.stack([data[2] for data in batch])
      
      # Move tensors to the GPU
      b_input_ids = input_id_tensors.to(device)
      b_input_mask = input_mask_tensors.to(device)
      b_labels = label_tensors.to(device)
        
      # Tell pytorch not to bother with constructing the compute graph during
      # the forward pass, since this is only needed for backprop (training).
      with torch.no_grad():        

        # Forward pass, calculate logit predictions.
        outputs = model(b_input_ids, 
                                token_type_ids=None, 
                                attention_mask=b_input_mask,
                                labels=b_labels)
        loss = outputs.loss
        logits = outputs.logits
            
        # Accumulate the validation loss.
        total_eval_loss += loss.item()
        
        # Move logits and labels to CPU
        logits = logits.detach().cpu().numpy()
        label_ids = b_labels.to('cpu').numpy()

        # Calculate the number of correctly labeled examples in batch
        pred_flat = np.argmax(logits, axis=1).flatten()
        labels_flat = label_ids.flatten()
        # ADDED CODE TO PRINT THE INCORRECTLY PREDICTED SENTENCE
        #for j in range(len(pred_flat)):
          #if pred_flat[j] != labels_flat[j]:
            #print(f"Incorrectly predicted text: {val_text[i*batch_size+j]}; pred:{pred_flat[j]} ; GT:{labels_flat[j]}")
        num_correct = np.sum(pred_flat == labels_flat)
        total_correct += num_correct
        
    # Report the final accuracy for this validation run.
    avg_val_accuracy = total_correct / len(val_set)
    return avg_val_accuracy

# training loop

# For each epoch...
for epoch_i in range(0, epochs):
    # Perform one full pass over the training set.

    print("")
    print('======== Epoch {:} / {:} ========'.format(epoch_i + 1, epochs))
    print('Training...')

    # Reset the total loss for this epoch.
    total_train_loss = 0

    # Put the model into training mode.
    model.train()

    # For each batch of training data...
    num_batches = int(len(train_set_total)/batch_size) + 1

    for i in range(num_batches):
      end_index = min(batch_size * (i+1), len(train_set_total))

      batch = train_set[i*batch_size:end_index]

      if len(batch) == 0: continue

      input_id_tensors = torch.stack([data[0] for data in batch])
      input_mask_tensors = torch.stack([data[1] for data in batch])
      label_tensors = torch.stack([data[2] for data in batch])

      # Move tensors to the GPU
      b_input_ids = input_id_tensors.to(device)
      b_input_mask = input_mask_tensors.to(device)
      b_labels = label_tensors.to(device)

      # Clear the previously calculated gradient
      model.zero_grad()        

      # Perform a forward pass (evaluate the model on this training batch).
      outputs = model(b_input_ids, 
                            token_type_ids=None, 
                            attention_mask=b_input_mask, 
                            labels=b_labels)
      loss = outputs.loss
      logits = outputs.logits

      total_train_loss += loss.item()

      # Perform a backward pass to calculate the gradients.
      loss.backward()

      # Update parameters and take a step using the computed gradient.
      optimizer.step()
        
    # ========================================
    #               Validation
    # ========================================
    # After the completion of each training epoch, measure our performance on
    # our validation set. Implement this function in the cell above.
    print(f"Total loss: {total_train_loss}")
    #val_acc = get_validation_performance(val_set,val_text)
    #print(f"Validation accuracy: {val_acc}")          
    
print("")
print("Training complete!")

get_validation_performance(test_set,test_text)

path = os.path.join('../Models', "roberta-CF-0.03")
model.save_pretrained(path)