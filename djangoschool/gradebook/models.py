import dateutil.utils
from django.db import models
from datetime import datetime, date
from admission.models import AcademicYear, AbstractClass, Student, SchoolLevel, Teacher, LearningPeriod

# from account.models import User

# Create your models here.
GRADE_CHOICES = [
    ("A", "A"),
    ("B", "B"),
    ("C", "C"),
    ("D", "D"),
    ("E", "E"),
]
class Subject(models.Model):
    subject_name = models.CharField(max_length=35, unique=True)
    short_name = models.CharField(max_length=5, blank=True, null=True)

    def __str__ (self):
        return f"{self.short_name} - {self.subject_name}"

class AssignmentType(models.Model):
    name = models.CharField(max_length=25, unique=True)
    short_name = models.CharField(max_length=10)

    def __str__ (self):
        return f"{self.name} ({self.short_name})"

class Weighting(models.Model):
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    level = models.ForeignKey(SchoolLevel, default=1, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    assignment = models.ForeignKey(AssignmentType, on_delete=models.CASCADE)
    weight = models.DecimalField(max_digits=2, decimal_places=2, default=0.0)

class Course(AbstractClass):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)

    def __str__ (self):
        return f"{self.subject.subject_name} - {self.academic_year.year}"

class CourseMember(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    na_date = models.DateField(null=True, blank=True)
    na_reason = models.CharField(max_length=100, blank=True, null=True)

class PassingGrade(models.Model):
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    level = models.ForeignKey(SchoolLevel, default=1, on_delete=models.CASCADE)
    passing_grade = models.IntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['academic_year', 'subject', 'level'],
                                    name='unique_passing_grades'),
        ]

class GradeEntry(models.Model):
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    period = models.ForeignKey(LearningPeriod, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    school_level = models.ForeignKey(SchoolLevel, default=1, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    assignment_type = models.ForeignKey(AssignmentType, on_delete=models.CASCADE)
    assignment_date = models.DateField(default=date.today())
    assignment_topic = models.CharField(max_length=100, default="to be fill later.")
    # set table to readonly by disabling all save/delete methode

    #def save(self, *args, **kwargs):
    #    pass

    #def delete(self, *args, **kwargs):
    #    pass

    #def __delete__(self, instance):
    #    pass

class AssignmentHead(models.Model):
    assignment = models.ForeignKey(AssignmentType, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    date = models.DateField(null=True, blank=True)
    topic = models.TextField(null=True, blank=True)
    max_score = models.IntegerField(default=100)

class AssignmentDetail(models.Model):
    assignment_head = models.ForeignKey(AssignmentHead, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    na_date = models.DateField(null=True, blank=True)
    na_reason = models.CharField(max_length=100, blank=True, null=True)

class ReportcardGrade(models.Model):
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    period = models.ForeignKey(LearningPeriod, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    level = models.ForeignKey(SchoolLevel, default=1, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    final_score = models.IntegerField(default=0)
    final_grade = models.CharField(max_length=1, choices=GRADE_CHOICES)

