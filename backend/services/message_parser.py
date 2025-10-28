import re
from typing import Optional, Dict, Any
from enum import Enum


class Intent(str, Enum):
    """User intent types"""
    REGISTRATION = "registration"
    SEND_MONEY = "send_money"
    CHECK_BALANCE = "check_balance"
    TRANSACTION_HISTORY = "transaction_history"
    CONFIRM = "confirm"
    CANCEL = "cancel"
    HELP = "help"
    SETTINGS = "settings"
    UNKNOWN = "unknown"


class MessageParser:
    """Parse user messages to extract intent and parameters"""
    
    # Intent patterns
    REGISTRATION_PATTERNS = [
        r'\b(hi|hello|hey|start|register|signup|sign up)\b',
    ]
    
    SEND_MONEY_PATTERNS = [
        r'send\s+\$?(\d+\.?\d*)\s+to\s+(.+)',
        r'pay\s+(.+?)\s+\$?(\d+\.?\d*)',
        r'transfer\s+\$?(\d+\.?\d*)\s+to\s+(.+)',
    ]
    
    BALANCE_PATTERNS = [
        r'\b(balance|bal|how much|wallet)\b',
    ]
    
    HISTORY_PATTERNS = [
        r'\b(history|transactions|activity|statement)\b',
    ]
    
    CONFIRM_PATTERNS = [
        r'\b(confirm|yes|y|proceed|ok|okay)\b',
    ]
    
    CANCEL_PATTERNS = [
        r'\b(cancel|no|n|abort|stop)\b',
    ]
    
    HELP_PATTERNS = [
        r'\b(help|commands|what can|how to)\b',
    ]
    
    SETTINGS_PATTERNS = [
        r'\b(settings|preferences|config|setup)\b',
    ]
    
    @classmethod
    def parse(cls, message: str) -> Dict[str, Any]:
        """
        Parse message and extract intent with parameters
        
        Returns:
            {
                'intent': Intent,
                'params': {...},
                'raw_message': str
            }
        """
        message = message.strip().lower()
        
        result = {
            'intent': Intent.UNKNOWN,
            'params': {},
            'raw_message': message
        }
        
        # Check registration
        if cls._matches_pattern(message, cls.REGISTRATION_PATTERNS):
            result['intent'] = Intent.REGISTRATION
            return result
        
        # Check send money
        send_match = cls._extract_send_money(message)
        if send_match:
            result['intent'] = Intent.SEND_MONEY
            result['params'] = send_match
            return result
        
        # Check balance
        if cls._matches_pattern(message, cls.BALANCE_PATTERNS):
            result['intent'] = Intent.CHECK_BALANCE
            return result
        
        # Check history
        if cls._matches_pattern(message, cls.HISTORY_PATTERNS):
            result['intent'] = Intent.TRANSACTION_HISTORY
            return result
        
        # Check confirm
        if cls._matches_pattern(message, cls.CONFIRM_PATTERNS):
            result['intent'] = Intent.CONFIRM
            return result
        
        # Check cancel
        if cls._matches_pattern(message, cls.CANCEL_PATTERNS):
            result['intent'] = Intent.CANCEL
            return result
        
        # Check help
        if cls._matches_pattern(message, cls.HELP_PATTERNS):
            result['intent'] = Intent.HELP
            return result
        
        # Check settings
        if cls._matches_pattern(message, cls.SETTINGS_PATTERNS):
            result['intent'] = Intent.SETTINGS
            return result
        
        return result
    
    @classmethod
    def _matches_pattern(cls, message: str, patterns: list) -> bool:
        """Check if message matches any pattern in list"""
        for pattern in patterns:
            if re.search(pattern, message, re.IGNORECASE):
                return True
        return False
    
    @classmethod
    def _extract_send_money(cls, message: str) -> Optional[Dict[str, Any]]:
        """Extract amount and recipient from send money message"""
        for pattern in cls.SEND_MONEY_PATTERNS:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                groups = match.groups()
                
                # Pattern 1: "send $20 to John"
                if len(groups) == 2 and groups[0].replace('.', '').isdigit():
                    return {
                        'amount': float(groups[0]),
                        'recipient': groups[1].strip()
                    }
                
                # Pattern 2: "pay John $20"
                if len(groups) == 2 and groups[1].replace('.', '').isdigit():
                    return {
                        'amount': float(groups[1]),
                        'recipient': groups[0].strip()
                    }
        
        return None


# Example usage and testing
if __name__ == "__main__":
    test_messages = [
        "Hi",
        "Send $50 to Alice",
        "pay Bob $25.50",
        "What's my balance?",
        "Show transactions",
        "confirm",
        "help me",
        "random text"
    ]
    
    parser = MessageParser()
    for msg in test_messages:
        result = parser.parse(msg)
        print(f"'{msg}' -> {result['intent']}, params: {result['params']}")