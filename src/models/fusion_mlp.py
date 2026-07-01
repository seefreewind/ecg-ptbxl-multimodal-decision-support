from __future__ import annotations

from collections.abc import Sequence

import torch
from torch import nn


class FusionMLP(nn.Module):
    def __init__(self, input_dim: int, hidden_dims: Sequence[int] = (512, 256), num_classes: int = 5, dropout: float = 0.3) -> None:
        super().__init__()
        layers: list[nn.Module] = []
        current = int(input_dim)
        for hidden in hidden_dims:
            layers.extend(
                [
                    nn.Linear(current, int(hidden)),
                    nn.BatchNorm1d(int(hidden)),
                    nn.ReLU(inplace=True),
                    nn.Dropout(float(dropout)),
                ]
            )
            current = int(hidden)
        layers.append(nn.Linear(current, int(num_classes)))
        self.net = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)
