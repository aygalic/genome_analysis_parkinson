import torch

import torch.nn as nn

from .autoencoder import Autoencoder

class CNNAutoencoder(Autoencoder):

    def __init__(
            self,
            shape,
            latent_dim=64,
            dropout = 0.1,
            slope = 0.05,
            num_layers = 3,
            variational = None,
            kernel_size = None,
            padding = None,
            num_embeddings = 512,
            embedding_dim = 512,
            commitment_cost = 1):
        
        super().__init__(
            shape = shape,
            latent_dim=latent_dim,
            dropout = dropout,
            slope = slope,
            num_layers = num_layers,
            variational = variational,
            num_embeddings = num_embeddings,
            embedding_dim = embedding_dim,
            commitment_cost = commitment_cost)
        

        if kernel_size is None:
            self.kernel_size = 7
        if padding is None:
            self.padding = 3

        self.in_channels = 1  # Starting with one input channel
        self.out_channels : int
        self.calculated_length : int 


    def build_encoder(self):
        # Encoder
        encoder_layers = []

        for i in range(self.num_layers):
            out_channels = 32 * (2 ** i)
            encoder_layers.extend([
                nn.Conv1d(self.in_channels, out_channels, kernel_size=self.kernel_size, stride=2, padding=self.padding),
                nn.LeakyReLU(self.slope),
                nn.Dropout(self.dropout),
                nn.MaxPool1d(2)
            ])

            self.in_channels = out_channels

        encoder_layers.extend([
            nn.Flatten(),
            nn.LazyLinear(self.latent_dim),
            nn.LeakyReLU(self.slope)
        ])

        self.encoder = nn.Sequential(*encoder_layers)

    def build_decoder(self):

        self.calculated_length = self._find_calculated_length()

        # Decoder
        decoder_layers = []
        in_features = self.latent_dim

        decoder_layers.extend([
            nn.Linear(in_features, self.in_channels * self.calculated_length),
            nn.Unflatten(1, (self.in_channels, self.calculated_length))
        ])

        #in_channels = 128
        for i in reversed(range(self.num_layers)):
            out_channels = 32 * (2 ** i)
            decoder_layers.extend([
                nn.Upsample(scale_factor=2),
                nn.ConvTranspose1d(self.in_channels, out_channels, kernel_size=self.kernel_size, stride=2, padding=self.padding),
                nn.LeakyReLU(self.slope),
                nn.Dropout(self.dropout)
            ])
            in_channels = out_channels

        # Last layer of decoder to reconstruct the input
        decoder_layers.extend([
            nn.Upsample(scale_factor=2),
            nn.ConvTranspose1d(in_channels, 1, kernel_size=self.kernel_size, stride=2, padding=self.padding),
            nn.LazyLinear(self.input_shape),
            nn.Sigmoid()
        ])

        self.decoder = nn.Sequential(*decoder_layers)
        
    def _find_calculated_length(self):
        mock_input = torch.rand(1, 1, self.input_shape)  
        with torch.no_grad():
            self.eval()
            for layer in self.encoder:
                if isinstance(layer, nn.Flatten):
                    break 
                mock_input = layer(mock_input)
        calculated_length = mock_input.size()
        return calculated_length[2]