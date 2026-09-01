"""One-shot: restore the immutable Deployment selector. Deleted after it runs."""

from pathlib import Path

p = Path("applications/agents/agent-lead.yaml")
t = p.read_text(encoding="utf-8")

PAIRS = [
    # Deployment metadata
    (
        """  name: agent-lead
  namespace: agents
  labels:
    app.kubernetes.io/name: agent-lead
    app.kubernetes.io/component: agent
spec:
  replicas: 1""",
        """  name: agent-lead
  namespace: agents
  labels:
    app: agent-lead
spec:
  replicas: 1""",
    ),
    # The selector itself — this is the field that cannot change on a live Deployment.
    (
        """  selector:
    matchLabels:
      app.kubernetes.io/name: agent-lead
  template:
    metadata:
      labels:
        app.kubernetes.io/name: agent-lead
        app.kubernetes.io/component: agent""",
        """  # spec.selector is IMMUTABLE. Changing it on an existing Deployment makes every
  # apply fail with "field is immutable", and because Flux applies ./applications as
  # one Kustomization, that failure freezes every other app in the tree too. Switching
  # to app.kubernetes.io/name did exactly that. Changing these labels now requires
  # deleting the Deployment first — do it deliberately, not as a tidy-up.
  selector:
    matchLabels:
      app: agent-lead
  template:
    metadata:
      labels:
        app: agent-lead""",
    ),
    # Service must select the same labels the pods actually carry.
    (
        """  name: agent-lead
  namespace: agents
  labels:
    app.kubernetes.io/name: agent-lead
spec:
  selector:
    app.kubernetes.io/name: agent-lead""",
        """  name: agent-lead
  namespace: agents
  labels:
    app: agent-lead
spec:
  selector:
    app: agent-lead""",
    ),
]

for old, new in PAIRS:
    assert old in t, old[:70]
    t = t.replace(old, new, 1)

assert "app.kubernetes.io" not in t, "a kubernetes.io label survived the rewrite"
p.write_text(t, encoding="utf-8")
print("labels restored")
