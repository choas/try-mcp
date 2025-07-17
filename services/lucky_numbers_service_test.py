import random
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union, Any

from services.base_service import BaseService
from data.models import ToolResult


# For testing purposes
def get_datetime_now():
    """Get the current datetime. This function can be mocked for testing."""
    return datetime.now()


class LuckyNumbersServiceTest(BaseService):
    """Service for generating 'statistically blessed' lucky numbers for various scenarios."""
    
    def __init__(self):
        """Initialize the Lucky Numbers service."""
        super().__init__(
            name="lucky-numbers",
            version="v1",
            description="Generates statistically blessed numbers for various life scenarios"
        )

    # Define scenarios with their specific configurations
    SCENARIOS = {
        "lottery": {
            "description": "Numbers for lottery games and jackpots",
            "default_count": 6,
            "default_min": 1,
            "default_max": 49,
            "emoji": "🎯 🍀 💰",
            "methodologies": [
                "Cosmic Alignment Calculation",
                "Golden Ratio Harmonics",
                "Fibonacci Sequence Mapping",
                "Lunar Phase Correlation",
                "Quantum Fluctuation Analysis"
            ]
        },
        "decision": {
            "description": "A single number to help make binary decisions",
            "default_count": 1,
            "default_min": 1,
            "default_max": 2,
            "emoji": "🤔 ⚖️ 🔮",
            "methodologies": [
                "Quantum Decision Matrix",
                "Synchronicity Pattern Analysis",
                "Intuitive Resonance Mapping",
                "Destiny Path Calculation",
                "Karmic Balance Equation"
            ]
        },
        # Add other scenarios here...
    }

    # Energy level descriptions and their impact factors
    ENERGY_LEVELS = {
        "low": {
            "description": "Subtle cosmic influence with gentle guidance",
            "factor": 0.8,
            "alignment_range": (60, 75)
        },
        "medium": {
            "description": "Balanced energetic flow with moderate cosmic alignment",
            "factor": 1.0,
            "alignment_range": (75, 85)
        },
        "high": {
            "description": "Powerful mystical forces with strong manifestation potential",
            "factor": 1.2,
            "alignment_range": (85, 95)
        },
        "extreme": {
            "description": "Extraordinary cosmic convergence with maximum blessing potential",
            "factor": 1.5,
            "alignment_range": (95, 100)
        }
    }

    def get_tools(self) -> List[Dict]:
        """Return the tools provided by this service."""
        return [
            {
                "name": "generate_blessed_numbers",
                "description": "Generates mystically optimized numbers for various life scenarios",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "scenario": {
                            "type": "string",
                            "description": "The scenario for which you need lucky numbers",
                            "enum": list(self.SCENARIOS.keys())
                        },
                        "count": {
                            "type": "integer",
                            "description": "Number of lucky numbers to generate (optional)",
                            "minimum": 1,
                            "maximum": 10
                        },
                        "min_value": {
                            "type": "integer",
                            "description": "Minimum value for generated numbers (optional)"
                        },
                        "max_value": {
                            "type": "integer",
                            "description": "Maximum value for generated numbers (optional)"
                        },
                        "energy_level": {
                            "type": "string",
                            "description": "Intensity of cosmic energy applied to number generation",
                            "enum": list(self.ENERGY_LEVELS.keys()),
                            "default": "medium"
                        }
                    },
                    "required": ["scenario"]
                }
            }
        ]

    async def handle_request(self, method: str, params: Dict) -> ToolResult:
        """Handle incoming requests to the Lucky Numbers service."""
        if method == "generate_blessed_numbers":
            result = await self._generate_blessed_numbers(params)
            if result.get("status") == "error":
                return self._create_error_response(result.get("error", "Unknown error"))
            else:
                # Format the successful response as a ToolResult
                return ToolResult(
                    content=[{
                        "type": "text",
                        "text": self._format_success_response(result)
                    }],
                    is_error=False
                )
        else:
            return self._create_error_response(f"Method '{method}' not found in Lucky Numbers service")

    async def _generate_blessed_numbers(self, params: Dict) -> Dict:
        """Generate blessed numbers based on the specified scenario and parameters."""
        # Extract and validate parameters
        scenario = params.get("scenario")
        if scenario not in self.SCENARIOS:
            return {
                "error": f"Invalid scenario: {scenario}. Available scenarios: {', '.join(self.SCENARIOS.keys())}",
                "status": "error"
            }

        # Get scenario configuration
        scenario_config = self.SCENARIOS[scenario]
        
        # Extract optional parameters with defaults from scenario config
        count = params.get("count", scenario_config["default_count"])
        min_value = params.get("min_value", scenario_config["default_min"])
        max_value = params.get("max_value", scenario_config["default_max"])
        energy_level = params.get("energy_level", "medium")

        # Validate parameters
        if not isinstance(count, int) or count < 1 or count > 10:
            return {
                "error": "Count must be an integer between 1 and 10",
                "status": "error"
            }
        
        if not isinstance(min_value, int) or not isinstance(max_value, int):
            return {
                "error": "Min and max values must be integers",
                "status": "error"
            }
            
        if min_value >= max_value:
            return {
                "error": "Min value must be less than max value",
                "status": "error"
            }
            
        if energy_level not in self.ENERGY_LEVELS:
            return {
                "error": f"Invalid energy level: {energy_level}. Available levels: {', '.join(self.ENERGY_LEVELS.keys())}",
                "status": "error"
            }

        # Generate the blessed numbers
        blessed_numbers = self._calculate_blessed_numbers(
            scenario, count, min_value, max_value, energy_level
        )
        
        # Calculate cosmic alignment percentage
        alignment = self._calculate_cosmic_alignment(scenario, energy_level)
        
        # Select a mystical methodology explanation
        methodology = self._select_methodology(scenario)
        
        # Format the response
        return {
            "blessed_numbers": blessed_numbers,
            "scenario": scenario,
            "scenario_description": scenario_config["description"],
            "cosmic_alignment": f"{alignment}%",
            "mystical_methodology": methodology,
            "energy_level": energy_level,
            "energy_description": self.ENERGY_LEVELS[energy_level]["description"],
            "message": self._generate_encouraging_message(scenario, alignment),
            "emoji": scenario_config["emoji"],
            "timestamp": get_datetime_now().isoformat(),
            "status": "success"
        }

    def _calculate_blessed_numbers(
        self, scenario: str, count: int, min_value: int, max_value: int, energy_level: str
    ) -> List[int]:
        """Calculate statistically blessed numbers based on scenario and parameters."""
        # Apply energy factor to the random seed for consistent but varied results
        energy_factor = self.ENERGY_LEVELS[energy_level]["factor"]
        seed_value = int(get_datetime_now().timestamp() * energy_factor) % 10000
        random.seed(seed_value)
        
        # Generate unique numbers
        numbers = set()
        while len(numbers) < count:
            # Use scenario-specific logic to generate numbers
            if scenario == "lottery":
                # For lottery, ensure truly random distribution
                num = random.randint(min_value, max_value)
            else:
                # For other scenarios, use standard random generation
                num = random.randint(min_value, max_value)
                
            numbers.add(num)
            
        # Convert to sorted list for consistent output
        return sorted(list(numbers))

    def _calculate_cosmic_alignment(self, scenario: str, energy_level: str) -> int:
        """Calculate the cosmic alignment percentage for the generated numbers."""
        # Base alignment from energy level
        min_alignment, max_alignment = self.ENERGY_LEVELS[energy_level]["alignment_range"]
        
        # Add some variability based on current time
        current_time = get_datetime_now()
        hour_factor = current_time.hour / 24.0  # 0.0 to 1.0 based on hour of day
        minute_factor = current_time.minute / 60.0  # 0.0 to 1.0 based on minute
        
        # Calculate alignment with some randomness but weighted toward the energy level range
        base = min_alignment + (max_alignment - min_alignment) * random.random()
        time_influence = (hour_factor + minute_factor) * 5  # Up to 5% influence from time
        
        # Final alignment with some scenario-specific adjustment
        scenario_factor = 1.0
        if scenario in ["lottery", "love"]:
            scenario_factor = 1.05  # Slightly higher for emotional scenarios
        elif scenario in ["health", "career"]:
            scenario_factor = 0.98  # Slightly lower for practical scenarios
            
        alignment = int(min(100, (base + time_influence) * scenario_factor))
        return alignment

    def _select_methodology(self, scenario: str) -> str:
        """Select a mystical methodology explanation for the number generation."""
        methodologies = self.SCENARIOS[scenario]["methodologies"]
        return random.choice(methodologies)

    def _generate_encouraging_message(self, scenario: str, alignment: int) -> str:
        """Generate an encouraging message based on scenario and alignment."""
        high_alignment_messages = [
            "The cosmic forces are strongly aligned in your favor today!",
            "These numbers resonate with extraordinary mystical energy!"
        ]
        
        medium_alignment_messages = [
            "These numbers carry positive energy from the universal consciousness.",
            "The mystical forces have smiled upon your number selection."
        ]
        
        low_alignment_messages = [
            "These numbers offer gentle guidance from the cosmic realm.",
            "While subtle, the mystical energy in these numbers will support your journey."
        ]
        
        # Select base message based on alignment
        if alignment >= 90:
            base_messages = high_alignment_messages
        elif alignment >= 75:
            base_messages = medium_alignment_messages
        else:
            base_messages = low_alignment_messages
            
        return random.choice(base_messages)
        
    def _format_success_response(self, result: Dict) -> str:
        """Format the successful response as a human-readable text.
        
        Args:
            result: The result dictionary from _generate_blessed_numbers
            
        Returns:
            Formatted text response
        """
        emoji = result["emoji"]
        numbers = result["blessed_numbers"]
        scenario = result["scenario"]
        scenario_desc = result["scenario_description"]
        alignment = result["cosmic_alignment"]
        methodology = result["mystical_methodology"]
        message = result["message"]
        energy_desc = result["energy_description"]
        
        # Format the response in a visually appealing way
        response = f"{emoji}\n\n"
        response += f"✨ LUCKY NUMBERS FOR {scenario.upper()} ✨\n\n"
        response += f"Your blessed numbers: {', '.join(map(str, numbers))}\n\n"
        response += f"Scenario: {scenario_desc}\n"
        response += f"Cosmic Alignment: {alignment}\n"
        response += f"Mystical Methodology: {methodology}\n"
        response += f"Energy Level: {energy_desc}\n\n"
        response += f"{message}"
        
        return response