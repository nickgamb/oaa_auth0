# Auth0 Integration for Veza Open Authorization API

This integration uses the Auth0 Management API to model an Auth0 Identity Provider in Veza. It fetches users, roles, permissions, and other metadata from Auth0 and pushes it to Veza for analysis and visualization.

## Prerequisites

- Python 3.9 or higher
- Auth0 Management API access with the following permissions:
  - `read:users`
  - `read:roles`
  - `read:resource_servers`
  - `read:clients`
  - `read:organizations`
  - `read:connections`
- Veza API key and URL

## Environment Variables

Create a `.env` file with the following variables:

```bash
export VEZA_API_KEY="your-veza-api-key"
export VEZA_URL="https://your-veza-instance.vezacloud.com"
export AUTH0_DOMAIN="your-tenant.auth0.com"
export AUTH0_CLIENT_ID="your-client-id"
export AUTH0_CLIENT_SECRET="your-client-secret"
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/your-name/oaa_auth0.git
cd oaa_auth0
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the integration script:
```bash
python3 auth0_provider.py
```

The script will:
1. Connect to Auth0 and fetch:
   - Users and their permissions
   - Roles and their permissions
   - Resource servers (APIs)
   - Clients (applications)
   - Organizations
   - Connections
2. Create a provider in Veza named "Auth0"
3. Push the metadata to Veza for analysis

## Features

- **User Management**
  - Fetches all Auth0 users
  - Tracks user properties:
    - Last login
    - Login count
    - Blocked status
    - Email verification status
    - Connection
    - Organization
  - Maps user permissions to Veza app assignments

- **Role Management**
  - Fetches all Auth0 roles
  - Maps role permissions to Veza app assignments
  - Creates role groups in Veza

- **Resource Servers (APIs)**
  - Fetches all Auth0 APIs
  - Maps API permissions to Veza applications
  - Tracks API scopes and descriptions

- **Clients (Applications)**
  - Fetches all Auth0 applications
  - Creates application entries in Veza
  - Tracks application descriptions

- **Organizations and Connections**
  - Fetches Auth0 organizations and connections
  - Creates corresponding groups in Veza

## Error Handling

The integration includes robust error handling:
- Rate limit detection and automatic retry with exponential backoff
- Detailed error logging with timestamps
- Validation of required environment variables
- Graceful handling of API errors
- Automatic provider creation if it doesn't exist

## Troubleshooting

If you encounter issues:
1. Check your environment variables are correctly set
2. Verify your Auth0 Management API access and permissions
3. Check the logs for specific error messages
4. Ensure your Veza API key has the necessary permissions
5. Verify network connectivity to both Auth0 and Veza

Common issues:
- Rate limiting: The script will automatically retry with backoff
- Missing permissions: Check Auth0 Management API permissions
- Invalid credentials: Verify Auth0 client ID and secret
- Network issues: Check connectivity to Auth0 and Veza

## Logging

The integration uses Python's logging module with the following configuration:
- Log level: INFO
- Format: `%(asctime)s - %(levelname)s - %(message)s`
- Output: Standard output

## License

Copyright 2024 Veza Technologies Inc.

Use of this source code is governed by the MIT license that can be found in the LICENSE file or at https://opensource.org/licenses/MIT.
