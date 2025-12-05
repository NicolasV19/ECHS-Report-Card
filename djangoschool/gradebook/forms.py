from django.shortcuts import get_object_or_404
from django import forms
from django.forms import modelform_factory, formset_factory
from .models import GradeEntry, AssignmentHead, AssignmentDetail, StudentAttendance
from admission.models import Class, ClassMember, Teacher, AbstractClass, Student

# Form Step 1
class GradeEntryForm(forms.ModelForm):
    class Meta:
        model = GradeEntry
        fields = ["academic_year", "period", "teacher", "subject", 
                  "course", "assignment_type"]
        

class TeacherForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = ['user']


# Absensi
# class AttendanceForm(forms.ModelForm):

#     def __init__(self, *args, **kwargs):
#         user = kwargs.pop('user', None)
#         super().__init__(*args, **kwargs)
    
#     current_teacher = ClassMember.student
#     # filtered_students = Teacher.objects.filter(current_teacher)
#     kelas_obj = Teacher.objects.filter(user_id=1)
#     # kelas_teacher = kelas_obj.alast.is_home_room
#     student = forms.ModelChoiceField(
#         queryset=kelas_obj,
#         required=False,  # Make it optional (so you can search by project only)
#     )



#     # jgn lupa yg diatas
#     class Meta:
#         model = StudentAttendance
#         fields = ["attendance_date", "student", "attendance_type", "notes"]
#         widgets = {
#             'attendance_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
#         }


class AttendanceForm(forms.ModelForm):


    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        # get current Teacher.user
        current_teacher = Teacher.objects.get(user=user)
        # filter Class table by current Teacher.user
        teacher_classes = Class.objects.filter(teacher=current_teacher)
            
        # filter ClassMember by filtered Class in kelas
        student_ids = ClassMember.objects.filter(
            kelas__in=teacher_classes, 
            is_active=True
        ).values_list('student_id', flat=True)
            
        # ganti queryset
        self.fields['student'].queryset = Student.objects.filter(id__in=student_ids)
            



    class Meta:
        model = StudentAttendance
        fields = ["attendance_date", "student", "attendance_type", "notes"]
        widgets = {
            'attendance_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
        }

# Form Step 2
class AssignmentHeadForm(forms.ModelForm):
    class Meta:
        model = AssignmentHead
        fields = ['date', 'topic', 'max_score'] 
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
        }
        # Note: course dan assignment type diambil dari step 1, jadi tidak perlu di-field lagi

# Form Step 3 (Detail per Siswa)
class AssignmentDetailItemForm(forms.ModelForm):
    # Field dummy hanya untuk tampilan
    student_name = forms.CharField(
        required=False, 
        widget=forms.TextInput(attrs={'readonly': 'readonly', 'class': 'form-control-plaintext'})
    )

    class Meta:
        model = AssignmentDetail
        fields = ['student', 'score', 'is_active', 'na_reason']
        widgets = {
            'student': forms.HiddenInput(), # ID siswa disembunyikan
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Jika ada data awal student, set nama siswanya untuk display
        if self.initial.get('student'):
            from admission.models import Student
            try:
                s = Student.objects.get(pk=self.initial['student'])
                self.fields['student_name'].initial = str(s)
            except Student.DoesNotExist:
                pass


        

# Membuat FormSet Factory
AssignmentDetailFormSet = formset_factory(AssignmentDetailItemForm, extra=0)