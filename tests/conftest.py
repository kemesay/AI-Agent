"""Shared pytest fixtures."""

import pytest

from trade_service_agents.models.invoice import ProformaInvoice


@pytest.fixture
def clean_invoice() -> ProformaInvoice:
    """A well-formed proforma invoice with no risk indicators."""
    return ProformaInvoice(
        supplierName="Acme Industrial Supplies Ltd",
        supplierAddress="12 Industrial Park Road, Birmingham, UK",
        hsCode="7323.93",
        itemDescription="Stainless steel household articles",
        quantity=500,
        unitPrice=160,
        currency="USD",
        paymentTerm="LC USD",
        transportMode="Sea Freight",
        incoterm="FOB",
        portOfLoading="Port of Shanghai",
        origin="UK",
        destination="Rotterdam",
        piNumber="PI-2026-001",
        piDate="2026-08-01",
        itemTotal=80000,
        shipmentCost=2000,
        grandTotal=82000,
        purpose="Import of stainless steel household goods",
        clientName="Nordic Trading Co",
    )


@pytest.fixture
def risky_invoice() -> ProformaInvoice:
    """A proforma invoice exhibiting multiple risk indicators."""
    return ProformaInvoice(
        supplierName=None,
        supplierAddress="Village Committee Group 1, Rural District",
        hsCode="9999.99",
        itemDescription="Steel pots and pans",
        quantity=2,
        unitPrice=50,
        currency="USD",
        paymentTerm="TT Advance",
        transportMode="Air Freight",
        incoterm="CFR",
        portOfLoading=None,
        origin="Unknown Region",
        destination="Rotterdam",
        piNumber=None,
        piDate=None,
        itemTotal=100,
        shipmentCost=500,
        grandTotal=1000,
        purpose="Personal gift",
        clientName="Individual Buyer",
    )
