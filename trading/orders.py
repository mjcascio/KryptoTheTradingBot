"""Order management functionality for the KryptoBot Trading System."""

from __future__ import annotations

import logging
from typing import Dict, Any, Optional, List, TypedDict, Literal
from datetime import datetime
from enum import Enum, auto
from utils.logging import setup_logging, log_exception

# Set up module logger
logger = setup_logging(__name__)

OrderStatus = Literal['new', 'partially_filled', 'filled', 'cancelled', 'rejected']

class OrderError(Exception):
    """Base exception for order-related errors."""
    pass

class ValidationError(OrderError):
    """Exception raised for order validation errors."""
    pass

class OrderExecutionError(OrderError):
    """Exception raised for order execution errors."""
    pass

class OrderType(Enum):
    """Types of orders that can be placed."""
    MARKET = auto()
    LIMIT = auto()
    STOP = auto()
    STOP_LIMIT = auto()

    def __str__(self) -> str:
        """Return string representation of order type."""
        return self.name.lower()

class OrderSide(Enum):
    """Side of the order (buy/sell)."""
    BUY = auto()
    SELL = auto()

    def __str__(self) -> str:
        """Return string representation of order side."""
        return self.name.lower()

class TimeInForce(Enum):
    """Time in force specifications for orders."""
    DAY = auto()      # Valid for the day
    GTC = auto()      # Good Till Cancelled
    IOC = auto()      # Immediate Or Cancel
    FOK = auto()      # Fill Or Kill

    def __str__(self) -> str:
        """Return string representation of time in force."""
        return self.name.lower()

class OrderUpdate(TypedDict, total=False):
    """Type definition for order update data."""
    status: OrderStatus
    filled_quantity: float
    filled_avg_price: float
    commission: float

class OrderDict(TypedDict):
    """Type definition for order dictionary representation."""
    client_order_id: str
    symbol: str
    side: str
    quantity: float
    order_type: str
    price: Optional[float]
    stop_price: Optional[float]
    time_in_force: str
    status: OrderStatus
    filled_quantity: float
    filled_avg_price: float
    commission: float
    created_at: str
    updated_at: str

