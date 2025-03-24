# SEO Internal Linking Tool - Deployment Repository

This repository contains the production-ready code for the SEO Internal Linking Tool.

## Project Structure

```
maillage-interne/
├── api/          # FastAPI backend
├── frontend/     # React frontend
└── requirements.txt  # Python dependencies
```

## Deployment Instructions

### 1. Prerequisites

- Python 3.9+
- Node.js 18+
- Docker and Docker Compose
- Git

### 2. Initial Setup

```bash
# Clone the repository
git clone https://github.com/BenSlashr/maillage-interne.git

# Navigate to the project directory
cd maillage-interne

# Initialize submodules (if any)
git submodule update --init --recursive
```

### 3. Backend Setup

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Frontend Setup

```bash
cd frontend
npm install
```

### 5. Building for Production

```bash
# Build frontend
cd frontend
npm run build

# Start backend
cd ../api
uvicorn main:app --reload --port 8002
```

## Environment Variables

Create a `.env` file in the `api` directory with the following variables:

```
PORT=8002
```

## Docker Deployment

The project can be deployed using Docker. A `docker-compose.yml` file is provided for easy deployment.

```bash
docker-compose up -d
```

### Docker Volumes

- `uploads`: For file uploads
- `static`: For static files
- `api`: For API code
- `frontend`: For frontend code

## Security

- Use environment variables for sensitive data
- Keep `.env` files out of version control
- Regularly update dependencies
- Use HTTPS in production

## Maintenance

### Updating Dependencies

```bash
# Update Python dependencies
pip install --upgrade -r requirements.txt

# Update Node dependencies
cd frontend
npm update
```

### Cleaning

```bash
# Clean Python cache
find . -type d -name "__pycache__" -exec rm -rf {} +

# Clean Node modules
cd frontend
rm -rf node_modules
npm install
```

## Troubleshooting

### Common Issues

1. Missing `index.html`
   - Ensure all files are properly committed and pushed
   - Check `.gitignore` for excluded files

2. Permission Errors
   - Run commands with `sudo` if needed
   - Check file permissions

3. Port Conflicts
   - Check if ports are in use
   - Modify port numbers in configuration
