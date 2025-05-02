#!env python3
"""
Uses the Auth0 Management API to model an Auth0 Identity Provider in Veza.

To run the code, you will need to export environment variables for:
- Veza URL and API key
- Auth0 domain, client ID, and client secret

Example:
    ```
    export VEZA_API_KEY="xxxxxxx"
    export VEZA_URL="https://myveza.vezacloud.com"
    export AUTH0_DOMAIN="your-tenant.auth0.com"
    export AUTH0_CLIENT_ID="your-client-id"
    export AUTH0_CLIENT_SECRET="your-client-secret"
    ./auth0_provider.py
    ```

Improvement Ideas:
1. Permission Granularity
   - Add support for more detailed permission types (read, write, delete, admin)
   - Map Auth0 permission patterns to standardized Veza permissions
   - Add permission categories for better organization

2. API Enhancements
   - Add support for API endpoints and methods
   - Track API usage statistics
   - Model API relationships and dependencies
   - Add API versioning information

3. Role-Based Access
   - Implement hierarchical role modeling
   - Add role inheritance tracking
   - Support for role templates
   - Role-based permission analysis

4. User Context
   - Add user login history
   - Track user device information
   - Model user location data
   - Add user risk scoring

5. Organization Structure
   - Model organizational hierarchy
   - Track department relationships
   - Add business unit mapping
   - Support for multiple domains

6. Security Features
   - Add MFA status tracking
   - Model security policies
   - Track security events
   - Add risk assessment data

7. Integration Enhancements
   - Support for custom rules
   - Add hook integration tracking
   - Model external service connections
   - Add integration status monitoring

8. Performance Optimizations
   - Implement caching for frequently accessed data
   - Add batch processing for large datasets
   - Optimize API calls
   - Add progress tracking for long operations

9. Reporting
   - Add permission usage analytics
   - Generate access pattern reports
   - Track permission changes over time
   - Create security compliance reports

10. Error Handling
    - Improve error recovery
    - Add detailed error logging
    - Implement retry strategies
    - Add error notification system

Copyright 2024 Veza Technologies Inc.

Use of this source code is governed by the MIT
license that can be found in the LICENSE file or at
https://opensource.org/licenses/MIT.
"""

from oaaclient.client import OAAClient, OAAClientError
from oaaclient.templates import CustomIdPProvider, OAAPropertyType, CustomApplication, OAAPermission, OAATemplateException
from auth0.authentication import GetToken
from auth0.management import Auth0
from auth0.exceptions import Auth0Error
import os
import sys
import json
import asyncio
from dotenv import load_dotenv
from typing import Dict, List, Any
import requests
import time
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def get_auth0_client():
    """Initialize and return an Auth0 management API client."""
    domain = os.getenv("AUTH0_DOMAIN")
    client_id = os.getenv("AUTH0_CLIENT_ID")
    client_secret = os.getenv("AUTH0_CLIENT_SECRET")

    if not all([domain, client_id, client_secret]):
        print("Missing required Auth0 environment variables")
        sys.exit(1)

    # Get access token using client credentials
    get_token = GetToken(domain, client_id, client_secret=client_secret)
    token = get_token.client_credentials(f"https://{domain}/api/v2/")
    mgmt_api_token = token['access_token']

    # Initialize management client
    return Auth0(domain, mgmt_api_token)

