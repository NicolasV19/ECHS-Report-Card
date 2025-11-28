from django.db import models
from django.contrib.auth.models import User


# Create your models here.    


class AbstractPerson(models.Model):
    GENDER_CHOICES = {"M": "Male", "F": "Female"}
    first_name = models.CharField(max_length=20)
    middle_name = models.CharField(max_length=20)
    last_name = models.CharField(max_length=20)
    place_of_birth = models.CharField(max_length=25)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, blank=True, choices=GENDER_CHOICES)
    class Meta:
        abstract = True
        
class Registration(AbstractPerson):
    form_no = models.CharField(max_length=20, unique=True)
    address = models.CharField(max_length=255)
    def __str__(self):
        return f"{self.form_no} ({self.first_name})" 

class AcademicYear(models.Model):
    year = models.CharField(max_length=4)
    begin_date = models.DateField()
    end_date = models.DateField()
    def __str__(self):
        return f"{self.year}"

class LearningPeriod(models.Model):
    academic_year = (models.ForeignKey(AcademicYear, on_delete=models.CASCADE))
    period_name = models.CharField(max_length=15)
    date_start = models.DateField()
    date_end = models.DateField()
    def __str__(self):
        return f"{self.academic_year} / {self.period_name}"

class Teacher(AbstractPerson):
    join_date = (models.DateField())
    user = models.OneToOneField(User, on_delete=models.CASCADE, blank=True, null=True)
    def __str__(self):
        return f"{self.last_name}, {self.first_name}"

class Student(models.Model):
    registration_data = models.OneToOneField(Registration, on_delete=models.CASCADE)
    id_number = models.CharField(max_length=15, unique=True)
    nisn = models.CharField(max_length=15, default="000000000000000", unique=True)
    is_active = models.BooleanField(default=True)
    na_date = models.DateField(null=True, blank=True)
    na_reason = models.CharField(max_length=100, blank=True, null=True)
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['registration_data', 'nisn', 'is_active'],
                                    name='unique_student_data'),
        ]
    def __str__(self):
        return f"{self.id_number}"


class AbstractClass(models.Model):
    name = models.CharField(max_length=50)
    short_name = models.CharField(max_length=6)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete = models.CASCADE)
    class Meta:
        abstract = True

class Class(AbstractClass):
    is_home_class = models.BooleanField(default=False)
    def __str__(self):
        return self.name

class ClassMember(models.Model):
    kelas = models.ForeignKey(Class, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    na_date = models.DateField(null=True, blank=True)
    na_reason = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['kelas', 'student', 'is_active'],
                                    name='unique_class_members'),
        ]

    def __str__(self):
        return f"{self.student}"

class SchoolData(models.Model):
    school_name = models.CharField(max_length=100, unique=True)
    address1 = models.CharField(max_length=100)
    address2 = models.CharField(max_length=100)
    district1 = models.CharField(max_length=100)
    district2 = models.CharField(max_length=100)
    city_name = models.CharField(max_length=50)
    province = models.CharField(max_length=50)

    def __str__(self):
        return self.school_name

class SchoolLevel(models.Model):
    level_name = models.CharField(max_length=25, unique=True)
    short_name = models.CharField(max_length=4, unique=True, blank=True, null=True)
    def __str__(self):
        return self.level_name

class HeadMaster(models.Model):
    school = models.ForeignKey(SchoolData, on_delete=models.CASCADE)
    level = models.ForeignKey(SchoolLevel, default=1, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["school", "level", "full_name"],
                                    name="unique_head_masters")
        ]

    def __str__(self):
        return f"{self.full_name}: {self.school} ({self.level})"