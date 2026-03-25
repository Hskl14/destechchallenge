import math
from django.db import transaction
from .models import AssistanceRequest, Provider, ServiceAssignment
from .tasks import notify_insurance_company_task


class AssistanceService:
    @classmethod
    def create_request(cls, data: dict) -> AssistanceRequest:
        return AssistanceRequest.objects.create(**data)

    @classmethod
    def find_nearest_available_provider(cls, lat: float, lon: float) -> Provider:
        def distance(lat1, lon1, lat2, lon2):
            """ ref: https://stackoverflow.com/questions/41336756/find-the-closest-latitude-and-longitude """
            p = 0.017453292519943295
            hav = (
                0.5
                - math.cos((lat2-lat1) * p) / 2
                + math.cos(lat1 * p)
                * math.cos(lat2 * p)
                * (1 - math.cos((lon2-lon1) * p)) / 2
            )
            return 12742 * math.asin(math.sqrt(hav)) # returns in km
        # TODO: should move the math to DB with ORM annotate() for performance
        available_providers = Provider.objects.filter(is_available=True)
        if not available_providers:
            raise Exception("No available providers exist")
        nearest_provider = None
        min_distance = float("inf")
        for provider in available_providers:
            dist = distance(
                lat,
                lon,
                provider.latitude,
                provider.longitude
            )
            if dist < min_distance:
                min_distance = dist
                nearest_provider = provider
        return nearest_provider

    @classmethod
    def assign_provider_atomic(cls, request_id: int, provider_id: int = None):
        req = AssistanceRequest.objects.get(id=request_id)

        if not provider_id:
            provider_id = cls.find_nearest_available_provider(req.lat, req.lon).id

        with transaction.atomic():
            provider = Provider.objects.select_for_update().get(id=provider_id)
            if provider.is_available:
                provider.is_available = False
                provider.save()
                ServiceAssignment.objects.create(request=req, provider=provider)
                req.status = 'DISPATCHED'
                req.save()
            else:
                raise Exception("Provider is busy!")
        notify_insurance_company_task.delay(req.id)

    @classmethod
    @transaction.atomic
    def complete_request(cls, request_id: int):
        req = AssistanceRequest.objects.select_for_update().select_related('assignment__provider').get(id=request_id)
        if req.status is not 'DISPATCHED':
            raise ValueError(f"Invalid Request Status: {req.status}")

        if hasattr(req, 'assignment'):
            provider = req.assignment.provider
            provider.is_available = True
            provider.save()

        req.status = 'COMPLETED'
        req.save()

    @classmethod
    @transaction.atomic
    def cancel_request(cls, request_id: int):
        req = AssistanceRequest.objects.select_for_update().select_related('assignment__provider').get(id=request_id)
        if req.status is 'COMPLETED':
            raise ValueError(f"Invalid Request Status: {req.status}")

        if req.status == 'DISPATCHED' and hasattr(req, 'assignment'):
            provider = req.assignment.provider
            provider.is_available = True
            provider.save()

        req.status = 'CANCELED'
        req.save()