def fetch_paginated_data(auth0_client, endpoint: str, **kwargs) -> List[Dict[str, Any]]:
    """Generic function to fetch paginated data from Auth0."""
    try:
        items = []
        page = 0
        per_page = 50  # Reduced from 100 to avoid rate limits
        
        while True:
            kwargs.update({"page": page, "per_page": per_page})
            
            # Get the appropriate client method based on the endpoint
            if endpoint == "resource_servers":
                response = auth0_client.resource_servers.get_all(**kwargs)
            elif endpoint == "users":
                response = auth0_client.users.list(**kwargs)
            elif endpoint == "roles":
                response = auth0_client.roles.list(**kwargs)
            elif endpoint == "clients":
                response = auth0_client.clients.all(**kwargs)
            elif endpoint == "organizations":
                response = auth0_client.organizations.all_organizations(**kwargs)
            elif endpoint == "connections":
                response = auth0_client.connections.all(**kwargs)
            else:
                raise ValueError(f"Unknown endpoint: {endpoint}")
            
            if isinstance(response, dict):
                if "users" in response:
                    items.extend(response["users"])
                elif "resource_servers" in response:
                    items.extend(response["resource_servers"])
                elif "organizations" in response:
                    items.extend(response["organizations"])
                elif "roles" in response:
                    items.extend(response["roles"])
                else:
                    items.extend(response)
            else:
                items.extend(response)
            
            if isinstance(response, dict):
                if "users" in response:
                    total = len(response["users"])
                elif "resource_servers" in response:
                    total = len(response["resource_servers"])
                elif "organizations" in response:
                    total = len(response["organizations"])
                elif "roles" in response:
                    total = len(response["roles"])
                else:
                    total = len(response)
            else:
                total = len(response)
                
            if total < per_page:
                break
                
            page += 1
            
            # Add a small delay between requests to avoid rate limits
            time.sleep(0.5)
            
        return items
    except Auth0Error as e:
        if e.status_code == 429:  # Rate limit error
            print(f"Rate limit reached while fetching {endpoint}. Waiting 30 seconds...")
            time.sleep(30)  # Wait 30 seconds before retrying
            return fetch_paginated_data(auth0_client, endpoint, **kwargs)
        print(f"Error fetching {endpoint} from Auth0: {e}")
        sys.exit(1)

def fetch_auth0_users(auth0_client):
    """Fetch all users from Auth0."""
    return fetch_paginated_data(auth0_client, "users")

def fetch_auth0_roles(auth0_client):
    """Fetch all roles from Auth0."""
    return fetch_paginated_data(auth0_client, "roles")

def fetch_auth0_clients(auth0_client):
    """Fetch all applications (clients) from Auth0."""
    return fetch_paginated_data(auth0_client, "clients")

def fetch_auth0_resource_servers(auth0_client):
    """Fetch all resource servers (APIs) from Auth0."""
    return fetch_paginated_data(auth0_client, "resource_servers")

def fetch_auth0_organizations(auth0_client):
    """Fetch all organizations from Auth0."""
    return fetch_paginated_data(auth0_client, "organizations")

def fetch_auth0_connections(auth0_client):
    """Fetch all connections from Auth0."""
    return fetch_paginated_data(auth0_client, "connections")

def fetch_user_permissions(auth0_client, user_id: str) -> List[Dict[str, Any]]:
    """Fetch permissions for a specific user."""
    try:
        response = auth0_client.users.list_permissions(user_id)
        return response.get("permissions", [])
    except Auth0Error as e:
        if e.status_code == 429:  # Rate limit error
            print(f"Rate limit reached while fetching permissions for user {user_id}. Waiting 30 seconds...")
            time.sleep(30)  # Wait 30 seconds before retrying
            return fetch_user_permissions(auth0_client, user_id)
        print(f"Error fetching permissions for user {user_id}: {e}")
        return []

def fetch_role_permissions(auth0_client, role_id: str) -> List[Dict[str, Any]]:
    """Fetch permissions for a specific role."""
    try:
        response = auth0_client.roles.list_permissions(role_id)
        return response.get("permissions", [])
    except Auth0Error as e:
        if e.status_code == 429:  # Rate limit error
            print(f"Rate limit reached while fetching permissions for role {role_id}. Waiting 30 seconds...")
            time.sleep(30)  # Wait 30 seconds before retrying
            return fetch_role_permissions(auth0_client, role_id)
        print(f"Error fetching permissions for role {role_id}: {e}")
        return []

