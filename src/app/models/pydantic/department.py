from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class Department(BaseModel):
    """Model for department data structure."""
    
    id: int
    name: str
    description: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class DepartmentResponse(BaseModel):
    """Response model for department API calls."""
    
    departments: list[Department]
    total_count: int
    success: bool = True
    error: Optional[str] = None 