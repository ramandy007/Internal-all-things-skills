---
name: ibm-cloud-security
description: >-
  IBM Cloud reference notes for managed databases (PostgreSQL, MongoDB) and object storage (COS):
  supported engines, storage classes, endpoints, access patterns and service characteristics, for
  when IBM Cloud appears in engagement scope or in leaked configuration. Use when you hold an IBM
  Cloud API key, a COS service-instance ID or a *.cloud-object-storage.appdomain.cloud endpoint
  and need to know what the service is, how it is reached and what data it holds, or when
  reviewing IBM Cloud storage and database exposure. Documents the platform only - there is no IBM
  Cloud attack toolchain here; for S3-style bucket mechanics use aws-security.
license: Upstream terms apply - see NOTICE.md
metadata:
  source: https://github.com/swisskyrepo/InternalAllTheThings
  source-commit: "203bb0c"
  reference-files: "2"
  generated-by: build/build.py
---

# IBM Cloud Security

IBM Cloud exposes two surfaces this skill covers: managed databases (PostgreSQL, MongoDB) reached by a connection string, and Cloud Object Storage (COS), an S3-compatible API authenticated with an IBM IAM API key and a service-instance ID. Both are ordinary data services once you hold a credential - the work is identifying which service instance the credential belongs to, proving read/write reach, and classifying what the data is worth. Done means: service identified, credential validated against it, and the accessible data enumerated.

## When to use this skill

- IBM Cloud is in scope and you hold an IBM IAM API key, a COS service-instance ID, or a database connection string.
- You found an endpoint matching `*.cloud-object-storage.appdomain.cloud` or a `psycopg2`/`mongodb://` connection string in code, config or a leak.
- You are reviewing whether IBM Cloud object storage buckets or managed databases are reachable with the credentials at hand.
- Boundary: these two references carry connectivity and service characteristics, not an offensive toolchain. There is no enumeration scanner, IAM-policy walker or privilege-escalation path in them - do not go looking for one here. For AWS S3 mechanics (bucket discovery, `--no-sign-request`, version listing) see `aws-security`; for the containers that consume these services see `container-security`.

## First moves

1. Install the COS SDK. The IBM client is a `ibm_boto3` build of boto3, so the call shape is S3-like but the auth is IBM IAM:

```bash
pip install ibm-cos-sdk
```

2. Build the client with an IBM IAM API key and the service-instance ID. Both are required - the key identifies the account, the instance ID scopes which COS resource you may touch:

```python
import ibm_boto3
from ibm_botocore.client import Config

cos = ibm_boto3.client('s3',
                       ibm_api_key_id='your_api_key',
                       ibm_service_instance_id='your_service_instance_id',
                       config=Config(signature_version='oauth'),
                       endpoint_url='https://s3.us.cloud-object-storage.appdomain.cloud')
```

3. Prove reach in both directions - an upload succeeding is write access, a download is the exfiltration path:

```python
cos.upload_file(Filename='example.txt', Bucket='your_bucket_name', Key='example.txt')
cos.download_file(Bucket='your_bucket_name', Key='example.txt', Filename='downloaded_example.txt')
```

4. PostgreSQL managed instances take a standard `psycopg2` connection; everything you need is in the service credentials:

```python
import psycopg2
conn = psycopg2.connect(dbname="your_database_name", user="your_username",
                        password="your_password", host="your_host", port="your_port")
cursor = conn.cursor()
cursor.execute("SELECT * FROM your_table;")
print(cursor.fetchall())
```

5. MongoDB managed instances take a URI of the form `mongodb://<user>:<pass>@<host>:<port>/<db>`; connect, list collections, then sample documents:

```javascript
const { MongoClient } = require('mongodb');
const uri = "mongodb://your_username:your_password@your_host:your_port/your_database";
const client = new MongoClient(uri);
await client.connect();
const db = client.db('your_database');
const user = await db.collection('your_collection').findOne({ name: "John Doe" });
```

## Reference map

| Reference | Read it when | Key content |
|---|---|---|
| [ibm-cloud-object-storage.md](references/ibm-cloud-object-storage.md) | a COS endpoint or IAM API key is in hand | SDK install, `ibm_boto3` client configuration, upload/download, storage classes (Standard/Vault/Cold Vault/Smart Tier), IAM access policies, regional endpoints |
| [ibm-cloud-databases.md](references/ibm-cloud-databases.md) | a managed Postgres or Mongo connection string is in hand | supported engines, `psycopg2` and `MongoClient` connection examples, automated backup/HA/encryption characteristics |

## Workflow

1. **Classify the credential before connecting.** An IBM IAM API key plus a service-instance ID → COS (`ibm-cloud-object-storage.md`). A `postgres://`/`psycopg2`-style tuple or a `mongodb://` URI → managed database (`ibm-cloud-databases.md`). A key with no instance ID is not enough for COS.
2. **COS path:** configure the client against the correct regional endpoint, then upload and download a test object. An auth failure here is almost always the key/instance pairing or the endpoint region, not a permission problem.
3. **Database path:** connect with the supplied credentials and query. If the connection is refused, confirm the host/port pair from the service credentials before assuming the credential is dead.
4. **Classify the data.** For COS, note each object's storage class - lifecycle policies move data between Standard, Vault, Cold Vault and Smart Tier automatically. For databases, enumerate schemas and sample rows rather than dumping whole tables.
5. **Record scope.** Both services are managed and encrypted at rest with automated backups; the finding is "data reachable with this credential", not host compromise.

## Gotchas

- The COS client here authenticates with `signature_version='oauth'` and `ibm_api_key_id`, not AWS SigV4 - an `aws s3` command with AWS keys does not authenticate against COS.
- `ibm_service_instance_id` is mandatory next to the API key. A key that works for one COS instance silently fails for another - this is scoping, not a broken key.
- `endpoint_url` is regional. Using `s3.us.cloud-object-storage.appdomain.cloud` for an instance in another region produces auth or not-found errors that look like permission denials.
- Storage classes (Standard, Vault, Cold Vault, Smart Tier) change cost and retrieval characteristics, and data lifecycle policies move objects between them automatically - record the class next to the key when you report exposure.
- Managed database instances are fully managed: encryption at rest, automated backups, HA/failover. There is no host filesystem to reach - the access path is the connection string only.
- The references contain no IBM Cloud CLI, IAM-policy enumeration or access-key discovery commands. Do not extrapolate an offensive workflow from the SDK examples; report the gap instead of inventing steps.

## Authorized use

These techniques are for authorized engagements only, with explicit permission and within the agreed scope. Reading customer data from a managed database or bucket needs the same authorization as any other data-access test.

## Source

Converted from the upstream InternalAllTheThings IBM Cloud guides (https://github.com/swisskyrepo/InternalAllTheThings), see NOTICE.md.
