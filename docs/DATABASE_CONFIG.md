# Database Configuration Guide

## Overview

The application supports two methods for configuring the database connection:

1. **Individual Components** (Recommended) - Separate environment variables for each component
2. **DATABASE_URL** - Single connection string

## Method 1: Individual Components (Recommended)

This method provides more flexibility and is easier to manage in different environments.

### Configuration in `.env`

```bash
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your-password-here
DB_NAME=web_crawler_dev
```

### Advantages
- ✅ Clear and explicit configuration
- ✅ Easy to change individual components
- ✅ Works well with environment-specific configs
- ✅ Better for Docker/Kubernetes deployments
- ✅ Password can be empty for local development

### Examples

**Local Development (no password):**
```bash
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=
DB_NAME=web_crawler_dev
```

**Local Development (with password):**
```bash
DB_HOST=localhost
DB_PORT=5432
DB_USER=myuser
DB_PASSWORD=mypassword
DB_NAME=web_crawler_dev
```

**Docker Compose:**
```bash
DB_HOST=db
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=web_crawler_dev
```

**Remote Database:**
```bash
DB_HOST=db.example.com
DB_PORT=5432
DB_USER=prod_user
DB_PASSWORD=secure_password
DB_NAME=web_crawler_prod
```

**AWS RDS:**
```bash
DB_HOST=mydb.abc123.us-east-1.rds.amazonaws.com
DB_PORT=5432
DB_USER=admin
DB_PASSWORD=MySecurePassword123
DB_NAME=web_crawler
```

## Method 2: DATABASE_URL

This method uses a single connection string.

### Configuration in `.env`

```bash
# This will override individual components if both are set
DATABASE_URL=postgresql://username:password@localhost:5432/web_crawler_dev
```

### Format

```
postgresql://[user[:password]@][host][:port][/dbname]
```

### Examples

**Local (no auth):**
```bash
DATABASE_URL=postgresql://localhost/web_crawler_dev
```

**Local (with auth):**
```bash
DATABASE_URL=postgresql://user:pass@localhost:5432/web_crawler_dev
```

**Remote:**
```bash
DATABASE_URL=postgresql://user:pass@db.example.com:5432/production
```

**Special Characters in Password:**
```bash
# URL-encode special characters
DATABASE_URL=postgresql://user:p%40ssw%23rd@localhost/db
```

### Advantages
- ✅ Single variable to manage
- ✅ Compatible with many PaaS platforms (Heroku, Railway, etc.)
- ✅ Easy to copy/paste entire connection string

### Disadvantages
- ❌ Less readable
- ❌ Harder to change individual parts
- ❌ Special characters in password need URL encoding

## How It Works

The configuration logic in [app/config.py](../app/config.py) works as follows:

```python
@staticmethod
def get_database_url():
    # 1. Check if DATABASE_URL is set
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url  # Use DATABASE_URL directly

    # 2. Otherwise, build from individual components
    db_user = os.getenv("DB_USER", "postgres")
    db_password = os.getenv("DB_PASSWORD", "")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "web_crawler_dev")

    # 3. Construct the URL
    if db_password:
        return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    else:
        return f"postgresql://{db_user}@{db_host}:{db_port}/{db_name}"
```

## Priority

If both methods are configured, **DATABASE_URL takes priority** and individual components are ignored.

```bash
# This configuration:
DATABASE_URL=postgresql://user:pass@remote:5432/prod
DB_HOST=localhost  # IGNORED
DB_PORT=5432       # IGNORED
DB_USER=postgres   # IGNORED
DB_PASSWORD=       # IGNORED
DB_NAME=dev        # IGNORED

# Will connect to: remote:5432/prod
```

## Additional Database Settings

### Connection Pool Settings

```bash
# Maximum number of connections in the pool
DB_POOL_SIZE=10

# Maximum overflow connections beyond pool_size
DB_MAX_OVERFLOW=20
```

These settings control how SQLAlchemy manages database connections:

- **DB_POOL_SIZE**: Number of connections to keep open (default: 10)
- **DB_MAX_OVERFLOW**: Additional connections allowed when pool is full (default: 20)
- **Total max connections**: DB_POOL_SIZE + DB_MAX_OVERFLOW = 30

### Auto-Configuration in Code

The following are set automatically in [app/config.py](../app/config.py):

