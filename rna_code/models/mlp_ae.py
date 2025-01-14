"""Multi layer perceptron implementation for Autoencoder"""

import torch.nn as nn

from .autoencoder import Autoencoder


class MLPAutoencoder(Autoencoder):
    """Multi Layer Perceptron based Auto encoder."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layer_sizes = (
            [self.input_shape]
            + [2048 // (2**i) for i in range(self.num_layers - 1)]
            + [self.latent_dim]
        )

    def build_encoder(self):
        """Build encoder."""
        encoder_layers = []
        for i in range(self.num_layers):
            encoder_layers.extend(
                [
                    nn.Linear(self.layer_sizes[i], self.layer_sizes[i + 1]),
                    nn.LeakyReLU(self.slope),
                    nn.Dropout(self.dropout),
                ]
            )
        self.encoder = nn.Sequential(*encoder_layers)

    def build_decoder(self):
        """Build decoder."""
        decoder_layers = []
        self.layer_sizes.reverse()
        for i in range(self.num_layers):
            decoder_layers.extend(
                [
                    nn.Linear(self.layer_sizes[i], self.layer_sizes[i + 1]),
                    nn.LeakyReLU(self.slope),
                    nn.Dropout(self.dropout),
                ]
            )
        decoder_layers.append(
            nn.Linear(self.layer_sizes[-1], self.layer_sizes[-1]),
        )
        decoder_layers.append(nn.LeakyReLU(self.slope))
        decoder_layers.append(nn.Sigmoid())
        self.decoder = nn.Sequential(*decoder_layers)
