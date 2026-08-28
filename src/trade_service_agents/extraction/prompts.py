"""Prompt templates for the multimodal data extraction agent."""


from PIL import Image


def base_extraction_prompt(first_page: Image.Image) -> list:
    return [
        first_page,
        (
            "Extract customer_name, amount_requested, currency, "
            "intended_use_of_funds, performa_invoice_number, Date, "
            "Tin_number, method_of_payment in JSON format"
        ),
    ]


def proforma_extraction_prompt(first_page: Image.Image) -> list:
    return [
        first_page,
        (
            "Extract supplier info, client info, deliveryTerms, leadOfDelivery, "
            "paymentTerm, transportationMethod, portOfLoading, destination, "
            "modeOfPayment, proformaInvoiceNumber, piDate, items (with sn, "
            "description, hsCode, photoReference, specification, origin, qty, "
            "unit, unitPrice, totalAmount), shipmentCost, totalAmount, currency, "
            "bankDetails (bankName, bankAccount, bankAddress, swiftCode) in JSON "
            "format matching this schema exactly: "
            "{'supplier':{'name':'','address':''},'client':{'name':'','address':''},"
            "'deliveryTerms':'','leadOfDelivery':'','paymentTerm':'',"
            "'transportationMethod':'','portOfLoading':'','destination':'',"
            "'modeOfPayment':'','proformaInvoiceNumber':'','piDate':'','items':"
            "[{'sn':'','description':'','hsCode':'','photoReference':'',"
            "'specification':'','origin':'','qty':'','unit':'','unitPrice':'',"
            "'totalAmount':''}],'shipmentCost':'','totalAmount':'','currency':'',"
            "'bankDetails':{'bankName':'','bankAccount':'','bankAddress':'',"
            "'swiftCode':''}}"
        ),
    ]
