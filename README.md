# Py-Alpaca-Daily-Losers 📉🐍

**Py-Alpaca-Daily-Losers** is a Python package that integrates with the Alpaca Markets API to identify and analyze daily stock market losers. This tool leverages various market data indicators and advanced AI analysis to provide insightful trading information.

* [PyAlpacaApi](https://github.com/TexasCoding/py-alpaca-api) is used to communicate with Alpaca Markets API.

## Features 🌟

- **Market Data Extraction**: Retrieves daily stock market data using the Alpaca Markets API.
- **Technical Analysis**: Analyzes data with indicators like Bollinger Bands and RSI.
- **News and Sentiment Analysis**: Extracts and analyzes news for sentiment using OpenAI.
- **Notifications**: Sends alerts via Slack.
- **Modular Design**: Structured for easy maintenance and scalability.

## Getting Started 🏁

### Installation

Clone the repository and install dependencies:
```bash
git clone https://github.com/TexasCoding/py-alpaca-daily-losers.git
cd py-alpaca-daily-losers
pip install -r requirements.txt
```

### Usage

Run the application:
```bash
python main.py
```

### Tests

Run the test suite:
```bash
pytest
```

## Project Structure 📂

```
py-alpaca-daily-losers/
├── README.md
├── poetry.lock
├── py_alpaca_daily_losers/
│   ├── __init__.py
│   ├── daily_losers.py
│   └── src/
│       ├── article_extractor.py
│       ├── global_functions.py
│       ├── marketaux.py
│       ├── openai.py
│       └── slack.py
├── pyproject.toml
└── tests/
    └── __init__.py
```

## Contributing 🤝

Contributions are welcome! Here’s how you can help:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Make your changes.
4. Commit your changes (`git commit -m 'Add new feature'`).
5. Push to the branch (`git push origin feature-branch`).
6. Open a Pull Request.

## License 📜

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgments 🙏

Special thanks to the contributors and the open-source community for their support and resources.

For more details, visit the [repository](https://github.com/TexasCoding/py-alpaca-daily-losers).