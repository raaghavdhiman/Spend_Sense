# Wipes the Momen "actions" table and loads data/actions.csv. Run once, right before the demo.
import json, requests, pandas as pd
from common import DATA, env

URL, TOKEN = env("GRAPHQL_API_URL"), env("ADMIN_BEARER_TOKEN")
HEAD = {"Content-Type": "application/json", "Authorization": f"Bearer {TOKEN}"}

def gql(query, variables=None):
    r = requests.post(URL, json={"query": query, "variables": variables or {}}, headers=HEAD, timeout=60)
    body = r.json()
    if "errors" in body:
        raise SystemExit(f"GraphQL error: {body['errors']}")
    return body["data"]

df = pd.read_csv(DATA / "actions.csv")
objects = json.loads(df.to_json(orient="records"))      # plain Python types, safe for JSON

print("Deleted:", gql("mutation($where: actions_bool_exp!){ delete_actions(where: $where){ affected_rows } }",
                         {"where": {"id": {"_gt": 0}}}))
print("Inserted:", gql("mutation($objects: [actions_insert_input!]!){ insert_actions(objects: $objects){ affected_rows } }",
                       {"objects": objects}))