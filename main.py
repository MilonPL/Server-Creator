# Python Server Creator for Pterodactyl
# Lighthouse Servers

# Imports
import requests
import json

# Load configuration from config.json
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

# Get API key and Pterodactyl URL from the configuration
api_key = config.get('api_key')
pterodactyl_url = config.get('pterodactyl_url')

# URLs
url_create_user = f"{pterodactyl_url}/api/application/users"
url_list_users = f"{pterodactyl_url}/api/application/users"
url_list_allocations = f"{pterodactyl_url}/api/application/nodes/{{}}/allocations"
url_create_server = f"{pterodactyl_url}/api/application/servers"

headers = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}",
}


def create_user():
    # Prompt the user for input
    email = input("Enter user email: ").strip()
    username = input("Enter username: ").strip()
    first_name = input("Enter first name: ").strip()
    last_name = input("Enter last name: ").strip()

    # Sanitize the input
    data_create_user = {
        "email": email,
        "username": username,
        "first_name": first_name,
        "last_name": last_name,
    }

    try:
        # Send the POST request to create a user
        response_create_user = requests.post(url_create_user, headers=headers, json=data_create_user)

        # Check if the user creation request was successful (status code 2xx)
        response_create_user.raise_for_status()

        # Get the user ID from the response
        user_id = response_create_user.json()["attributes"]["id"]
        print(f"User created successfully with ID: {user_id}")

        return first_name, user_id

    except requests.exceptions.RequestException as e:
        # Handle any exceptions that occurred during the requests
        print(f"An error occurred: {e}")
        return None, None


def search_user():
    while True:
        # Prompt the user for input to search for an existing user
        search_input = input(
            "Enter email, username, or Discord ID to search for an existing user (type 'exit' to quit): ").strip()

        if search_input.lower() == 'exit':
            print("Exiting search.")
            return None, None

        # Send the request to list all users
        response_list_users = requests.get(url_list_users, headers=headers)
        response_list_users.raise_for_status()

        # Filter users based on the search input
        filtered_users = [user for user in response_list_users.json()["data"]
                          if search_input.lower() in [user["attributes"]["email"].lower(),
                                                      user["attributes"]["username"].lower(),
                                                      user["attributes"]["last_name"].lower()]]

        if not filtered_users:
            print(f"No user found with the provided search input: {search_input}")
        elif len(filtered_users) == 1:
            user_id = filtered_users[0]["attributes"]["id"]
            first_name = filtered_users[0]["attributes"]["first_name"]
            print(f"User found with ID: {user_id}")
            return first_name, user_id
        else:
            print("Multiple users found. Please refine your search.")


def select_node():
    while True:
        # Ask the user to select a node
        node_selection = input("Select the node: Metis (ID 1), Amalthea (ID 2), Adrastea (ID 3), type 'exit' to quit: ").strip().lower()

        if node_selection == 'exit':
            print("Exiting search.")
            return None, None
        elif node_selection == 'metis' or node_selection == '1':
            node_id = 1
            return node_id
        elif node_selection == 'amalthea' or node_selection == '2':
            node_id = 2
            return node_id
        elif node_selection == 'adrastea' or node_selection == '3':
            node_id = 3
            return node_id
        else:
            print("Invalid node selection. Please try again.")


def main():
    # Prompt the user to create a new account or search for an existing one
    create_new_account = input("Create user account? (Y/N): ").strip().lower()

    if create_new_account == "y" or create_new_account == "yes":
        first_name, user_id = create_user()
    elif create_new_account == "n" or create_new_account == "no":
        first_name, user_id = search_user()
    else:
        print("Invalid choice. Please enter 'Y' or 'N'.")
        return

    if user_id:
        # Select a node
        node_id = select_node()

        if node_id is not None:
            # Send the request to get the allocations for the selected node
            response_list_allocations = requests.get(url_list_allocations.format(node_id), headers=headers)
            response_list_allocations.raise_for_status()

            # Filter allocations based on node alias or IP and unassigned status
            node_alias_or_ip = None
            if node_id == 1:
                node_alias_or_ip = "metis.lighthouse-servers.com"
            elif node_id == 2:
                node_alias_or_ip = "104.243.46.28"
            elif node_id == 3:
                node_alias_or_ip = "adrastea.lighthouse-servers.com"

            filtered_allocations = [allocation for allocation in response_list_allocations.json()["data"]
                                    if not allocation["attributes"]["assigned"] and
                                    (allocation["attributes"]["alias"] == node_alias_or_ip or
                                     allocation["attributes"]["ip"] == node_alias_or_ip)]

            # Check if there are at least two unassigned allocations
            if len(filtered_allocations) >= 2:
                print(f"First two unassigned allocations next to each other: "
                      f"{filtered_allocations[0]['attributes']['port']} and {filtered_allocations[1]['attributes']['port']}")

                # Extract the first two unassigned allocations
                allocation_1 = filtered_allocations[0]['attributes']['id']
                allocation_2 = filtered_allocations[1]['attributes']['id']

                # Create a server for the user
                data_create_server = {
                    "name": f"{first_name} | Barotrauma",
                    "user": user_id,
                    "egg": 44,
                    "docker_image": "ghcr.io/milord-thatonemodder/trusted-seas-barotrauma-pterodactyl:main",
                    "startup": "./mod_manager.sh && ./custom_script.sh && export LD_LIBRARY_PATH=\"$LD_LIBRARY_PATH:$PWD/linux64\" && port={{SERVER_PORT}} && ./DedicatedServer -port $port -queryport $(( $port + 1 ))",
                    "environment": {
                        "SRCDS_APPID": "1026340",
                        "AUTO_UPDATE": "1"
                    },
                    "limits": {
                        "memory": 4096,
                        "swap": 0,
                        "disk": 0,
                        "io": 500,
                        "cpu": 0
                    },
                    "feature_limits": {
                        "databases": 0,
                        "backups": 0
                    },
                    "allocation": {
                        "default": allocation_1,
                        "additional": allocation_2
                    }
                }

                response_create_server = requests.post(url_create_server, headers=headers, json=data_create_server)
                response_create_server.raise_for_status()

                print("Server created successfully.")
            else:
                print("Not enough available unassigned allocations for the selected node.")


if __name__ == "__main__":
    main()
