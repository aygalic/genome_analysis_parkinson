import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd 

import plotly.express as px
import plotly.subplots as sp
import plotly.graph_objs as go




# from vq-vae
from sklearn.metrics import classification_report, silhouette_score, silhouette_samples
from sklearn.decomposition import PCA
from sklearn import metrics
from sklearn.manifold import TSNE
from sklearn.datasets import make_blobs
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

# experimental
import matplotlib.gridspec as gridspec


# this function is used in the dataset analysis. it plots the whole dataset as a heatmap, 
# as well as the density of total expression of genes
def dataset_plot(data):

    # get everything out of TensorFlow back to numpy/pandas
    data = np.concatenate(list(data.as_numpy_iterator()), axis=0)


    # Create a single figure with two subplots
    plt.figure(figsize=(12, 6))

    #plt.subplots(1, 2, figsize=(12, 6))
    plt.subplot(1, 2, 1)
    sns.heatmap(data, yticklabels=False, xticklabels=False, cbar=True)
    plt.title('Gene expression plot')
    plt.xlabel('Genes')
    plt.ylabel('Cells')


    # Create the KDE plot in the second subplot
    plt.subplot(1, 2, 2)  # Create a new subplot for the KDE plot
    sns.kdeplot(data.sum(axis=0))
    plt.title('Density of total expression throughout the dataset for each Gene')
    plt.xlabel('Sum of Expression')
    plt.ylabel('Density')



    plt.tight_layout()  # Ensure plots don't overlap
    plt.show()

# plot a single observation, its latent space as well as its reconstruction
def plot_single_obs_processing(x_train, autoencoder):
    
    e = iter(x_train).next()
    
    if(autoencoder._is_variational == True):
        _,__, z = autoencoder.encoder(e)
    else :
        z = autoencoder.encoder(e)

    decoded = autoencoder.decoder(z)


    if(x_train._is_time_series):
        e_ = e[0]  
        z_ = z[0].reshape(1, -1) 
        decoded_ = decoded[0]  
    else:
        e_ = e[0].reshape(1, -1) 
        z_ = z[0].reshape(1, -1) 
        decoded_ = decoded[0].reshape(1, -1) 



    # Create subplot grid with vertical stacking
    fig = sp.make_subplots(rows=3, cols=1, shared_xaxes=False, vertical_spacing=0.1)

    # Add the original image as a heatmap-like plot
    heatmap_trace1 = go.Heatmap(z=e_, colorscale='viridis')
    fig.add_trace(heatmap_trace1, row=1, col=1)

    # Add the latent representation as a heatmap-like plot
    heatmap_trace2 = go.Heatmap(z=z_, colorscale='viridis')
    fig.add_trace(heatmap_trace2, row=2, col=1)

    # Add the decoded image as a heatmap-like plot
    heatmap_trace3 = go.Heatmap(z=decoded_, colorscale='viridis')
    fig.add_trace(heatmap_trace3, row=3, col=1)

    # Update layout
    fig.update_layout(title='Stacked Graph of Image and Latent Space', showlegend=False)

    fig.show()



# plot the whole , its latent representation as well as its reconstruction
def plot_dataset_processing(x_train, autoencoder):

    # get everything out of TensorFlow back to numpy/pandas
    data = np.concatenate(list(x_train.as_numpy_iterator()), axis=0)

    if(autoencoder._is_variational == True):
        _,__, z = autoencoder.encoder(data)
    else :
        z = autoencoder.encoder(data)



    reconstruction = autoencoder.decoder.predict(z)


    if(x_train._is_time_series):
        data = data.reshape(data.shape[0], data.shape[2]*data.shape[1])
        reconstruction = reconstruction.reshape(reconstruction.shape[0], reconstruction.shape[2]*reconstruction.shape[1])
 

    # Create a single figure with two subplots
    plt.figure(figsize=(18, 6))

    plt.subplot(1, 3, 1)
    sns.heatmap(data, yticklabels=False, xticklabels=False, cbar=True)
    # sns.clustermap(data,yticklabels=False,xticklabels=False) # IF I WANT CLUSTERS

    plt.title('Gene expression plot')
    plt.xlabel('Genes')
    plt.ylabel('Cells')

    plt.subplot(1, 3, 2)
    sns.heatmap(z, yticklabels=False, xticklabels=False, cbar=True)
    plt.title('Latent representaiton plot')
    plt.xlabel('Latent variables')
    plt.ylabel('Cells')

    plt.subplot(1, 3, 3)
    sns.heatmap(reconstruction, yticklabels=False, xticklabels=False, cbar=True)
    plt.title('Reconstruction - Gene expression plot')
    plt.xlabel('Genes')
    plt.ylabel('Cells')


    plt.tight_layout()  # Ensure plots don't overlap
    plt.show()


def plot_clusters(latent_Z, True_labels, TSNE_params = None):
    True_labels = pd.DataFrame(True_labels)

    #### TSNE
    if (TSNE_params == None) :
        TSNE_params = {
            "early_exaggeration" : 50,
            "learning_rate" : 500, 
            "perplexity" : 15, 
            "min_grad_norm" : 1e-7, 
            "n_iter" : 5000,
            "n_components" : 2
        }
    tsne = TSNE(**TSNE_params).fit_transform(latent_Z)
    x_min, x_max = np.min(tsne, 0), np.max(tsne, 0)
    tsne = tsne / (x_max - x_min)

    TSNE_result = pd.DataFrame(tsne, columns=['TSNE_Dim1', 'TSNE_Dim2'])
    TSNE_result['Subtype'] = True_labels


    # Map string labels to numeric values
    my_cmap = plt.get_cmap('viridis', len(TSNE_result['Subtype'].unique()))
    subtype_labels = TSNE_result['Subtype'].unique()
    subtype_to_numeric = {subtype: i for i, subtype in enumerate(subtype_labels)}
    colors = [my_cmap(subtype_to_numeric[subtype]) for subtype in TSNE_result['Subtype']]


    #### PCA of learened feature
    pca = PCA(n_components=2)
    pca.fit(latent_Z)
    print(pca.explained_variance_ratio_)
    print(pca.explained_variance_)
    pca_result = pca.transform(latent_Z)


    # Create a figure with two subplots
    fig, axes = plt.subplots(1, 2, figsize = (12,6))

    # Plot the first subplot (tsne)
    sns.scatterplot(data=TSNE_result, x='TSNE_Dim1', y='TSNE_Dim2', hue='Subtype', s=70, ax=axes[0])
    axes[0].set_xlabel("TSNE_Dim1")
    axes[0].set_ylabel("TSNE_Dim2")

    # Plot the second subplot (PCA)
    a = axes[1].scatter(pca_result[:, 0], pca_result[:, 1], marker='o', cmap=my_cmap, c=colors, s=20)
    axes[1].set_xlabel("PCA_dim1")
    axes[1].set_ylabel("PCA_dim2")

    plt.tight_layout()
    plt.show()

    #### Joinplot
    f = sns.jointplot(x=TSNE_result.TSNE_Dim1, y=TSNE_result.TSNE_Dim2, cmap="Blues", fill=True, kind='kde',height=6,
                 marginal_kws={"alpha":.2},thresh=0.05, alpha=.8)

    #### blobs 
    f = sns.jointplot(x=TSNE_result.TSNE_Dim1, y=TSNE_result.TSNE_Dim2, fill=True, kind='kde',hue=TSNE_result.Subtype,height=6,marginal_kws={"alpha":.2},thresh=0.05, alpha=.9)
    f.ax_joint.legend_._visible=False
