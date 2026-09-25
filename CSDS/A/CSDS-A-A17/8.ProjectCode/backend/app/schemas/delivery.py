from pydantic import BaseModel


class DeliveryRecommendationOut(BaseModel):
    listing_id: int
    ranked_buyers: dict
    best_route: dict
    best_sell_day: int

    class Config:
        from_attributes = True
