import requests
import json
import yaml
import time

API_KEY = "rnd_vUtUq94WOOrX2UNYEiLZvvgrwcdF"
OWNER_ID = "tea-d7241gnfte5s73ep30n0"
BASE_URL = "https://api.render.com/v1"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

with open("render.yaml") as f:
    blueprint = yaml.safe_load(f)

created_ids = {}

def create_service(name, payload):
    print(f"  Creating {name}...")
    resp = requests.post(f"{BASE_URL}/services", headers=HEADERS, json=payload)
    if resp.status_code in (200, 201):
        data = resp.json()
        sid = data.get("id", "unknown")
        created_ids[name] = sid
        print(f"  ✓ {name}: {sid}")
        return sid
    else:
        print(f"  ✗ {name} ({resp.status_code}): {resp.text[:200]}")
        return None

def create_redis(name, payload):
    print(f"  Creating {name}...")
    resp = requests.post(f"{BASE_URL}/redis", headers=HEADERS, json=payload)
    if resp.status_code in (200, 201):
        data = resp.json()
        sid = data.get("id", data.get("redis", {}).get("id", "unknown"))
        created_ids[name] = sid
        print(f"  ✓ {name}: {sid}")
        return sid
    else:
        print(f"  ✗ {name} ({resp.status_code}): {resp.text[:200]}")
        return None

# Phase 1: Create infrastructure services (no cross-references)
print("=== Phase 1: Infrastructure ===")
for svc in blueprint["services"]:
    name = svc["name"]
    stype = svc["type"]

    if stype == "redis":
        create_redis(name, {
            "name": name,
            "ownerId": OWNER_ID,
            "region": "singapore",
            "plan": "starter",
            "maxmemoryPolicy": "noeviction",
            "ipAllowList": []
        })
    elif stype == "pserv":
        env_vars = []
        for ev in svc.get("envVars", []):
            if "sync" in ev:
                env_vars.append({"key": ev["key"], "sync": ev["sync"]})
            elif "value" in ev:
                env_vars.append({"key": ev["key"], "value": ev["value"]})
        payload = {
            "name": name,
            "ownerID": OWNER_ID,
            "type": "pserv",
            "env": "docker",
            "region": "singapore",
            "plan": "starter",
            "dockerfilePath": svc.get("dockerfilePath", ""),
            "dockerContext": svc.get("dockerContext", "./"),
            "envVars": env_vars
        }
        if "disk" in svc:
            payload["disk"] = svc["disk"]
        create_service(name, payload)
    time.sleep(2)

# Phase 2: Create application services (with cross-references)
print("\n=== Phase 2: Application Services ===")
for svc in blueprint["services"]:
    name = svc["name"]
    stype = svc["type"]

    if stype not in ("web", "worker"):
        continue

    env_vars = []
    for ev in svc.get("envVars", []):
        if "sync" in ev:
            env_vars.append({"key": ev["key"], "sync": ev["sync"]})
        elif "value" in ev:
            env_vars.append({"key": ev["key"], "value": ev["value"]})
        elif "generateValue" in ev:
            env_vars.append({"key": ev["key"], "generateValue": ev["generateValue"]})
        elif "fromService" in ev:
            ref = ev["fromService"]
            ref_name = ref.get("name", "")
            ref_id = created_ids.get(ref_name, "")
            if ref_id:
                env_vars.append({
                    "key": ev["key"],
                    "fromService": {
                        "type": ref.get("type", ""),
                        "id": ref_id,
                        "property": ref.get("property", ""),
                        "envVarKey": ref.get("envVarKey", "")
                    }
                })
            else:
                # Skip cross-references for now - will set manually
                env_vars.append({"key": ev["key"], "value": ""})

    payload = {
        "name": name,
        "ownerID": OWNER_ID,
        "type": stype,
        "env": "docker",
        "region": "singapore",
        "plan": "standard",
        "dockerfilePath": svc.get("dockerfilePath", ""),
        "dockerContext": svc.get("dockerContext", "./"),
        "envVars": env_vars
    }
    if "healthCheckPath" in svc:
        payload["healthCheckPath"] = svc["healthCheckPath"]

    create_service(name, payload)
    time.sleep(2)

print(f"\n=== Summary: {len(created_ids)} services created ===")
for name, sid in created_ids.items():
    print(f"  {name}: {sid}")