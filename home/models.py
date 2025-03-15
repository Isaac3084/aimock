from django.db import models
import uuid

class MockInterview(models.Model):
    mock_id = models.UUIDField(default=uuid.uuid4, editable=False)
    json_mock_resp = models.JSONField()
    job_position = models.CharField(max_length=255)
    job_desc = models.CharField(max_length=255)
    job_experience = models.CharField(max_length=50)
    created_by = models.EmailField()
    created_at = models.DateField(auto_now_add=True)

    class Meta:
        db_table = 'mock_interview' 