"""Order models for Coinbase integration."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any

class OrderSide(str, Enum):
    """Order side enumeration."""
    
    BUY = "buy"
    SELL = "sell"

class OrderType(str, Enum):
    """Order type enumeration."""
    
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"
    TRAILING_STOP = "trailing_stop"

class OrderStatus(str, Enum):
    """Order status enumeration."""
    
    OPEN = "open"
    PENDING = "pending"
    ACTIVE = "active"
    DONE = "done"
    REJECTED = "rejected"
    CANCELLED = "cancelled"

class TimeInForce(str, Enum):
    """Time in force options."""
    
    GTC = "GTC"  # Good till cancelled
    GTT = "GTT"  # Good till time
    IOC = "IOC"  # Immediate or cancel
    FOK = "FOK"  # Fill or kill

@dataclass
class StopPrice:
    """Stop price configuration."""
    
    stop_price: float
    limit_price: Optional[float] = None  # For stop-limit orders
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to API parameters.
        
        Returns:
            API parameters
        """
        params = {"stop_price": str(self.stop_price)}
        if self.limit_price is not None:
            params["price"] = str(self.limit_price)
        return params

@dataclass
class TrailingStop:
    """Trailing stop configuration."""
    
    trail_value: float
    trail_type: str = "percentage"  # percentage or value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to API parameters.
        
        Returns:
            API parameters
        """
        return {
            "trail_value": str(self.trail_value),
            "trail_type": self.trail_type
        }

@dataclass
class Order:
    """Order information."""
    
    id: str
    symbol: str
    side: OrderSide
    type: OrderType
    size: float
    price: float
    status: OrderStatus
    created_at: datetime
    filled_size: Optional[float] = None
    executed_price: Optional[float] = None
    remaining_size: Optional[float] = None
    client_order_id: Optional[str] = None
    time_in_force: TimeInForce = TimeInForce.GTC
    stop_price: Optional[StopPrice] = None
    trailing_stop: Optional[TrailingStop] = None
    expire_time: Optional[datetime] = None
    post_only: bool = False
    
    def to_api_params(self) -> Dict[str, Any]:
        """Convert order to API parameters.
        
        Returns:
            API parameters
        """
        params = {
            "type": self.type.value,
            "side": self.side.value,
            "product_id": self.symbol,
            "size": str(self.size),
            "time_in_force": self.time_in_force.value,
            "post_only": self.post_only
        }
        
        # Add price for limit orders
        if self.type in [OrderType.LIMIT, OrderType.STOP_LIMIT]:
            params["price"] = str(self.price)
        
        # Add stop price configuration
        if self.stop_price and self.type in [OrderType.STOP, OrderType.STOP_LIMIT]:
            params.update(self.stop_price.to_dict())
        
        # Add trailing stop configuration
        if self.trailing_stop and self.type == OrderType.TRAILING_STOP:
            params.update(self.trailing_stop.to_dict())
        
        # Add expiry time for GTT orders
        if self.time_in_force == TimeInForce.GTT and self.expire_time:
            params["expire_time"] = self.expire_time.isoformat()
        
        # Add client order ID if specified
        if self.client_order_id:
            params["client_oid"] = self.client_order_id
        
        return params
    
    @classmethod
    def from_api_response(cls, response: Dict[str, Any]) -> "Order":
        """Create order from API response.
        
        Args:
            response: API response data
            
        Returns:
            Order instance
        """
        # Extract stop price configuration
        stop_price = None
        if "stop_price" in response:
            stop_price = StopPrice(
                stop_price=float(response["stop_price"]),
                limit_price=float(response.get("price", 0)) if "price" in response else None
            )
        
        # Extract trailing stop configuration
        trailing_stop = None
        if "trail_value" in response:
            trailing_stop = TrailingStop(
                trail_value=float(response["trail_value"]),
                trail_type=response.get("trail_type", "percentage")
            )
        
        return cls(
            id=response["id"],
            symbol=response["product_id"],
            side=OrderSide(response["side"]),
            type=OrderType(response["type"]),
            size=float(response["size"]),
            price=float(response.get("price", 0)),
            status=OrderStatus(response["status"]),
            created_at=datetime.fromisoformat(response["created_at"].replace("Z", "+00:00")),
            filled_size=float(response["filled_size"]) if "filled_size" in response else None,
            executed_price=float(response["executed_value"]) / float(response["filled_size"]) if "executed_value" in response and float(response.get("filled_size", 0)) > 0 else None,
            remaining_size=float(response["size"]) - float(response.get("filled_size", 0)) if "filled_size" in response else None,
            client_order_id=response.get("client_oid"),
            time_in_force=TimeInForce(response.get("time_in_force", "GTC")),
            stop_price=stop_price,
            trailing_stop=trailing_stop,
            expire_time=datetime.fromisoformat(response["expire_time"].replace("Z", "+00:00")) if "expire_time" in response else None,
            post_only=response.get("post_only", False)
        ) 