class Order:
    """Represents a trading order in the system."""

    def __init__(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        order_type: OrderType = OrderType.MARKET,
        price: Optional[float] = None,
        stop_price: Optional[float] = None,
        time_in_force: TimeInForce = TimeInForce.DAY,
        client_order_id: Optional[str] = None
    ) -> None:
        """Initialize an order.
        
        Args:
            symbol: Trading symbol
            side: Order side (buy/sell)
            quantity: Order quantity
            order_type: Type of order
            price: Limit price (required for limit orders)
            stop_price: Stop price (required for stop orders)
            time_in_force: Time in force specification
            client_order_id: Optional client-specified order ID
            
        Raises:
            ValidationError: If order parameters are invalid
        """
        try:
            self.symbol: str = symbol.upper()
            self.side: OrderSide = side
            self.quantity: float = quantity
            self.order_type: OrderType = order_type
            self.price: Optional[float] = price
            self.stop_price: Optional[float] = stop_price
            self.time_in_force: TimeInForce = time_in_force
            self.client_order_id: str = client_order_id or self._generate_order_id()
            
            self.status: OrderStatus = 'new'
            self.filled_quantity: float = 0.0
            self.filled_avg_price: float = 0.0
            self.commission: float = 0.0
            self.created_at: datetime = datetime.now()
            self.updated_at: datetime = self.created_at
            
            self._validate()
            
            logger.info(
                f"Created {order_type} {side} order for {symbol}: "
                f"{quantity} units at {price if price else 'market'} price"
            )
            
        except Exception as e:
            error_context = {
                'symbol': symbol,
                'side': str(side),
                'quantity': quantity,
                'order_type': str(order_type),
                'price': price,
                'stop_price': stop_price
            }
            logger.exception_context("Error creating order", e, error_context)
            raise OrderError(f"Failed to create order: {str(e)}")
    
    def _validate(self) -> None:
        """Validate order parameters.
        
        Raises:
            ValidationError: If any parameters are invalid
        """
        try:
            # Validate symbol
            if not self.symbol or not isinstance(self.symbol, str):
                raise ValidationError("Invalid symbol")
            
            # Validate quantity
            if not isinstance(self.quantity, (int, float)) or self.quantity <= 0:
                raise ValidationError("Quantity must be a positive number")
            
            # Validate price for limit orders
            if self.order_type in [OrderType.LIMIT, OrderType.STOP_LIMIT]:
                if self.price is None or self.price <= 0:
                    raise ValidationError(f"Price is required for {self.order_type} orders")
            
            # Validate stop price for stop orders
            if self.order_type in [OrderType.STOP, OrderType.STOP_LIMIT]:
                if self.stop_price is None or self.stop_price <= 0:
                    raise ValidationError(f"Stop price is required for {self.order_type} orders")
            
            # Validate side
            if not isinstance(self.side, OrderSide):
                raise ValidationError("Invalid order side")
            
            # Validate order type
            if not isinstance(self.order_type, OrderType):
                raise ValidationError("Invalid order type")
            
            # Validate time in force
            if not isinstance(self.time_in_force, TimeInForce):
                raise ValidationError("Invalid time in force")
                
        except ValidationError as e:
            error_context = self.to_dict()
            logger.exception_context("Order validation failed", e, error_context)
            raise
    
    @log_exception(logger)
    def update(self, update_data: OrderUpdate) -> None:
        """Update order with execution data.
        
        Args:
            update_data: Dictionary containing update information
            
        Raises:
            OrderError: If update fails
        """
        try:
            old_status = self.status
            
            # Update order attributes
            self.status = update_data.get('status', self.status)
            self.filled_quantity = update_data.get('filled_quantity', self.filled_quantity)
            self.filled_avg_price = update_data.get('filled_avg_price', self.filled_avg_price)
            self.commission = update_data.get('commission', self.commission)
            self.updated_at = datetime.now()
            
            # Log status change
            if old_status != self.status:
                logger.info(
                    f"Order {self.client_order_id} status changed: "
                    f"{old_status} -> {self.status}"
                )
            
            # Log fill update
            if 'filled_quantity' in update_data:
                logger.info(
                    f"Order {self.client_order_id} fill update: "
                    f"{self.filled_quantity}/{self.quantity} @ {self.filled_avg_price}"
                )
                
        except Exception as e:
            error_context = {
                'order_id': self.client_order_id,
                'current_state': self.to_dict(),
                'update_data': update_data
            }
            logger.exception_context("Error updating order", e, error_context)
            raise OrderError(f"Failed to update order: {str(e)}")
    
    def _generate_order_id(self) -> str:
        """Generate a unique order ID."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        return f"order_{timestamp}"
    
    def is_filled(self) -> bool:
        """Check if order is completely filled."""
        return self.status == "filled" and self.filled_quantity == self.quantity
    
    def is_active(self) -> bool:
        """Check if order is still active."""
        return self.status in ["new", "partially_filled"]
    
    def to_dict(self) -> OrderDict:
        """Convert order to dictionary format.
        
        Returns:
            Dictionary containing order details
        """
        return {
            'client_order_id': self.client_order_id,
            'symbol': self.symbol,
            'side': str(self.side),
            'quantity': self.quantity,
            'order_type': str(self.order_type),
            'price': self.price,
            'stop_price': self.stop_price,
            'time_in_force': str(self.time_in_force),
            'status': self.status,
            'filled_quantity': self.filled_quantity,
            'filled_avg_price': self.filled_avg_price,
            'commission': self.commission,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class OrderManager:
    """Manages the lifecycle of trading orders."""

    def __init__(self) -> None:
        """Initialize the order manager."""
        self.orders: Dict[str, Order] = {}
        self.filled_orders: Dict[str, Order] = {}
        self.logger = setup_logging(f"{__name__}.OrderManager")
    
    @log_exception(logger)
    def create_order(self, **kwargs: Any) -> Order:
        """Create a new order.
        
        Args:
            **kwargs: Order parameters
            
        Returns:
            Created order object
            
        Raises:
            OrderError: If order creation fails
        """
        try:
            # Convert string enums to proper enum types
            if 'side' in kwargs:
                kwargs['side'] = OrderSide[str(kwargs['side']).upper()]
            if 'order_type' in kwargs:
                kwargs['order_type'] = OrderType[str(kwargs['order_type']).upper()]
            if 'time_in_force' in kwargs:
                kwargs['time_in_force'] = TimeInForce[str(kwargs['time_in_force']).upper()]
            
            # Create and validate order
            order = Order(**kwargs)
            self.orders[order.client_order_id] = order
            
            # Log order creation
            self.logger.info(f"Created order: {order.to_dict()}")
            return order
            
        except Exception as e:
            error_context = {'order_params': kwargs}
            self.logger.exception_context("Error creating order", e, error_context)
            raise OrderError(f"Failed to create order: {str(e)}")
    
    @log_exception(logger)
    def update_order(
        self,
        client_order_id: str,
        update_data: OrderUpdate
    ) -> Optional[Order]:
        """Update an existing order.
        
        Args:
            client_order_id: Order ID to update
            update_data: Update information
            
        Returns:
            Updated order object or None if not found
            
        Raises:
            OrderError: If update fails
        """
        try:
            order = self.orders.get(client_order_id)
            if not order:
                self.logger.warning(f"Order not found: {client_order_id}")
                return None
            
            # Update order
            order.update(update_data)
            self.logger.info(f"Updated order {client_order_id}: {order.to_dict()}")
            
            # Move to filled orders if complete
            if order.is_filled():
                self.filled_orders[client_order_id] = order
                del self.orders[client_order_id]
                self.logger.info(f"Order {client_order_id} completed and moved to filled orders")
            
            return order
            
        except Exception as e:
            error_context = {
                'order_id': client_order_id,
                'update_data': update_data
            }
            self.logger.exception_context("Error updating order", e, error_context)
            raise OrderError(f"Failed to update order: {str(e)}")
    
    @log_exception(logger)
    def cancel_order(self, client_order_id: str) -> bool:
        """Cancel an active order.
        
        Args:
            client_order_id: Order ID to cancel
            
        Returns:
            True if order was cancelled, False otherwise
            
        Raises:
            OrderError: If cancellation fails
        """
        try:
            order = self.orders.get(client_order_id)
            if not order:
                self.logger.warning(f"Order not found: {client_order_id}")
                return False
            
            if not order.is_active():
                self.logger.warning(f"Order {client_order_id} is not active")
                return False
            
            # Cancel order
            order.update({'status': 'cancelled'})
            self.filled_orders[client_order_id] = order
            del self.orders[client_order_id]
            
            self.logger.info(f"Cancelled order {client_order_id}")
            return True
            
        except Exception as e:
            error_context = {'order_id': client_order_id}
            self.logger.exception_context("Error cancelling order", e, error_context)
            raise OrderError(f"Failed to cancel order: {str(e)}")
    
    def get_order(self, client_order_id: str) -> Optional[Order]:
        """Get an order by ID.
        
        Args:
            client_order_id: Order ID to retrieve
            
        Returns:
            Order object or None if not found
        """
        return self.orders.get(client_order_id) or self.filled_orders.get(client_order_id)
    
    def get_active_orders(self, symbol: Optional[str] = None) -> Dict[str, Order]:
        """Get all active orders.
        
        Args:
            symbol: Optional symbol to filter by
            
        Returns:
            Dictionary of active orders
        """
        if symbol:
            symbol = symbol.upper()
            return {
                order_id: order
                for order_id, order in self.orders.items()
                if order.symbol == symbol
            }
        return self.orders.copy()
    
    def get_filled_orders(self, symbol: Optional[str] = None) -> Dict[str, Order]:
        """Get all filled orders.
        
        Args:
            symbol: Optional symbol to filter by
            
        Returns:
            Dictionary of filled orders
        """
        if symbol:
            symbol = symbol.upper()
            return {
                order_id: order
                for order_id, order in self.filled_orders.items()
                if order.symbol == symbol
            }
        return self.filled_orders.copy() 