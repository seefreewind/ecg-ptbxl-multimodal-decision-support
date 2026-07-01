from __future__ import annotations

import torch
from torch import nn


class GatedFusionMLP(nn.Module):
    def __init__(
        self,
        signal_dim: int,
        structured_dim: int,
        hidden_dim: int = 256,
        classifier_hidden_dim: int = 256,
        num_classes: int = 5,
        dropout: float = 0.3,
    ) -> None:
        super().__init__()
        self.signal_proj = nn.Sequential(
            nn.Linear(int(signal_dim), int(hidden_dim)),
            nn.BatchNorm1d(int(hidden_dim)),
            nn.ReLU(inplace=True),
            nn.Dropout(float(dropout)),
        )
        self.structured_proj = nn.Sequential(
            nn.Linear(int(structured_dim), int(hidden_dim)),
            nn.BatchNorm1d(int(hidden_dim)),
            nn.ReLU(inplace=True),
            nn.Dropout(float(dropout)),
        )
        self.gate = nn.Sequential(
            nn.Linear(int(hidden_dim) * 2, int(hidden_dim)),
            nn.Sigmoid(),
        )
        self.classifier = nn.Sequential(
            nn.Linear(int(hidden_dim), int(classifier_hidden_dim)),
            nn.BatchNorm1d(int(classifier_hidden_dim)),
            nn.ReLU(inplace=True),
            nn.Dropout(float(dropout)),
            nn.Linear(int(classifier_hidden_dim), int(num_classes)),
        )

    def forward(self, signal_x: torch.Tensor, structured_x: torch.Tensor, return_gate: bool = False) -> torch.Tensor | tuple[torch.Tensor, torch.Tensor]:
        signal_h = self.signal_proj(signal_x)
        structured_h = self.structured_proj(structured_x)
        gate = self.gate(torch.cat([signal_h, structured_h], dim=1))
        fused = gate * signal_h + (1.0 - gate) * structured_h
        logits = self.classifier(fused)
        if return_gate:
            return logits, gate
        return logits