def retry_with_backoff(func, max_retries=3, initial_delay=1):
    """Decorator to retry a function with exponential backoff."""
    def wrapper(*args, **kwargs):
        delay = initial_delay
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)}. Retrying in {delay} seconds...")
                time.sleep(delay)
                delay *= 2
    return wrapper

def main():
    try:
        # Load environment variables
        load_dotenv()
        logger.info("Environment variables loaded")

        # Initialize Auth0 client
        auth0_client = get_auth0_client()
        logger.info("Auth0 client initialized")

        # Initialize Veza client
        veza_api_key = os.getenv("VEZA_API_KEY")
        veza_url = os.getenv("VEZA_URL")
        if not veza_api_key or not veza_url:
            logger.error("Missing required Veza environment variables")
            sys.exit(1)

        logger.info("Initializing Veza client")
        veza_con = OAAClient(url=veza_url, api_key=veza_api_key)

        # Create Auth0 provider in Veza with proper naming
        provider_name = "Auth0"
        logger.info("Creating Auth0 provider in Veza")
        idp = CustomIdPProvider("Auth0", idp_type="auth0", domain=os.getenv("AUTH0_DOMAIN"))

        # Define custom properties for Auth0-specific attributes
        idp.property_definitions.define_user_property("last_login", OAAPropertyType.STRING)
        idp.property_definitions.define_user_property("logins_count", OAAPropertyType.NUMBER)
        idp.property_definitions.define_user_property("blocked", OAAPropertyType.BOOLEAN)
        idp.property_definitions.define_user_property("email_verified", OAAPropertyType.BOOLEAN)
        idp.property_definitions.define_user_property("connection", OAAPropertyType.STRING)
        idp.property_definitions.define_user_property("organization", OAAPropertyType.STRING)

        # Define app properties
        idp.property_definitions.define_app_property("description", OAAPropertyType.STRING)
        idp.property_definitions.define_app_property("type", OAAPropertyType.STRING)

        # Fetch and process Auth0 resource servers (APIs)
        logger.info("Fetching Auth0 resource servers")
        resource_servers = fetch_auth0_resource_servers(auth0_client)
        logger.info(f"Found {len(resource_servers)} resource servers")
        for api in resource_servers:
            app_id = api.get("identifier", "")
            app_name = api.get("name")
            veza_app = idp.add_app(app_id, app_name)
            veza_app.description = api.get("description", "")
            veza_app.set_property("type", "api")

        # Fetch and process Auth0 clients (applications)
        logger.info("Fetching Auth0 clients")
        clients = fetch_auth0_clients(auth0_client)
        logger.info(f"Found {len(clients)} clients")
        for client in clients:
            app_id = client.get("client_id", "")
            app_name = client.get("name")
            veza_app = idp.add_app(app_id, app_name)
            veza_app.description = client.get("description", "")
            veza_app.set_property("type", "client")

        # Fetch and process Auth0 organizations
        logger.info("Fetching Auth0 organizations")
        organizations = fetch_auth0_organizations(auth0_client)
        logger.info(f"Found {len(organizations)} organizations")
        for org in organizations:
            idp.add_group(org.get("name"), full_name=org.get("display_name", ""))

        # Fetch and process Auth0 connections
        logger.info("Fetching Auth0 connections")
        connections = fetch_auth0_connections(auth0_client)
        logger.info(f"Found {len(connections)} connections")
        for conn in connections:
            idp.add_group(conn.get("name"), full_name=conn.get("display_name", ""))

        # Fetch and process Auth0 users
        logger.info("Fetching Auth0 users")
        auth0_users = fetch_auth0_users(auth0_client)
        logger.info(f"Found {len(auth0_users)} users")
        for user in auth0_users:
            # Create user in Veza using user_id as identity
            veza_user = idp.add_user(
                name=user.get("name"),
                full_name=user.get("name"),
                email=user.get("email"),
                identity=user.get("user_id")  # Use Auth0 user_id as identity
            )

            # Set Auth0-specific properties
            veza_user.set_property("last_login", user.get("last_login"))
            veza_user.set_property("logins_count", user.get("logins_count", 0))
            veza_user.set_property("blocked", user.get("blocked", False))
            veza_user.set_property("email_verified", user.get("email_verified", False))
            veza_user.set_property("connection", user.get("connection", ""))
            veza_user.set_property("organization", user.get("organization", ""))

            # Add user permissions
            permissions = fetch_user_permissions(auth0_client, user.get("user_id"))
            for permission in permissions:
                app_id = permission.get("resource_server_identifier")
                permission_name = permission.get("permission_name")
                if app_id and permission_name:
                    # Create unique app assignment ID using user_id, app_id, and permission_name
                    assignment_id = f"{user.get('user_id')}_{app_id}_{permission_name}"
                    try:
                        veza_user.add_app_assignment(
                            id=assignment_id,
                            name=permission_name,
                            app_id=app_id
                        )
                    except OAATemplateException as e:
                        if "already exists" in str(e):
                            logger.warning(f"Skipping duplicate app assignment {assignment_id} for user {user.get('name')}")
                            continue
                        raise

        # Fetch and process Auth0 roles
        logger.info("Fetching Auth0 roles")
        auth0_roles = fetch_auth0_roles(auth0_client)
        logger.info(f"Found {len(auth0_roles)} roles")
        for role in auth0_roles:
            if isinstance(role, dict):
                # Create role as a group in Veza using role ID as identity
                veza_role = idp.add_group(
                    name=role.get("name", ""),
                    full_name=role.get("description", ""),
                    identity=role.get("id")  # Use Auth0 role ID as identity
                )
                
                # Add role permissions
                permissions = fetch_role_permissions(auth0_client, role.get("id", ""))
                for permission in permissions:
                    app_id = permission.get("resource_server_identifier")
                    permission_name = permission.get("permission_name")
                    if app_id and permission_name:
                        # Create unique app assignment ID using role_id, app_id, and permission_name
                        assignment_id = f"{role.get('id')}_{app_id}_{permission_name}"
                        try:
                            veza_role.add_app_assignment(
                                id=assignment_id,
                                name=permission_name,
                                app_id=app_id
                            )
                        except OAATemplateException as e:
                            if "already exists" in str(e):
                                logger.warning(f"Skipping duplicate app assignment {assignment_id} for role {role.get('name')}")
                                continue
                            raise
            else:
                print(f"Warning: Skipping invalid role format: {role}")

        # Push the metadata to Veza
        logger.info(f"Checking for existing provider: {provider_name}")
        
        @retry_with_backoff
        def get_or_create_provider():
            provider = veza_con.get_provider(provider_name)
            if provider:
                logger.info("Found existing provider")
            else:
                logger.info(f"Creating new provider: {provider_name}")
                provider = veza_con.create_provider(provider_name, "identity_provider")
            return provider

        provider = get_or_create_provider()
        logger.info(f"Provider: {provider['name']} ({provider['id']})")

        @retry_with_backoff
        def push_to_veza():
            logger.info("Pushing metadata to Veza")
            # Use the correct data source name format
            response = veza_con.push_application(
                provider_name,
                data_source_name=f"{idp.name} ({idp.idp_type})",
                application_object=idp,
                save_json=True
            )
            if response.get("warnings", None):
                logger.warning("Push succeeded with warnings:")
                for e in response["warnings"]:
                    logger.warning(f"  - {e}")
            return response

        try:
            response = push_to_veza()
            logger.info("Successfully pushed metadata to Veza")
        except OAAClientError as e:
            logger.error(f"Error pushing to Veza: {e.error}: {e.message} ({e.status_code})")
            if hasattr(e, "details"):
                for d in e.details:
                    logger.error(f"  -- {d}")
            raise

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        logger.error("Stack trace:", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main() 