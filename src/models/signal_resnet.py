from __future__ import annotations

from collections.abc import Sequence

import torch
from torch import nn


class ResidualBlock1D(nn.Module):
    def __init__(self, channels: int, kernel_size: int = 7, dropout: float = 0.1) -> None:
        super().__init__()
        padding = kernel_size // 2
        self.block = nn.Sequential(
            nn.Conv1d(channels, channels, kernel_size=kernel_size, padding=padding, bias=False),
            nn.BatchNorm1d(channels),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout),
            nn.Conv1d(channels, channels, kernel_size=kernel_size, padding=padding, bias=False),
            nn.BatchNorm1d(channels),
        )
        self.activation = nn.ReLU(inplace=True)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.activation(x + self.block(x))


class SignalResNet(nn.Module):
    """Small 1D ResNet for PTB-XL multi-label signal baseline."""

    def __init__(
        self,
        in_channels: int = 12,
        num_classes: int = 5,
        base_channels: int = 32,
        blocks_per_stage: Sequence[int] = (2, 2, 2),
        dropout: float = 0.1,
    ) -> None:
        super().__init__()
        layers: list[nn.Module] = [
            nn.Conv1d(in_channels, base_channels, kernel_size=15, stride=2, padding=7, bias=False),
            nn.BatchNorm1d(base_channels),
            nn.ReLU(inplace=True),
        ]
        channels = base_channels
        for stage_idx, n_blocks in enumerate(blocks_per_stage):
            if stage_idx > 0:
                next_channels = channels * 2
                layers.extend(
                    [
                        nn.Conv1d(channels, next_channels, kernel_size=5, stride=2, padding=2, bias=False),
                        nn.BatchNorm1d(next_channels),
                        nn.ReLU(inplace=True),
                    ]
                )
                channels = next_channels
            for _ in range(int(n_blocks)):
                layers.append(ResidualBlock1D(channels, dropout=dropout))
        self.encoder = nn.Sequential(*layers)
        self.pool = nn.AdaptiveAvgPool1d(1)
        self.flatten = nn.Flatten()
        self.dropout = nn.Dropout(dropout)
        self.classifier = nn.Linear(channels, num_classes)
        self.embedding_dim = channels

    def forward(self, x: torch.Tensor, return_embedding: bool = False) -> torch.Tensor | tuple[torch.Tensor, torch.Tensor]:
        encoded = self.encoder(x)
        embedding = self.flatten(self.pool(encoded))
        logits = self.classifier(self.dropout(embedding))
        if return_embedding:
            return logits, embedding
        return logits
