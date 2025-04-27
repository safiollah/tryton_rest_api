#!/usr/bin/env python
import os
import sys
from pprint import pprint
import requests
import json

# Activate the virtual environment
import naiad

# Configuration
TRYTON_URL = "http://localhost:8090"  # Change this to your Tryton server URL
DATABASE = "trytonDB"  # Change this to your database name
API_KEY = "64d2b609dcb84d3d9f0f766fa9b8734e9fde53642d5d46bdad0fb78aa2cbc1398e5f598454664144b5047f2b332ce3f10f4073005abb4fa3b5f227db5bd5452e"  # Get this from Tryton user application

def test_naiad_rest_api():
    """Test the naiad REST API functionality"""
    print("Testing naiad REST API for Tryton...")

    # Create a client
    client = naiad.Client(
        base_url=f"{TRYTON_URL}/{DATABASE}",
        key=API_KEY,
        usages=["default"],
        context={"company": 1},  # Set your company ID
        languages=["en"]
    )

    # Track created resources for cleanup
    created_resources = {}

    # Test 1: Search for parties
    print("\n1. Searching for parties...")
    parties = []
    try:
        parties = client.search("party.party", domain=[["active", "=", True]], limit=5)
        print(f"Found {len(parties)} parties:")
        for party in parties:
            print(f"  - {party.id}: {party.rec_name if 'rec_name' in party else 'N/A'}")
    except Exception as e:
        print(f"Error searching parties: {e}")

    # Test 2: Get a single party
    print("\n2. Getting a single party...")
    try:
        if parties:
            party_id = parties[0].id
            party = client.get("party.party", party_id)
            print(f"Retrieved party {party.id}: {party.rec_name if 'rec_name' in party else 'N/A'}")
            print("Party details:")
            pprint(party.to_dict())

            print("\nComplete field list for party:")
            for field_name in dir(party):
                if not field_name.startswith('_'):
                    try:
                        value = getattr(party, field_name)
                        if not callable(value):
                            print(f"  - {field_name}: {value}")
                    except Exception as e:
                        print(f"  - {field_name}: <error accessing>")
        else:
            print("Skipping get test as no parties were found")
    except Exception as e:
        print(f"Error getting party: {e}")

    # Test 3: Create a new party using REST
    print("\n3. Creating a new party using REST...")
    created_party = None
    try:
        rest_url = f"{TRYTON_URL}/{DATABASE}/rest/model/party.party"
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        rest_payload = {
            "name": "Test Party via REST",
            "active": True
        }
        response = requests.post(rest_url, headers=headers, json=rest_payload)
        if response.status_code == 200:
            result = response.json()
            print(f"REST API response: {json.dumps(result, indent=2)}")
            if isinstance(result, dict) and result.get("id"):
                party_id = result["id"]
                created_party = client.get("party.party", party_id)
                print(f"Retrieved created party: {created_party.rec_name}")
                created_resources['party'] = created_party
            else:
                print(f"Unexpected REST API result: {result}")
        else:
            print(f"REST API create failed: {response.status_code} {response.text}")
    except Exception as e:
        print(f"Error creating party: {e}")

    # Test 4: Update a party
    print("\n4. Updating a party...")
    try:
        if created_party:
            party_to_update = created_party
        elif parties:
            print("Using existing party for update test since creation failed")
            party_to_update = client.get("party.party", parties[0].id)
            update_party = naiad.Record(__name__="party.party")
            update_party.id = party_to_update.id
            update_party.name = f"{party_to_update.rec_name} (Updated)"
            party_to_update = update_party
        else:
            print("Skipping update test as no parties are available")
            raise ValueError("No party available to update")

        print("Update payload:")
        pprint(party_to_update.to_dict())

        updated_party = client.store(party_to_update)
        print(f"Updated party {updated_party.id}, new name: {updated_party.rec_name if hasattr(updated_party, 'rec_name') else updated_party.name}")
    except Exception as e:
        print(f"Error updating party: {e}")
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            print(f"Error response: {e.response.text}")

    # Test 5: Search with pagination using ranges
    print("\n5. Testing pagination with ranges...")
    try:
        range_info, parties = client.search("party.party", range_=(0, 9))
        start, end, total = range_info
        print(f"Retrieved records {start}-{end} of {total} total parties")
        print(f"Got {len(parties)} parties in this page")
    except Exception as e:
        print(f"Error with pagination: {e}")

    # Test 6: Delete a party
    print("\n6. Deleting a party...")
    try:
        if 'party' in created_resources:
            client.delete(created_resources['party'])
            print(f"Deleted party with ID: {created_resources['party'].id}")
        else:
            print("Skipping delete test as no test party was created")
    except Exception as e:
        print(f"Error deleting party: {e}")

    print("\nTests completed.")

if __name__ == "__main__":
    test_naiad_rest_api()
