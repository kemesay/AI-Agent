"""Domain model for a proforma invoice extracted from a supplier document."""

from pydantic import BaseModel, Field


class ProformaInvoice(BaseModel):
    supplier_name: str | None = Field(None, alias="supplierName")
    supplier_address: str | None = Field(None, alias="supplierAddress")
    hs_code: str | None = Field(None, alias="hsCode")
    item_description: str | None = Field(None, alias="itemDescription")
    quantity: float | None = None
    unit_price: float | None = Field(None, alias="unitPrice")
    currency: str | None = None
    payment_term: str | None = Field(None, alias="paymentTerm")
    transport_mode: str | None = Field(None, alias="transportMode")
    incoterm: str | None = None
    port_of_loading: str | None = Field(None, alias="portOfLoading")
    origin: str | None = None
    destination: str | None = None
    pi_number: str | None = Field(None, alias="piNumber")
    pi_date: str | None = Field(None, alias="piDate")
    item_total: float | None = Field(None, alias="itemTotal")
    shipment_cost: float | None = Field(None, alias="shipmentCost")
    grand_total: float | None = Field(None, alias="grandTotal")
    purpose: str | None = None
    client_name: str | None = Field(None, alias="clientName")

    model_config = {"populate_by_name": True}
