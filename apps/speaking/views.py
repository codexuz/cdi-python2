#  apps/speaking/views.py
from drf_spectacular.utils import extend_schema
from rest_framework import permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from apps.profiles.models import StudentProfile
from .serializers import SpeakingRequestCreateSerializer, SpeakingRequestSerializer
from .services import create_speaking_request
from .models import SpeakingRequest


@extend_schema(
    tags=["Speaking"],
    summary="Speaking so'rovi yaratish (balance dan yechadi + Admin TG xabari)",
    request=SpeakingRequestCreateSerializer,
    responses={201: SpeakingRequestSerializer},
)
@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def request_speaking(request):

    ser = SpeakingRequestCreateSerializer(data=request.data)
    ser.is_valid(raise_exception=True)

    sp = get_object_or_404(StudentProfile, user=request.user)

    try:
        sr = create_speaking_request(student=sp, note="")
    except ValueError as e:
        return Response({"error": str(e)}, status=400)

    return Response(SpeakingRequestSerializer(sr).data, status=201)


@extend_schema(
    tags=["Speaking"],
    summary="Mening speaking so'rovlarim",
    responses={200: SpeakingRequestSerializer(many=True)},
)
@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def my_speaking_requests(request):
    sp = get_object_or_404(StudentProfile, user=request.user)
    qs = SpeakingRequest.objects.filter(student=sp).order_by("-created_at")
    return Response(SpeakingRequestSerializer(qs, many=True).data)