```python
SQLALCHEMY_ENGINE_OPTIONS = {
    "pool_size": 10,           # From DB_POOL_SIZE
    "pool_recycle": 3600,      # Recycle connections after 1 hour
    "pool_pre_ping": True,     # Test connection before using
    "max_overflow": 20         # From DB_MAX_OVERFLOW
}
```

## Environment-Specific Configuration

### Development
```bash
FLASK_ENV=development
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=
DB_NAME=web_crawler_dev
```

### Testing
```bash
FLASK_ENV=testing
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=
DB_NAME=web_crawler_test
```

### Production
```bash
FLASK_ENV=production
DB_HOST=prod-db.example.com
DB_PORT=5432
DB_USER=prod_user
DB_PASSWORD=secure_prod_password
DB_NAME=web_crawler_prod
```

## Verification

### Check Current Configuration

```bash
# Start Python shell
python

# Load and print config
from app import create_app
app = create_app()
print(app.config['SQLALCHEMY_DATABASE_URI'])
```

### Test Connection

```bash
# Try connecting to database
psql -h localhost -p 5432 -U postgres -d web_crawler_dev

# Or using the environment variables
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME
```

### Check from Flask Shell

```bash
flask shell

# Test database connection
>>> from app.extensions import db
>>> db.engine.connect()
# Should connect successfully
```

## Troubleshooting

### Connection Refused
```
Error: could not connect to server: Connection refused
```

**Solutions:**
- Check PostgreSQL is running: `pg_isready`
- Verify DB_HOST and DB_PORT
- Check firewall settings

### Authentication Failed
```
Error: FATAL: password authentication failed for user "postgres"
```

**Solutions:**
- Verify DB_USER and DB_PASSWORD
- Check `pg_hba.conf` for authentication settings
- Ensure user exists: `psql -U postgres -c "\du"`

### Database Does Not Exist
```
Error: FATAL: database "web_crawler_dev" does not exist
```

**Solutions:**
- Create database: `createdb web_crawler_dev`
- Or: `psql -U postgres -c "CREATE DATABASE web_crawler_dev;"`
- Verify DB_NAME matches existing database

### URL Encoding Issues
```
Error: invalid connection string
```

**Solutions:**
- URL-encode special characters in password
- Use individual components instead of DATABASE_URL
- Example: `@` → `%40`, `#` → `%23`, `?` → `%3F`

## Security Best Practices

1. **Never commit `.env` to version control**
   ```bash
   # .gitignore should contain:
   .env
   ```

2. **Use strong passwords in production**
   ```bash
   # Bad
   DB_PASSWORD=password

   # Good
   DB_PASSWORD=R@nd0m!Str0ng#P@ssw0rd
   ```

3. **Restrict database user permissions**
   ```sql
   -- Don't use superuser in production
   CREATE USER app_user WITH PASSWORD 'secure_password';
   GRANT CONNECT ON DATABASE web_crawler_prod TO app_user;
   GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
   ```

4. **Use environment-specific credentials**
   - Development: Local database with no/simple password
   - Testing: Separate test database
   - Production: Strong credentials, restricted access

## Migration Between Methods

### From DATABASE_URL to Individual Components

**Before:**
```bash
DATABASE_URL=postgresql://user:pass@host:5432/dbname
```

**After:**
```bash
# Comment out DATABASE_URL
# DATABASE_URL=postgresql://user:pass@host:5432/dbname

# Add individual components
DB_HOST=host
DB_PORT=5432
DB_USER=user
DB_PASSWORD=pass
DB_NAME=dbname
```

### From Individual Components to DATABASE_URL

**Before:**
```bash
DB_HOST=host
DB_PORT=5432
DB_USER=user
DB_PASSWORD=pass
DB_NAME=dbname
```

**After:**
```bash
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# Comment out individual components
# DB_HOST=host
# DB_PORT=5432
# DB_USER=user
# DB_PASSWORD=pass
# DB_NAME=dbname
```

## Summary

**Use Individual Components when:**
- You want clear, explicit configuration
- You're using Docker/Kubernetes
- You need to change components frequently
- You prefer environment-specific config files

**Use DATABASE_URL when:**
- Deploying to PaaS platforms (Heroku, Railway)
- You have a single connection string to manage
- You need quick copy/paste configuration

Both methods are fully supported and will work correctly!

---

**Last Updated:** January 22, 2026
