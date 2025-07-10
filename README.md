# simulakra

TBA.

## Requirements

- Python 3.7+
- GoPhish server with API access
- SMTP server for warning emails (Mailgun recommended)
- CSV file with target information

## Installation

1. **Clone or download the project files**
   ```bash
   git clone <repository-url>
   cd gophish-automation
   ```

2. **Create a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your actual credentials
   nano .env
   ```

5. **Configure the application**
   ```bash
   # Edit config.yaml with your GoPhish server details and object names
   nano config.yaml
   ```

6. **Prepare target CSV file**
   ```bash
   # Edit targets.csv with your actual target information
   nano targets.csv
   ```

## Configuration

### Environment Variables (.env)

```bash
# GoPhish API
GOPHISH_API_KEY=your_gophish_api_key_here

# Mailgun SMTP (for warning emails)
MAILGUN_SMTP_SERVER=smtp.mailgun.org
MAILGUN_SMTP_PORT=587
MAILGUN_SMTP_USER=your_mailgun_username@your-domain.com
MAILGUN_SMTP_PASS=your_mailgun_password_here
```

### Application Configuration (config.yaml)

- **GoPhish URL and API key**
- **Object names**: SMTP profile, template, and landing page names
- **Campaign settings**: URL, timeout, warning email preferences
- **SMTP settings**: Sender information for warning emails

### Target CSV Format

The CSV file must contain these columns:
- `FirstName`: Target's first name
- `LastName`: Target's last name
- `Email`: Target's email address
- `Position`: Target's job position/title

## GoPhish Setup Requirements

Before running the script, ensure your GoPhish instance has:

1. **SMTP Profile named "MailgunSMTP"** (or update config.yaml)
2. **Email Template named "UZEM_Password_Reset"** (or update config.yaml)
3. **Landing Page named "UZEM_Login"** (or update config.yaml)
4. **Valid API key** with appropriate permissions

## Usage

### Manual Execution

```bash
# Activate virtual environment
source venv/bin/activate

# Run the script
python simulakra.py
```

### Automated Execution (Cron)

Add to crontab for monthly execution on the 1st at 9 AM:

```bash
# Edit crontab
crontab -e

# Add this line (adjust paths as needed)
0 9 1 * * /path/to/venv/bin/python /path/to/simulakra.py >> /var/log/simulakra.log 2>&1
```

### Testing

For testing purposes, you can modify the timeout in config.yaml to a shorter duration:

```yaml
campaign:
  timeout_hours: 1  # Wait only 1 hour for testing
```

