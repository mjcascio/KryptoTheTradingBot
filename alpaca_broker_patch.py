import os
import certifi
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Set SSL certificate path in the environment
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
logger.info(f"SSL_CERT_FILE: {os.environ.get('SSL_CERT_FILE', 'Not set')}")
