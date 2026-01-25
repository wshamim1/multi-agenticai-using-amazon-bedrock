"""
Agent Configurations
Defines all collaborator agent configurations including Lambda functions
"""

from orchestrator import CollaboratorConfig

# Weather Agent Configuration
WEATHER_AGENT = CollaboratorConfig(
    name="weather-agent",
    instruction="You are a weather information expert. Help users get weather forecasts, current conditions, and weather alerts for any location.",
    description="Weather information and forecast agent",
    action_group_name="weather-actions",
    action_group_description="Actions for weather information retrieval",
    lambda_function_name="weather-operations-lambda",
    lambda_handler_code='''
import json
import logging
from datetime import datetime, timedelta
import random

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Handle Weather operations
    """
    logger.info(f"Received event: {json.dumps(event)}")
    
    action = event.get('actionGroup', '')
    function = event.get('function', '')
    parameters = event.get('parameters', [])
    
    try:
        if function == 'get_current_weather':
            location = next((p['value'] for p in parameters if p['name'] == 'location'), 'New York')
            # Mock weather data
            result = {
                "location": location,
                "temperature": random.randint(60, 85),
                "condition": random.choice(["Sunny", "Cloudy", "Rainy", "Partly Cloudy"]),
                "humidity": random.randint(40, 80),
                "wind_speed": random.randint(5, 20),
                "timestamp": datetime.now().isoformat()
            }
        elif function == 'get_forecast':
            location = next((p['value'] for p in parameters if p['name'] == 'location'), 'New York')
            days = int(next((p['value'] for p in parameters if p['name'] == 'days'), 5))
            # Mock forecast data
            forecast = []
            for i in range(days):
                date = (datetime.now() + timedelta(days=i)).strftime('%Y-%m-%d')
                forecast.append({
                    "date": date,
                    "high": random.randint(70, 90),
                    "low": random.randint(50, 70),
                    "condition": random.choice(["Sunny", "Cloudy", "Rainy", "Partly Cloudy"])
                })
            result = {"location": location, "forecast": forecast}
        elif function == 'get_weather_alerts':
            location = next((p['value'] for p in parameters if p['name'] == 'location'), 'New York')
            # Mock alerts
            result = {
                "location": location,
                "alerts": [
                    {"type": "Heat Advisory", "severity": "Moderate", "expires": "2024-01-20T18:00:00"}
                ] if random.random() > 0.5 else []
            }
        else:
            result = {"error": f"Unknown function: {function}"}
        
        return {
            'messageVersion': '1.0',
            'response': {
                'actionGroup': action,
                'function': function,
                'functionResponse': {
                    'responseBody': {
                        'TEXT': {
                            'body': json.dumps(result)
                        }
                    }
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return {
            'messageVersion': '1.0',
            'response': {
                'actionGroup': action,
                'function': function,
                'functionResponse': {
                    'responseBody': {
                        'TEXT': {
                            'body': json.dumps({"error": str(e)})
                        }
                    }
                }
            }
        }
''',
    functions=[
        {
            "name": "get_current_weather",
            "description": "Get current weather conditions for a location",
            "parameters": {
                "location": {
                    "description": "City name or location",
                    "required": True,
                    "type": "string"
                }
            }
        },
        {
            "name": "get_forecast",
            "description": "Get weather forecast for upcoming days",
            "parameters": {
                "location": {
                    "description": "City name or location",
                    "required": True,
                    "type": "string"
                },
                "days": {
                    "description": "Number of days for forecast (1-7)",
                    "required": False,
                    "type": "integer"
                }
            }
        },
        {
            "name": "get_weather_alerts",
            "description": "Get weather alerts and warnings for a location",
            "parameters": {
                "location": {
                    "description": "City name or location",
                    "required": True,
                    "type": "string"
                }
            }
        }
    ],
    enabled=True
)


