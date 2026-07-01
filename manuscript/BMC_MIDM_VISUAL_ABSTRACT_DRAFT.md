# BMC MIDM Visual Abstract Draft

```mermaid
flowchart LR
  A["Panel 1: Internal multimodal evaluation<br/>PTB-XL waveform + released PTB-XL+ structured features<br/>Fair concat and gated fusion<br/>Internal multimodal complementarity: GO"]
  B["Panel 2: Decision-support diagnostics<br/>Calibration<br/>Uncertainty triage<br/>XAI<br/>Exploratory DCA<br/>Evaluation layers, not clinical readiness"]
  C["Panel 3: External validation boundary<br/>CPSC2018 + Chapman-Shaoxing<br/>Signal-only validation<br/>No external threshold tuning<br/>Signal-level external evidence: GO"]
  D["Panel 4: Reproducibility audit<br/>Structured external reconstruction not validated with adequate coverage/fidelity<br/>Stage 14L audit<br/>External multimodal validation: NO-GO"]
  A --> B --> C --> D
```

Visual abstract text:

> We evaluated a reproducibility-aware ECG decision-support framework. Internal PTB-XL/PTB-XL+ experiments supported multimodal complementarity when ECG signal embeddings were combined with released structured features. Conservative decision-support diagnostics assessed calibration, uncertainty, XAI, and exploratory decision-curve behavior. External evaluation was restricted to signal-only validation on CPSC2018 and Chapman-Shaoxing. A structured-feature reproducibility audit found insufficient external coverage/fidelity for multimodal external validation, which remained NO-GO.
