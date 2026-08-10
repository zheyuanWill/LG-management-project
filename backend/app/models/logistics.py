import enum


class LogisticsNodeType(str, enum.Enum):
    ORDERED = "ordered"
    SUPPLIER_SHIPPED = "supplier_shipped"
    IN_TRANSIT = "in_transit"
    ARRIVED = "arrived"
    WAREHOUSED = "warehoused"
    SENT_TO_OWNER = "sent_to_owner"
    HK_SIGNED = "hk_signed"
    SETTLED = "settled"