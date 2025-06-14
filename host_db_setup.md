# Host Database Setup Guide

This guide explains how to set up PostgreSQL on your host machine to connect with Django running in VirtualBox.

## Prerequisites

- PostgreSQL installed on your host machine
- VirtualBox with Django project running
- Network connectivity between host and VirtualBox

## Step 1: Install PostgreSQL on Host Machine

If not already installed, install PostgreSQL on your host machine:

### Windows
- Download and install from [PostgreSQL official website](https://www.postgresql.org/download/windows/)
- Remember the password you set for the 'postgres' user during installation

### macOS
```bash
brew install postgresql
brew services start postgresql
```

### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

## Step 2: Create Database and User

1. Connect to PostgreSQL as the postgres user:

```bash
# Windows
psql -U postgres

# macOS
sudo -u postgres psql

# Linux
sudo -u postgres psql
```

2. Create the database and user (adjust as needed):

```sql
CREATE DATABASE reservehub;
CREATE USER django WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE reservehub TO django;
\q
```

## Step 3: Configure PostgreSQL to Allow Remote Connections

### 1. Locate PostgreSQL Configuration Files

The location depends on your operating system:

- Windows: `C:\Program Files\PostgreSQL\[version]\data\`
- macOS: `/usr/local/var/postgres/` or `/opt/homebrew/var/postgres`
- Linux: `/etc/postgresql/[version]/main/`

### 2. Edit postgresql.conf

Find and modify these lines:
```
listen_addresses = '*'
port = 2002
```

### 3. Edit pg_hba.conf

Add these lines at the end of the file to allow connections from your VirtualBox VM:

```
# Allow connections from VirtualBox VM
host    all             all             10.0.2.0/24            md5
host    all             all             0.0.0.0/0              md5
```

### 4. Restart PostgreSQL

```bash
# Windows - Use Services application or
pg_ctl restart -D "C:\Program Files\PostgreSQL\[version]\data"

# macOS
brew services restart postgresql

# Linux
sudo systemctl restart postgresql
```

## Step 4: Configure Firewall (if needed)

Ensure that port 5432 is open on your host machine's firewall.

### Windows
1. Open Windows Defender Firewall
2. Click "Advanced settings"
3. Click "Inbound Rules" > "New Rule"
4. Select "Port" > "TCP" > Enter "5432" > Allow the connection > Name it "PostgreSQL"

### macOS
```bash
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /opt/homebrew/opt/postgresql/bin/postgres
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --unblockapp /opt/homebrew/opt/postgresql/bin/postgres
```

### Linux
```bash
sudo ufw allow 5432/tcp
```

## Step 5: Update Your .env File

Make sure your `.env` file has the correct settings:

```
USE_HOST_DB=True
DB_NAME=reservehub
DB_USER=django  # or 'postgres' if you didn't create a new user
DB_PASSWORD=your_password
DB_HOST=10.0.2.2  # This is typically the host machine's IP as seen from VirtualBox
DB_PORT=2002
```

## Step 6: Test the Connection

Run the test script from your Django project directory:

```bash
python test_db_connection.py
```

## Step 7: Apply Migrations

Once the connection is established, run migrations:

```bash
python manage.py migrate
```

## Troubleshooting

1. **Connection Refused Error**:
   - Verify PostgreSQL is running on the host
   - Check firewall settings
   - Ensure `postgresql.conf` has correct port (2002) and `listen_addresses = '*'`
   - Make sure the firewall allows connections on port 2002

2. **Authentication Failed**:
   - Verify username and password in .env file
   - Check pg_hba.conf has the correct authentication method

3. **Database Does Not Exist**:
   - Connect to PostgreSQL and create the database:
     ```sql
     CREATE DATABASE reservehub;
     ```

4. **Wrong IP Address**:
   - The host machine's IP as seen from VirtualBox is usually 10.0.2.2
   - Run `ip route | grep default` in the VM to find the gateway IP