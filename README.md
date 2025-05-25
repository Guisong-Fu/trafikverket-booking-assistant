# 🚗 Trafikverket Booking Assistant

An AI-powered automation tool for booking Swedish driving license tests through Trafikverket's official website. This project combines intelligent chat interface with browser automation to streamline the booking process.

## 🎯 Features

- **Intelligent Chat Interface**: AI-powered chatbot that collects booking requirements in natural language
- **QR Code Authentication**: Seamless BankID authentication through QR code scanning
- **Browser Automation**: Automated booking process using browser-use technology
- **Multi-language Support**: Supports Swedish and English interactions
- **Real-time Updates**: Live status updates during the booking process

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit     │    │   FastAPI       │    │   Browser       │
│   Frontend      │◄──►│   Backend       │◄──►│   Automation    │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Chat UI       │    │   LangChain     │    │   Trafikverket  │
│   QR Display    │    │   Chatbot       │    │   Website       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.13+
- OpenAI API key
- UV package manager (recommended) or pip

### Installation

1. **Clone the repository**

2. **Install dependencies**
   ```bash
   # Using UV (recommended)
   uv sync
   
   # Or using pip
   pip install -r requirements.txt
   ```

3. install playwright as playwright is required by browser-use:
   ```bash
   playwright install chromium --with-deps --no-shell
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```

### Running the Application

1. **Start the FastAPI backend**
   ```bash
   uv run uvicorn app.main:app --reload
   ```

2. **Start the Streamlit frontend** (in a new terminal)
   ```bash
   uv run streamlit run st-frontend.py
   ```

3. **Access the application**
   - Frontend: http://localhost:8501
   - API Documentation: http://localhost:8000/docs

## 📖 Usage

### Basic Booking Flow

1. **Start a conversation**: Tell the chatbot what kind of test you want to book
   ```
   "I want to book B driver license practical driving test in Uppsala"
   ```

2. **Provide details**: The chatbot will ask for any missing information:
   - License type (A, A1, A2, B, B96, BE, etc.)
   - Test type (practical driving test or theory test)
   - Transmission type (manual or automatic)
   - Preferred locations (up to 4)
   - Time preferences

3. **Confirm details**: Review and confirm your booking requirements

4. **Authenticate**: Scan the QR code with your BankID app

5. **Automated booking**: The system will automatically search and book available slots

### Supported License Types

```
A, A1, A2, B, B96, BE, Bus, Goods, C, C1, C1E, CE, 
D, D1, D1E, DE, Lorry, Train driver, Taxi, AM, 
Tractor, ADR, APV, VVH
```

### Available Test Locations

The system supports all official Trafikverket test locations across Sweden, including:
- Stockholm area: Uppsala, Upplands Väsby, Västerhaninge
- Gothenburg area: Göteborg Högsbo, Göteborg-Hisingen, Kungsbacka
- Malmö area: Malmö, Lund, Helsingborg
- And many more...

## 🛠️ Development

### Project Structure

```
trafikverket/
├── app/
│   ├── api/                 # FastAPI route handlers
│   ├── constants/           # Application constants
│   ├── models/             # Pydantic data models
│   ├── services/           # Business logic
│   └── main.py             # FastAPI application
├── test/                   # Test files
├── st-frontend.py          # Streamlit frontend
├── pyproject.toml          # Project configuration
└── README.md
```

### Key Components

- **Chat Service** (`app/services/chatbot_service.py`): LangChain-powered chatbot for requirement collection
- **Browser Service** (`app/services/browser_service.py`): Browser automation using browser-use
- **Data Models** (`app/models/data_models.py`): Pydantic models for type safety
- **Constants** (`app/constants/`): Valid license types, locations, and messages


## 🔧 Configuration

### Environment Variables

```bash
OPENAI_API_KEY=your_openai_api_key
LOG_LEVEL=INFO
BROWSER_HEADLESS=true  # Set to false for development
```

### Browser Configuration

The browser automation can be configured in `app/services/browser_service.py`:

```python
browser_config = BrowserConfig(
    headless=True,  # Set to False for debugging
    disable_security=True,
    # Additional configuration options...
)
```

## 🚨 Known Issues

- Browser automation reliability needs improvement
- Confirmation flow has some edge cases
- Session persistence between QR auth and booking needs work

See [todo.md](todo.md) for a complete list of known issues and planned improvements.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow Python PEP 8 style guidelines
- Add type hints to all functions
- Write tests for new features
- Update documentation as needed

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This tool is for educational and personal use only. Users are responsible for complying with Trafikverket's terms of service and applicable laws. The authors are not responsible for any misuse or consequences arising from the use of this software.

## 🙏 Acknowledgments

- [browser-use](https://github.com/browser-use/browser-use) for browser automation
- [LangChain](https://langchain.com/) for AI chat capabilities
- [FastAPI](https://fastapi.tiangolo.com/) for the backend framework
- [Streamlit](https://streamlit.io/) for the frontend interface

## 📞 Support

If you encounter any issues or have questions:

1. Check the [todo.md](todo.md) for known issues
2. Search existing GitHub issues
3. Create a new issue with detailed information

---

**Note**: This project is under active development. Some features may be incomplete or unstable. See [todo.md](todo.md) for current status and roadmap.