# Stock Market Agent Configuration
STOCK_AGENT = CollaboratorConfig(
    name="stock-agent",
    instruction="You are a stock market expert. Help users get stock prices, market data, and financial information.",
    description="Stock market and financial data agent",
    action_group_name="stock-actions",
    action_group_description="Actions for stock market operations",
    lambda_function_name="stock-operations-lambda",
    lambda_handler_code='''
import json
import logging
import random
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Handle Stock Market operations
    """
    logger.info(f"Received event: {json.dumps(event)}")
    
    action = event.get('actionGroup', '')
    function = event.get('function', '')
    parameters = event.get('parameters', [])
    
    try:
        if function == 'get_stock_price':
            symbol = next((p['value'] for p in parameters if p['name'] == 'symbol'), 'AAPL')
            # Mock stock data
            base_price = {"AAPL": 175, "GOOGL": 140, "MSFT": 380, "AMZN": 155, "TSLA": 245}
            price = base_price.get(symbol.upper(), 100) + random.uniform(-5, 5)
            result = {
                "symbol": symbol.upper(),
                "price": round(price, 2),
                "change": round(random.uniform(-3, 3), 2),
                "change_percent": round(random.uniform(-2, 2), 2),
                "volume": random.randint(1000000, 50000000),
                "timestamp": datetime.now().isoformat()
            }
        elif function == 'get_market_summary':
            # Mock market summary
            result = {
                "indices": [
                    {"name": "S&P 500", "value": 4783.45, "change": 12.34, "change_percent": 0.26},
                    {"name": "NASDAQ", "value": 15043.12, "change": -23.45, "change_percent": -0.16},
                    {"name": "DOW", "value": 37305.16, "change": 45.67, "change_percent": 0.12}
                ],
                "timestamp": datetime.now().isoformat()
            }
        elif function == 'get_company_info':
            symbol = next((p['value'] for p in parameters if p['name'] == 'symbol'), 'AAPL')
            # Mock company info
            companies = {
                "AAPL": {"name": "Apple Inc.", "sector": "Technology", "market_cap": "2.8T"},
                "GOOGL": {"name": "Alphabet Inc.", "sector": "Technology", "market_cap": "1.7T"},
                "MSFT": {"name": "Microsoft Corporation", "sector": "Technology", "market_cap": "2.9T"}
            }
            result = companies.get(symbol.upper(), {"name": "Unknown", "sector": "N/A", "market_cap": "N/A"})
            result["symbol"] = symbol.upper()
        else:
            result = {"error": f"Unknown function: {function}"}
        
        return {
            'messageVersion': '1.0',
            'response': {
                'actionGroup': action,
                'function': function,
                'functionResponse': {
                    'responseBody': {
                        'TEXT': {
                            'body': json.dumps(result)
                        }
                    }
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return {
            'messageVersion': '1.0',
            'response': {
                'actionGroup': action,
                'function': function,
                'functionResponse': {
                    'responseBody': {
                        'TEXT': {
                            'body': json.dumps({"error": str(e)})
                        }
                    }
                }
            }
        }
''',
    functions=[
        {
            "name": "get_stock_price",
            "description": "Get current stock price and details",
            "parameters": {
                "symbol": {
                    "description": "Stock ticker symbol (e.g., AAPL, GOOGL)",
                    "required": True,
                    "type": "string"
                }
            }
        },
        {
            "name": "get_market_summary",
            "description": "Get overall market summary and major indices",
            "parameters": {}
        },
        {
            "name": "get_company_info",
            "description": "Get company information and details",
            "parameters": {
                "symbol": {
                    "description": "Stock ticker symbol",
                    "required": True,
                    "type": "string"
                }
            }
        }
    ],
    enabled=True
)


