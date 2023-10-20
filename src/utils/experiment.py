from .. import config

import sys
import pickle
import importlib

sys.path.append('..')
#from utils import data_handler
from src.utils import data_handler
from src import config
from src.utils import visualisation, benchmark, helpers, monitoring
from src.models import torch_CVAE


# data manipulation
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# data analysis
from sklearn.model_selection import train_test_split
from sklearn.decomposition import PCA

# pytorch specific
import torch
import torch.optim as optim
import torch.nn.functional as F
from tqdm import tqdm

DEVICE = torch.device(config["DEVICE"])



from sklearn.cluster import KMeans
from sklearn import datasets
from sklearn.metrics import silhouette_score
import matplotlib.pyplot as plt

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix, adjusted_rand_score, normalized_mutual_info_score, fowlkes_mallows_score, homogeneity_completeness_v_measure




class Experiment():
    def build_dataset(self, data_param):
        self.data, self.metadata = data_handler.generate_dataset_BRCA(**data_param)
        self.input_shape = len(self.metadata["feature_names"])
        print("input shape :", self.input_shape)

    def build_model(self, shape, model_param):
        self.model = torch_CVAE.Autoencoder(shape = shape, **model_param)
        self.model.add_attention()


    def __init__(self, data_param, model_param, verbose = 0, n_epoch = 3000):
        self.data_param = data_param
        self.model_param = model_param
        self.verbose = verbose
        self.n_epoch = n_epoch
        self.data = None
        self.input_shape = None

        self.meta_data = None
        self.model = None
        self.metric = None
        
        self.build_dataset(data_param)
        # here we need to capture the shape of the input before building the model.
        self.build_model(shape = self.input_shape, model_param = model_param)
        self.optimizer = optim.Adam(self.model.parameters(), lr=1e-4, amsgrad=False)
        self.data_set, self.dataloader = helpers.format_dataset(self.data, self.metadata)

        self.monitor = monitoring.Monitor(self.model, self.dataloader, label = self.metadata["subtypes"])
        self.callbacks = self.monitor.callbacks
        self.scheduler = optim.lr_scheduler.ReduceLROnPlateau(self.optimizer, 'min', min_lr= 1e-5)


    
        
    def run(self):
        self.model.to(DEVICE)
        for epoch in tqdm(range(self.n_epoch)):
            running_loss = 0.0
            count = 0
            
            # Training loop
            for _, inputs in enumerate(self.dataloader):
                self.optimizer.zero_grad()
                inputs = inputs.to(DEVICE)
                # Compute the VAE loss or standard loss
                if self.model.is_variational:
                    outputs, mu, log_var = self.model(inputs)
                    reconstruction_loss = F.mse_loss(outputs, inputs)
                    kld = -0.5 * torch.sum(1 + log_var - mu.pow(2) - log_var.exp())
                    loss = reconstruction_loss + (1 * kld)
                else:
                    outputs = self.model(inputs)
                    loss = F.mse_loss(outputs, inputs)
                
                loss.backward()
                self.optimizer.step()
                count += 1
                running_loss += loss.item()
            
            # Calculate and store training loss for this epoch
            train_loss = running_loss / count
            self.monitor.append_loss(train_loss)
            self.callbacks(epoch)
        

        encode_out, reconstruction_out = helpers.encode_recon_dataset(self.dataloader, self.model, DEVICE)

        # PCA of the latent space
        pca = PCA(n_components=2)
        pca.fit(encode_out)
        pca_result = pca.transform(encode_out)


        # Assuming you've determined that you want 5 clusters
        n_clusters = 5

        # Initialize the KMeans model
        kmeans = KMeans(n_clusters=n_clusters)

        # Fit the model on your data
        kmeans.fit(encode_out)

        # Get the cluster assignments
        labels = kmeans.labels_

        # Calculate silhouette score
        silhouette_avg = silhouette_score(encode_out, labels)

        # Visualization: Assuming you have 2D data, you can also visualize the clusters:
        # (This is for illustration. If your data is not 2D, additional steps are needed for plotting, like PCA to reduce dimensions before plotting.)


        


        plt.show()
        if self.verbose >= 1:
            print(f"Silhouette score for {n_clusters} clusters: {silhouette_avg}")

            fig, axs = plt.subplots(1, 2, figsize=(12, 6))

            sns.scatterplot(x=pca_result[:, 0], y=pca_result[:, 1], hue=[str(l) for l in labels], ax=axs[0])
            sns.scatterplot(x=pca_result[:, 0], y=pca_result[:, 1], hue=self.metadata["subtypes"], ax=axs[1])
            plt.show()

        


        # These are your cluster labels and true labels.
        # They should be assigned with your actual data.
        y_pred = labels  # replace with your actual labels
        y_true = self.metadata["subtypes"]  # replace with your actual clustering results


        # Filter out None values
        y_pred = [label for label, test in zip(y_pred, y_true) if test is not None]
        y_true = [label for label in y_true if label is not None]
        X_filtered = [x for x, test in zip(encode_out, y_true) if test is not None]
        # Ensure you apply the same filter to the associated data if needed



        # Because your labels might not be integers, or might not start from zero, or not consecutive, we create mappings to ensure the confusion matrix is created correctly.
        true_labels = np.unique(y_true)
        pred_labels = np.unique(y_pred)

        # Create a mapping for true labels
        true_label_mapping = {label: idx for idx, label in enumerate(true_labels)}
        y_true_mapped = np.array([true_label_mapping[label] for label in y_true])

        # Create a mapping for predicted labels
        pred_label_mapping = {label: idx for idx, label in enumerate(pred_labels)}
        y_pred_mapped = np.array([pred_label_mapping[label] for label in y_pred])

        # Calculate confusion matrix
        conf_matrix = confusion_matrix(y_true_mapped, y_pred_mapped)

        ari_score = adjusted_rand_score(y_true, y_pred)
        nmi_score = normalized_mutual_info_score(y_true, y_pred, average_method='arithmetic')
        fm_score = fowlkes_mallows_score(y_true, y_pred)  # or use y_true_filtered, y_pred_filtered
        homogeneity, completeness, v_measure = homogeneity_completeness_v_measure(y_true, y_pred)  # or use y_true_filtered, y_pred_filtered


        if(self.verbose >= 1):
            # Plot the confusion matrix
            plt.figure(figsize=(10, 8))
            sns.heatmap(conf_matrix, annot=True, fmt="d", cmap="Blues", xticklabels=pred_labels, yticklabels=true_labels)
            plt.ylabel('True Label')
            plt.xlabel('Clustered Label')
            plt.title('Confusion Matrix')
            plt.show()

            # Calculate Adjusted Rand Index (ARI)
            print(f"Adjusted Rand Index (ARI): {ari_score:.2f}")

            # Calculate Normalized Mutual Information (NMI)
            print(f"Normalized Mutual Information (NMI): {nmi_score:.2f}")

            # Calculate Fowlkes-Mallows Index
            print(f"Fowlkes-Mallows Index: {fm_score:.2f}")

            # Calculate Homogeneity, Completeness, and V-measure
            print(f"Homogeneity: {homogeneity:.2f}")
            print(f"Completeness: {completeness:.2f}")
            print(f"V-measure: {v_measure:.2f}")

            print(f"Silhouette Score: {silhouette_avg:.2f}")


        self.metric = ari_score


