# Primary-source novelty check — 2026-11-27

Search window: 2025-11-27 through 2026-11-27. Codex checked primary publisher
and arXiv pages; no external-model novelty certification or full systematic
review. Claims below describe abstracts, not reproduced implementations.

- **PADRE**, IJCAI 2026 main track, pp. 4518–4526, DOI 10.24963/ijcai.2026/503:
  combines delayed residuals, current context and retrieved drift patterns to
  gate adaptation. Our inference: residual-driven memory gating as a general
  recipe is already occupied. Forecasting gradient gates are not directly
  interchangeable with a trading RL value-memory mechanism.
  https://ijcai.org/proceedings/2026/503
- **Adaptive Conformal Inference Under Delayed Feedback**, arXiv:2609.07251v1,
  submitted 2026-09-07: relates delayed coverage adaptation to residual memory
  time scales, with dependence on the residual process. Our inference: delay
  relative to evidence lifetime must be tested, but borrowing this diagnostic
  does not confer interval or profit guarantees on our gate.
  https://arxiv.org/abs/2609.07251
- **A Temporal Algebraic Framework for Data Stream Evaluation Under Delayed
  Labels and Distribution Shifts**, arXiv:2611.21914v1, submitted 2026-11-16:
  distinguishes prevalence shifts and classifier changes under delayed/selected
  labels. Our inference: observed residual changes need not identify a change
  in decision quality; exposure and selection effects require separate audits.
  https://arxiv.org/abs/2611.21914

Decision: implement only a transparent conditional/global expert-weighting
control and causal ledger first. Do not promote its toy diagnostic as a new
CCF A method. Retain old failed routes and seek an RL-specific mechanism with
an advantage that survives an equivalent contextual weighting baseline.