# News Agent Configuration
NEWS_AGENT = CollaboratorConfig(
    name="news-agent",
    instruction="You are a news information expert. Help users get latest news, headlines, and articles on various topics.",
    description="News and current events agent",
    action_group_name="news-actions",
    action_group_description="Actions for news retrieval",
    lambda_function_name="news-operations-lambda",
    lambda_handler_code='''
import json
import logging
from datetime import datetime, timedelta
import random

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Handle News operations
    """
    logger.info(f"Received event: {json.dumps(event)}")
    
    action = event.get('actionGroup', '')
    function = event.get('function', '')
    parameters = event.get('parameters', [])
    
    try:
        if function == 'get_top_headlines':
            category = next((p['value'] for p in parameters if p['name'] == 'category'), 'general')
            # Mock headlines
            headlines = [
                {"title": "Tech Giants Announce AI Breakthrough", "source": "Tech News", "published": datetime.now().isoformat()},
                {"title": "Global Markets Show Strong Growth", "source": "Financial Times", "published": (datetime.now() - timedelta(hours=2)).isoformat()},
                {"title": "Climate Summit Reaches Agreement", "source": "World News", "published": (datetime.now() - timedelta(hours=5)).isoformat()},
                {"title": "New Space Mission Launches Successfully", "source": "Science Daily", "published": (datetime.now() - timedelta(hours=8)).isoformat()}
            ]
            result = {"category": category, "headlines": headlines[:3]}
        elif function == 'search_news':
            query = next((p['value'] for p in parameters if p['name'] == 'query'), 'technology')
            # Mock search results
            articles = [
                {
                    "title": f"Latest developments in {query}",
                    "description": f"Comprehensive coverage of recent {query} news",
                    "source": "News Source",
                    "url": "https://example.com/article1",
                    "published": datetime.now().isoformat()
                },
                {
                    "title": f"{query.capitalize()} industry sees major changes",
                    "description": f"Analysis of {query} trends and impacts",
                    "source": "Industry News",
                    "url": "https://example.com/article2",
                    "published": (datetime.now() - timedelta(hours=3)).isoformat()
                }
            ]
            result = {"query": query, "articles": articles}
        elif function == 'get_news_by_source':
            source = next((p['value'] for p in parameters if p['name'] == 'source'), 'BBC')
            # Mock source news
            result = {
                "source": source,
                "articles": [
                    {"title": f"Breaking: {source} reports major event", "published": datetime.now().isoformat()},
                    {"title": f"{source} exclusive interview", "published": (datetime.now() - timedelta(hours=4)).isoformat()}
                ]
            }
        else:
            result = {"error": f"Unknown function: {function}"}
        
        return {
            'messageVersion': '1.0',
            'response': {
                'actionGroup': action,
                'function': function,
                'functionResponse': {
                    'responseBody': {
                        'TEXT': {
                            'body': json.dumps(result)
                        }
                    }
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return {
            'messageVersion': '1.0',
            'response': {
                'actionGroup': action,
                'function': function,
                'functionResponse': {
                    'responseBody': {
                        'TEXT': {
                            'body': json.dumps({"error": str(e)})
                        }
                    }
                }
            }
        }
''',
    functions=[
        {
            "name": "get_top_headlines",
            "description": "Get top news headlines by category",
            "parameters": {
                "category": {
                    "description": "News category (general, business, technology, sports, etc.)",
                    "required": False,
                    "type": "string"
                }
            }
        },
        {
            "name": "search_news",
            "description": "Search for news articles by keyword",
            "parameters": {
                "query": {
                    "description": "Search query or keyword",
                    "required": True,
                    "type": "string"
                }
            }
        },
        {
            "name": "get_news_by_source",
            "description": "Get news from a specific source",
            "parameters": {
                "source": {
                    "description": "News source name (e.g., BBC, CNN, Reuters)",
                    "required": True,
                    "type": "string"
                }
            }
        }
    ],
    enabled=True
)


# List of all available agents
ALL_AGENTS = [WEATHER_AGENT, STOCK_AGENT, NEWS_AGENT]


def get_enabled_agents(disable_weather=False, disable_stock=False, disable_news=False):
    """
    Get list of enabled agents based on flags
    
    Args:
        disable_weather: Disable weather agent
        disable_stock: Disable stock agent
        disable_news: Disable news agent
    
    Returns:
        List of enabled CollaboratorConfig objects
    """
    agents = []
    
    if not disable_weather:
        agents.append(WEATHER_AGENT)
    
    if not disable_stock:
        agents.append(STOCK_AGENT)
    
    if not disable_news:
        agents.append(NEWS_AGENT)
    
    return agents

