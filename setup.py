from setuptools import setup, find_packages

setup(
    name="krypto_trading_bot",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "alpaca-py>=0.39.0",
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "python-dotenv>=1.0.0",
        "requests>=2.31.0",
        "websockets>=11.0.0",
        "ta>=0.10.0",
        "python-telegram-bot>=20.0",
        "schedule>=1.2.0"
    ]
) 