**1. The diagnosis is substantially supported; the exact attribution is not yet proved.**

At T2 right, the strongest explanation is **boundary contamination from the old edge, followed by a fit that does not follow its own observations**. The signed discrepancies move from 1.4 m outward to 0.5 m inward. That is persuasive evidence of a geometry problem independent of the hood-camera impression. A typical 0.3 m registration mismatch cannot explain that full excursion alone.

The 26-station blend is a credible cause of the entry displacement. Map labels causing the inward drift remain a hypothesis: demonstrate it by masking them and rerunning the detector. The overlays establish disagreement, not its precise cause.

For the left edge, heterogeneous feature detection, retained geometry in holes, and capture transitions are credible contributors. Kind flips and detection jumps show that the measurements are unreliable; they do **not** establish that every discrepancy belongs to the mesh.

Two corrections:

- Gaussian smoothing has no wavelength cutoff. Sigma 5 m retains about 58% of a 30 m sinusoid and 87% of a 60 m sinusoid. Your broad conclusion holds.
- Half-width slope is not directly edge heading: centreline curvature, changing normals, and correspondence affect it. Your angle conversion is approximately valid on a straight.

The centreline statistic and edge-relative statistic measure different quantities, so their magnitudes are not directly comparable. Inspect world-space edge tangents and curvature. Centreline movement can change widths without moving the physical edge. Given the supplied geometry evidence, rendering and z are secondary suspects, though coarse tessellation or depth conflicts could add separate artifacts.

**2. Fit globally, but do not let global smoothness certify accuracy.**

I support a periodic robust spline, but disagree with “painted lines are string-line smooth” as a universal constraint. Real boundaries have repairs, local deviations, kerb transitions, and nonlinear tapers. Straight/clothoid/arc fitting is too restrictive without surveyed alignment evidence.

My starting configuration:

- Fit both world-space boundaries in a common, stable station frame; constrain ordering, plausible widths, and correspondence.
- Use periodic cubic B-splines with **15–25 m knot spacing**, locally refined only at documented features. Penalize rapid curvature variation; tune strength against trusted observations and hood views, initially targeting **30–60 m nuisance undulations**. Knot spacing alone does not set smoothing scale.
- Use uncertainty-weighted **Huber loss**, initially transitioning at **0.2–0.3 m** for trusted paint observations. Shadow and generic non-asphalt detections should not become equivalent boundary observations.
- Define the physical target first. White-line inner edge and kerb outer limit are different boundaries; switching between them can manufacture width changes. Encode their offsets or fit separate features.
- Start with existing registration fixed. Subsequently solve capture translations with priors from registration uncertainty and an absolute anchor. Joint fitting otherwise lets curve displacement and capture offsets trade off, especially with mostly single-capture coverage. Do not introduce rotation or scale without residual evidence.

Use deployed geometry as a weak fallback with uncertainty, not a strong prior: your measurements show it already contains waves.

Your **0.3°/m relative-heading change limit is too permissive as an anti-wave criterion**. A 0.3 m-amplitude, 60 m sinusoid peaks at only about 0.19°/m.

**3. Gate the offending wavelengths and physical displacement.**

Use provisional thresholds, then calibrate against accepted hood views:

- Measure world-space normal displacement against a validated reference curve, separating approximately **15–30, 30–60, and 60–120 m wavelengths**. On gentle sections, fail any rolling 100 m window exceeding **0.10 m RMS or 0.25 m peak** in these bands.
- Gate adjacent edge-heading change at **0.5° per metre**, after accounting for intended curvature. This catches kinks, not broad waves.
- Require trusted-observation residuals: initially **95% within 0.25 m**, with coherent bias above **0.2 m over 10 m** triggering review.
- Flag unsupported intervals and registration uncertainty separately. A smooth hallucination must not pass as verified geometry.

Your sigma-15–25 residual is useful but insufficient alone. Keep the 48-frame sheet, plus slow moving views through failures at the actual camera settings.

**4. Tomorrow’s credible T2 experiment**

Fit one coherent **300–480 interval with 40–60 m context at each end**, replacing all intervening patches. Manually verify a sparse set of paint anchors, mask map graphics, reject ambiguous detections, and freeze registration initially.

Use the same spline objective intended for the full lap. Treat endpoints as constraints with uncertainty, not mandatory attachment to suspect neighbours; evaluate the central interval separately from temporary boundaries.

Deliver before/after world-edge plots, observation residuals, band metrics, and identical hood-camera passes. That tests the replacement method rather than adding another blended repair.
