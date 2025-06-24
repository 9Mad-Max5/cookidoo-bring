from dataclasses import dataclass
from typing import Optional

@dataclass
class Ingredient:
    name: str
    amount: Optional[float] = None
    unit: Optional[str] = None
    transferred: Optional[bool] = False
