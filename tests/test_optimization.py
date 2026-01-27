from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.mark.asyncio
async def test_optimize_endpoint_success():
    """Test successful optimization request"""
    mock_response = "Optimized query: specific details added."

    with patch(
        "app.services.optimization_service.OptimizationService.optimize_input", new_callable=AsyncMock
    ) as mock_optimize:
        mock_optimize.return_value = mock_response

        # Note: OptimizationService is instantiated as `optimization_service` in the module.
        # However, patching the class method on the instance or the class depends on how it's used.
        # Since we import the instance `optimization_service` in api/v1/optimization.py,
        # we should patch the method on the class or the specific instance.
        # Patching the class method affects all instances.

        response = client.post("/api/v1/optimization/optimize", json={"input": "help me check green credit"})

        assert response.status_code == 200
        data = response.json()
        assert data["optimized_input"] == mock_response
        mock_optimize.assert_called_once_with("help me check green credit")


@pytest.mark.asyncio
async def test_optimize_endpoint_empty():
    """Test empty input validation"""
    response = client.post("/api/v1/optimization/optimize", json={"input": "   "})
    assert response.status_code == 400
    assert "Input cannot be empty" in response.json()["detail"]
