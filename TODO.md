# TODO

Things deliberately deferred, with the reasoning, so the decision does not have to be
made again from scratch.

## Move Loki's storage to OCI Object Storage

**Now:** `hostPath` at `/var/lib/loki` on whichever node the pod lands on, 30-day
retention. Survives pod restarts; lost when OKE replaces the node.

**Why move:** the nodes are not stable. Both were hours old when this was written, and
the whole node set changed once during a single afternoon. So the 30-day retention is
honest only until the next node replacement.

**Why Object Storage rather than a PVC:** `oci-bv` bills a 50 GB minimum, and only one
more volume fits in the 200 GB Always Free allowance. Spending the last slot on ~1.4 GB
of logs would be waste; that slot belongs to something that genuinely needs a
filesystem. Object Storage is 20 GB free, needs no volume at all, and does not care
which node anything runs on.

**Measured, so the numbers do not need re-deriving:**

| | |
|---|---|
| log volume | ~48 MB/day across 14 namespaces, and falling since `ndots:1` |
| 20 GB free tier holds | ~426 days at that rate |
| Loki writes | ~592 chunks/day = one PUT each |
| plus index shipper and compactor | ~7,200/month |
| **total** | **~25,000 requests/month against a free allowance of ~50,000** |

**Verify before committing:** the 50,000 requests/month figure is from memory, not from
the console. Confirm it, because the margin is roughly 2× and not 20×.

**What it needs:** a bucket, a Customer Secret Key (S3 credentials for the OCI user),
and `storage.type: s3` in `loki.yaml` pointing at the S3-compatible endpoint. The
`loki.yaml` header already anticipated this as "a Phase 2 concern".

## Decide what to do with `hopa`

Three replicas of plain `nginx` in the `default` namespace, created 2026-07-19 with
`kubectl apply`, no Service, no route, no resource requests, and **not in this
repository** — so Flux does not know it exists. It serves the default nginx page to
nobody and costs 3 Mi per pod.

Either delete it or bring it into git. Untracked workloads in a GitOps cluster are how
you end up afraid to reconcile.

## Consider `TRACE_CONTENT` for the agents — but decide the Grafana question first

Full request/response tracing would make the agents' behaviour debuggable: today the
audit log records tool names, hashed arguments and token counts, but nothing anyone
said. That was enough to diagnose a hallucination only because the failing call could be
reproduced live.

**The blocker is not technical.** Grafana is anonymously readable on purpose, for demos,
and its Loki datasource answers unauthenticated queries — verified from outside the
cluster. Turning on content tracing would therefore publish conversations with the agent
and the contents of every file it reads. Decide the access question before the logging
one, not after.
