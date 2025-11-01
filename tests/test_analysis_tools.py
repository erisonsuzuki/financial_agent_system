from sqlalchemy.orm import Session
from unittest.mock import patch
from datetime import date
from decimal import Decimal

from app.agents import tools
from app import crud, schemas

def test_get_full_portfolio_analysis(db_session: Session):
    # Arrange: Create two different assets with full history
    asset1 = crud.create_asset(db_session, schemas.AssetCreate(ticker="ASSET1.SA", name="Asset One", asset_type="STOCK"))
    crud.create_asset_transaction(db_session, schemas.TransactionCreate(asset_id=asset1.id, quantity=100, price=Decimal("10.00"), transaction_date=date(2025, 1, 1)))

    asset2 = crud.create_asset(db_session, schemas.AssetCreate(ticker="ASSET2.SA", name="Asset Two", asset_type="STOCK"))
    crud.create_asset_transaction(db_session, schemas.TransactionCreate(asset_id=asset2.id, quantity=50, price=Decimal("200.00"), transaction_date=date(2025, 1, 1)))

    # Mock the external market data agent
    with patch('app.agents.market_data_agent.get_current_price') as mock_get_price:
        # Set different current prices for each asset
        def side_effect(ticker):
            if ticker == "ASSET1.SA":
                return 12.00 # This one has a positive return
            if ticker == "ASSET2.SA":
                return 150.00 # This one has a negative return
            return None
        mock_get_price.side_effect = side_effect

        # Act
        result = tools.get_full_portfolio_analysis.invoke({})

        # Assert
        assert isinstance(result, list)
        assert len(result) == 2

        analysis1 = next(item for item in result if item["ticker"] == "ASSET1.SA")
        analysis2 = next(item for item in result if item["ticker"] == "ASSET2.SA")

        assert Decimal(analysis1["financial_return_value"]) > 0
        assert Decimal(analysis2["financial_return_value"]) < 0
        assert analysis2["ticker"] == "ASSET2.SA" # Sanity check
