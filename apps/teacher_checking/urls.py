#  app/urls/teacher_checking.py
from django.urls import path
from .views import (
    AllWritingList,
    MyCheckingList,
    MyCheckedList,
    claim_view,
    grade_view,
    student_submit_writing,
)

urlpatterns = [
    # student
    path("submit/", student_submit_writing, name="student-submit-writing"),
    # teacher queues
    path("all/", AllWritingList.as_view(), name="all-writing"),
    path("in-progress/", MyCheckingList.as_view(), name="my-checking"),
    path("checked/", MyCheckedList.as_view(), name="my-checked"),
    # teacher actions
    path("claim/", claim_view, name="claim-writing"),
    path("grade/", grade_view, name="grade-writing"),
]
