<p align="center">
  <img src="https://raw.githubusercontent.com/PKief/vscode-material-icon-theme/ec559a9f6bfd399b82bb44393651661b08aaf7ba/icons/folder-markdown-open.svg" width="100" alt="project-logo">
</p>
<p align="center">
    <h1 align="center">PY-ALPACA-DAILY-LOSERS</h1>
</p>
<p align="center">
    <em>Unleashing strategic insights for daily market victories.</em>
</p>
<p align="center">
	<img src="https://img.shields.io/github/license/TexasCoding/py-alpaca-daily-losers?style=default&logo=opensourceinitiative&logoColor=white&color=0080ff" alt="license">
	<img src="https://img.shields.io/github/last-commit/TexasCoding/py-alpaca-daily-losers?style=default&logo=git&logoColor=white&color=0080ff" alt="last-commit">
	<img src="https://img.shields.io/github/languages/top/TexasCoding/py-alpaca-daily-losers?style=default&color=0080ff" alt="repo-top-language">
	<img src="https://img.shields.io/github/languages/count/TexasCoding/py-alpaca-daily-losers?style=default&color=0080ff" alt="repo-language-count">
<p>
<p align="center">
	<!-- default option, no dependency badges. -->
</p>

<br><!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary><br>

- [ Overview](#-overview)
- [ Features](#-features)
- [ Repository Structure](#-repository-structure)
- [ Modules](#-modules)
- [ Getting Started](#-getting-started)
  - [ Installation](#-installation)
  - [ Usage](#-usage)
  - [ Tests](#-tests)
- [ Project Roadmap](#-project-roadmap)
- [ Contributing](#-contributing)
- [ License](#-license)
- [ Acknowledgments](#-acknowledgments)
</details>
<hr>

##  Overview

The py-alpaca-daily-losers project integrates Alpaca Markets for a daily losers strategy, offering market data extraction, AI analysis, and Slack notifications. The core functionality centers on retrieving and analyzing daily stock market data using indicators like Bollinger Bands and RSI. It provides insights through news extraction, sentiment analysis, and chat functions via OpenAI integration. This project equips users with robust data analysis tools for informed decision-making in the stock market.

This project is in no way trading advice, or a vaild strategy. Any trading done using this package should only be on a paper account, until proven to work.

Visit [PyAlpacaApi](https://github.com/TexasCoding/py-alpaca-api) to learn more about the core of this project.

Visit [AlpacaApiStrategies](https://github.com/TexasCoding/alpaca-api-strategies) for an example app using this strategy.

---

##  Features

|    |   Feature         | Description |
|----|-------------------|---------------------------------------------------------------|
| ⚙️  | **Architecture**  | The project has a modular architecture that integrates various components for market data extraction, AI analysis, and Slack notifications. It leverages external APIs effectively within its architecture. |
| 🔩 | **Code Quality**  | The codebase maintains good practices and follows a consistent style throughout. It includes clear documentation and comments for better understanding. |
| 📄 | **Documentation** | The project provides extensive documentation explaining different modules and functionalities. It helps users understand the purpose and usage of each component clearly. |
| 🔌 | **Integrations**  | Key integrations include Alpaca API for market data, OpenAI for sentiment analysis, and Slack for notifications. External dependencies are managed efficiently. |
| 🧩 | **Modularity**    | The codebase is structured in a modular manner, promoting reusability and easy maintenance. Each module serves a specific purpose, enhancing code organization. |
| 🧪 | **Testing**       | Testing frameworks are not explicitly mentioned in the details provided. Additional information would be needed to assess the extent of testing in the project. |
| ⚡️  | **Performance**   | The project efficiently processes market data and conducts analysis, ensuring timely insights for decision-making. Performance optimizations are likely implemented to handle data efficiently. |
| 🛡️ | **Security**      | Measures for data protection and access control are not explicitly mentioned in the details provided. Additional information would be needed to assess the security practices in the project. |
| 📦 | **Dependencies**  | Key external libraries and dependencies include tqdm, openai, toml, requests, python-dotenv, and others. These dependencies are vital for various functionalities within the project. |
| 🚀 | **Scalability**   | The project's architecture and modular design suggest potential scalability to handle increased traffic and load. It can likely accommodate growth with minimal adjustments. |

---

##  Repository Structure

```sh
└── py-alpaca-daily-losers/
    ├── README.md
    ├── poetry.lock
    ├── py_alpaca_daily_losers
    │   ├── __init__.py
    │   ├── daily_losers.py
    │   └── src
    │       ├── __init__.py
    │       ├── article_extractor.py
    │       ├── global_fuctions.py
    │       ├── marketaux.py
    │       ├── openai.py
    │       └── slack.py
    ├── pyproject.toml
    └── tests
        └── __init__.py
```

---

##  Modules

<details closed><summary>.</summary>

| File                                                                                               | Summary                                                                                                                                                                                                                      |
| ---                                                                                                | ---                                                                                                                                                                                                                          |
| [pyproject.toml](https://github.com/TexasCoding/py-alpaca-daily-losers/blob/master/pyproject.toml) | Implements Alpaca Markets integration for Daily Losers strategy using py-alpaca-api. Incorporates critical features for market data extraction, AI integration, and Slack notifications within the repositorys architecture. |

</details>

<details closed><summary>py_alpaca_daily_losers</summary>

| File                                                                                                                        | Summary                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| ---                                                                                                                         | ---                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| [daily_losers.py](https://github.com/TexasCoding/py-alpaca-daily-losers/blob/master/py_alpaca_daily_losers/daily_losers.py) | The `daily_losers.py` file in the `py-alpaca-daily-losers` repository serves as a crucial component for retrieving and analyzing daily stock market data. It leverages various modules such as Bollinger Bands and RSI Indicator to calculate key indicators. Additionally, it integrates external APIs for news extraction and open-source tools for effective data processing. The script pulls relevant market data and conducts in-depth analysis to provide valuable insights for decision-making within the parent repositorys architecture. |

</details>

<details closed><summary>py_alpaca_daily_losers.src</summary>

| File                                                                                                                                      | Summary                                                                                                                                                                                                   |
| ---                                                                                                                                       | ---                                                                                                                                                                                                       |
| [slack.py](https://github.com/TexasCoding/py-alpaca-daily-losers/blob/master/py_alpaca_daily_losers/src/slack.py)                         | Defines a class to send messages to a Slack channel based on provided parameters. Handles sending messages or printing if Slack token is missing. Implements error handling for message sending failures. |
| [openai.py](https://github.com/TexasCoding/py-alpaca-daily-losers/blob/master/py_alpaca_daily_losers/src/openai.py)                       | Implements OpenAI chat and sentiment analysis functions using API keys for financial news within the repositorys architecture.                                                                            |
| [marketaux.py](https://github.com/TexasCoding/py-alpaca-daily-losers/blob/master/py_alpaca_daily_losers/src/marketaux.py)                 | Retrieves recent news links related to a given stock symbol using the MarketAux API. Parses the response to extract valid URLs for further processing within the repositorys architecture.                |
| [global_fuctions.py](https://github.com/TexasCoding/py-alpaca-daily-losers/blob/master/py_alpaca_daily_losers/src/global_fuctions.py)     | Sends messages to Slack based on production environment; utilizes environment variables for settings.                                                                                                     |
| [article_extractor.py](https://github.com/TexasCoding/py-alpaca-daily-losers/blob/master/py_alpaca_daily_losers/src/article_extractor.py) | Extracts article content from URLs using API key-Truncates long text if needed-Retrieves article title and content snippets-Handles API requests and response processing                                  |

</details>

---

##  Getting Started

**System Requirements:**

* **Python**: `version x.y.z`

###  Installation

<h4>From <code>source</code></h4>

> 1. Clone the py-alpaca-daily-losers repository:
>
> ```console
> $ git clone https://github.com/TexasCoding/py-alpaca-daily-losers
> ```
>
> 2. Change to the project directory:
> ```console
> $ cd py-alpaca-daily-losers
> ```
>
> 3. Install the dependencies:
> ```console
> $ pip install -r requirements.txt
> ```

###  Usage

<h4>From <code>source</code></h4>

> Run py-alpaca-daily-losers using the command below:
> ```console
> $ python main.py
> ```

###  Tests

> Run the test suite using the command below:
> ```console
> $ pytest
> ```

---

##  Project Roadmap

- [X] `► INSERT-TASK-1`
- [ ] `► INSERT-TASK-2`
- [ ] `► ...`

---

##  Contributing

Contributions are welcome! Here are several ways you can contribute:

- **[Report Issues](https://github.com/TexasCoding/py-alpaca-daily-losers/issues)**: Submit bugs found or log feature requests for the `py-alpaca-daily-losers` project.
- **[Submit Pull Requests](https://github.com/TexasCoding/py-alpaca-daily-losers/blob/main/CONTRIBUTING.md)**: Review open PRs, and submit your own PRs.
- **[Join the Discussions](https://github.com/TexasCoding/py-alpaca-daily-losers/discussions)**: Share your insights, provide feedback, or ask questions.

<details closed>
<summary>Contributing Guidelines</summary>

1. **Fork the Repository**: Start by forking the project repository to your github account.
2. **Clone Locally**: Clone the forked repository to your local machine using a git client.
   ```sh
   git clone https://github.com/TexasCoding/py-alpaca-daily-losers
   ```
3. **Create a New Branch**: Always work on a new branch, giving it a descriptive name.
   ```sh
   git checkout -b new-feature-x
   ```
4. **Make Your Changes**: Develop and test your changes locally.
5. **Commit Your Changes**: Commit with a clear message describing your updates.
   ```sh
   git commit -m 'Implemented new feature x.'
   ```
6. **Push to github**: Push the changes to your forked repository.
   ```sh
   git push origin new-feature-x
   ```
7. **Submit a Pull Request**: Create a PR against the original project repository. Clearly describe the changes and their motivations.
8. **Review**: Once your PR is reviewed and approved, it will be merged into the main branch. Congratulations on your contribution!
</details>

<details closed>
<summary>Contributor Graph</summary>
<br>
<p align="center">
   <a href="https://github.com{/TexasCoding/py-alpaca-daily-losers/}graphs/contributors">
      <img src="https://contrib.rocks/image?repo=TexasCoding/py-alpaca-daily-losers">
   </a>
</p>
</details>

---

##  License

This project is protected under the [SELECT-A-LICENSE](https://choosealicense.com/licenses) License. For more details, refer to the [LICENSE](https://choosealicense.com/licenses/) file.

---

##  Acknowledgments

- List any resources, contributors, inspiration, etc. here.

[**Return**](#-overview)

---
