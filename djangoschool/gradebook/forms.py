from django.shortcuts import get_object_or_404
from django import forms
from slick_reporting.forms import BaseReportForm
from django.forms import modelform_factory, formset_factory, modelformset_factory, BaseFormSet
from .models import GradeEntry, AssignmentHead, AssignmentDetail, StudentAttendance, ReportcardGrade, StudentReportcard, Subject, Course, LearningPeriod, AcademicYear
from admission.models import Class, ClassMember, Teacher, AbstractClass, Student, SchoolLevel

# Define grade choices
FINAL_GRADE_CHOICES = [
    ('A', 'A'),
    ('B', 'B'),
    ('C', 'C'),
    ('D', 'D'),
    ('E', 'E'),
]

# Form Step 1
class GradeEntryForm(forms.ModelForm):
    class Meta:
        model = GradeEntry
        fields = ["academic_year", "period", "teacher", "subject", 
                  "course", "assignment_type"]
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        acayear_nonidleval = self.initial.get('academic_year') or self.data.get('academic_year')

        self.fields['academic_year'].widget.attrs.update({
            'hx-get': '/gradebook/get-period-ge/',
            'hx-trigger': 'change',
            'hx-target': '#period-select-ge',
            'hx-swap': 'innerHTML',
            'hx-include': '[name="0-period"]'
        })
        self.fields['period'].widget.attrs['id'] = 'period-select-ge'
        if acayear_nonidleval:
            self.fields['period'].queryset = LearningPeriod.objects.none()
            self.fields['period'].disabled = True
        else:
            self.fields['period'].queryset = LearningPeriod.objects.all()

        
        self.fields['teacher'].widget.attrs.update({
            'class': 'custom-select mb-4',
            'hx-get': '/gradebook/get-subjects-ge/',
            'hx-trigger': 'change',
            'hx-target': '#subject-select-ge',
            'hx-swap': 'innerHTML',
            'hx-include': '[name="0-subject"]'
        })
        period_nonidleval = self.initial.get('period') or self.data.get('period')
        if period_nonidleval:
            self.fields['teacher'].queryset = Teacher.objects.none()
            self.fields['teacher'].disabled = False
        else:
            self.fields['teacher'].queryset = Teacher.objects.all()
        self.fields['subject'].widget.attrs.update({
            'id': 'subject-select-ge',
            'class': 'custom-select mb-4',
            'hx-get': '/gradebook/get-courses/',
            'hx-trigger': 'change',
            'hx-target': '#course-select-ge',
            'hx-swap': 'innerHTML',
            'hx-include': '[name="0-course"]'
        })
        self.fields['course'].widget.attrs['id'] = 'course-select-ge'
        self.fields['academic_year'].widget.attrs.update({
            'class': 'custom-select mb-4',
            'hx-get': '/gradebook/get-period-ge/',
            'hx-trigger': 'change',
            'hx-target': '#period-select',
            'hx-swap': 'innerHTML',
            'hx-include': '[name="1-period"]'
            })
        self.fields['period'].widget.attrs.update({
            'class': 'custom-select mb-4',
            'id': 'period-select'
            })
        # self.fields['student'].widget.attrs.update({
        #     'class': 'custom-select mb-4',
        #     'hx-get': '/gradebook/get-courses/',
        #     'hx-trigger': 'change',
        #     'hx-target': '#course-select',
        #     'hx-swap': 'innerHTML',
        #     'hx-include': '[name="1-course"]'
        #     })
        # self.fields['attendance_type'].widget.attrs.update({
        #     'class': 'custom-select mb-4',
        #     'hx-get': '/gradebook/get-courses/',
        #     'hx-trigger': 'change',
        #     'hx-target': '#course-select',
        #     'hx-swap': 'innerHTML',
        #     'hx-include': '[name="1-course"]'
        #     })
        # self.fields['notes'].widget.attrs.update({
        #     'class': 'custom-select mb-4',
        #     'hx-get': '/gradebook/get-courses/',
        #     'hx-trigger': 'change',
        #     'hx-target': '#course-select',
        #     'hx-swap': 'innerHTML',
        #     'hx-include': '[name="1-course"]'
        #     })
        
class ReportCardComment(forms.ModelForm):
    class Meta:
        model = ReportcardGrade
        fields = ["teacher_notes"]

        

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
        teacher_classes = Class.objects.filter(teacher=current_teacher, is_home_class=True)
        teacher_classes_nothomeroom = Class.objects.filter(teacher=current_teacher, is_home_class=False)
            
        # filter ClassMember by filtered Class in kelas
        student_ids = ClassMember.objects.filter(
            kelas__in=teacher_classes, 
            is_active=True
        ).values_list('student_id', flat=True)
            
        
        # ganti queryset
        # self.fields['student'].queryset = Student.objects.filter(id__in=student_ids)
        if teacher_classes:
            self.fields['student'].queryset = Student.objects.filter(id__in=student_ids)
        else:
            self.fields['student'].queryset = Student.objects.all()


            



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

    # teacher_notes = forms.CharField(
    #     widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Notes...'}),
    #     required=False
    # )

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


        if self.instance and self.instance.pk:
            try:
                # You need to find the specific ReportcardGrade for this Student + Subject
                # Note: You might need to filter by a specific 'active' ReportCard if you have multiple terms.
                grade_entry = ReportcardGrade.objects.filter(
                    reportcard__student=self.instance.student,
                    subject=self.instance.assignment_head.subject
                ).first()
                
                if grade_entry:
                    self.fields['teacher_notes'].initial = grade_entry.teacher_notes
            except (AttributeError, ReportcardGrade.DoesNotExist):
                pass

        

# Membuat FormSet Factory
class AssignmentDetailFormSet(BaseFormSet):
    def __init__(self, *args, max_score=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_score = max_score
    
    def clean(self):
        super().clean()
        if self.max_score is not None:
            for form in self.forms:
                if form.cleaned_data and form.cleaned_data.get('score') is not None:
                    if form.cleaned_data['score'] > self.max_score:
                        form.add_error('score', f"Score cannot exceed {self.max_score}.")

AssignmentDetailFormSet = formset_factory(AssignmentDetailItemForm, formset=AssignmentDetailFormSet, extra=0)


class StudentReportcardForm(forms.ModelForm):
    class Meta:
        model = StudentReportcard
        fields = ["academic_year", "period", "is_mid", "level"]
        widgets = {
            'student': forms.Select(attrs={'class': 'form-select select2'}), # Assuming you use select2
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['academic_year'].widget.attrs.update({
            'class': 'custom-select mb-4',
            'hx-get': '/gradebook/get-period-ge/',
            'hx-trigger': 'change',
            'hx-target': '#period-select',
            'hx-swap': 'innerHTML',
            'hx-include': '[name="1-period"]'
            })
        self.fields['period'].widget.attrs.update({
                'class': 'custom-select mb-4',
                'id': 'period-select'
                })

class CourseByTeacher(forms.ModelForm):
    class Meta:
        model = GradeEntry
        fields = ["subject", "course"]
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['course'].required = False
        self.fields['subject'].widget.attrs.update({
            'class': 'custom-select mb-4',
            'hx-get': '/gradebook/get-courses/',
            'hx-trigger': 'change',
            'hx-target': '#course-select',
            'hx-swap': 'innerHTML',
            'hx-include': '[name="1-course"]'
        })
        self.fields['course'].widget.attrs.update({
            'class': 'custom-select mb-4',
            'id': 'course-select'
        })


class ReportCardGradeForm(forms.ModelForm):
    # Dummy field for display purposes only
    subject_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'readonly': 'readonly', 'class': 'form-control-plaintext fw-bold'})
    )

    student_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'readonly': 'readonly', 'class': 'form-control-plaintext fw-bold'})
    )
    

    # This must be required=False, as you haven't entered a score yet
    final_score = forms.DecimalField(required=False, max_digits=5, decimal_places=2, initial=0) 
    
    # This must be required=False, as you haven't entered a grade yet
    final_grade = forms.ChoiceField(choices=FINAL_GRADE_CHOICES, required=False) 
    
    # Hidden field for the Subject ID: MUST NOT BE required=True
    subject = forms.ModelChoiceField(queryset=Subject.objects.all(), required=False)

    teacher_notes = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Notes...'}),
        required=False
    )

    def __init__(self, *args, subject_queryset=None, **kwargs):
        super().__init__(*args, **kwargs)

        # Apply a filtered queryset when provided (passed via formset form_kwargs)
        if subject_queryset:
            self.fields['subject'].queryset = subject_queryset
        else:
            self.fields['subject'].queryset = Subject.objects.all()

        # UI tweaks
        # Keep the subject value submitted: use readonly/display field for name
        self.fields['subject'].widget.attrs.pop('disabled', None)
        self.fields['subject'].widget.attrs['readonly'] = True
        self.fields['subject'].widget.attrs['class'] = 'form-control bg-light'

        self.fields['final_score'].widget.attrs.pop('disabled', None)
        self.fields['final_score'].widget.attrs['readonly'] = True
        self.fields['final_score'].widget.attrs['class'] = 'form-control bg-light'

        self.fields['final_grade'].disabled = True
        self.fields['final_grade'].widget.attrs['readonly'] = True
        # self.fields['final_grade'].widget.attrs['class'] = 'form-control bg-light'

        # Populate subject_name for display if initial data exists
        if self.initial.get('subject'):
            try:
                subj = Subject.objects.get(pk=self.initial['subject'])
                self.fields['subject_name'].initial = subj.subject_name
            except Subject.DoesNotExist:
                pass

        # Populate student_name for display if initial data exists
        if self.initial.get('student_name'):
            self.fields['student_name'].initial = self.initial['student_name']

    class Meta:
        model = ReportcardGrade
        fields = ['student_name', 'subject', 'final_score', 'final_grade', 'teacher_notes']
        widgets = {
            'student_name': forms.Textarea(attrs={'class': 'form-control', 'rows': 1}),
            'subject': forms.HiddenInput(),
            'final_score': forms.NumberInput(attrs={'class': 'form-control'}),
            'final_grade': forms.Select(attrs={'class': 'form-select'}),
            'teacher_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 1}),
        }
        exclude = ('reportcard',)
        

ReportCardGradeFormset = formset_factory(ReportCardGradeForm, extra=0)
# ReportCardGradeFormset = modelformset_factory(
#     ReportcardGrade,  # Use the Model
#     form=ReportCardGradeForm, # Use your custom form
#     extra=0
# )

class ReportCardFilterForm(BaseReportForm):
    subject_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'readonly': 'readonly', 'class': 'form-control-plaintext fw-bold'})
    )

    student_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'readonly': 'readonly', 'class': 'form-control-plaintext fw-bold'})
    )
    

    # This must be required=False, as you haven't entered a score yet
    final_score = forms.DecimalField(required=False, max_digits=5, decimal_places=2, initial=0) 
    
    # This must be required=False, as you haven't entered a grade yet
    final_grade = forms.ChoiceField(choices=FINAL_GRADE_CHOICES, required=False) 
    
    # Hidden field for the Subject ID: MUST NOT BE required=True
    subject = forms.ModelChoiceField(queryset=Subject.objects.all(), required=False)

    teacher_notes = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Notes...'}),
        required=False
    )

    def __init__(self, *args, subject_queryset=None, **kwargs):
        object().__init__(*args, **kwargs)

        # Apply a filtered queryset when provided (passed via formset form_kwargs)
        if subject_queryset:
            self.fields['subject'].queryset = subject_queryset
        else:
            self.fields['subject'].queryset = Subject.objects.all()

        # UI tweaks
        # Keep the subject value submitted: use readonly/display field for name
        self.fields['subject'].widget.attrs.pop('disabled', None)
        self.fields['subject'].widget.attrs['readonly'] = True
        self.fields['subject'].widget.attrs['class'] = 'form-control bg-light'

        self.fields['final_score'].widget.attrs.pop('disabled', None)
        self.fields['final_score'].widget.attrs['readonly'] = True
        self.fields['final_score'].widget.attrs['class'] = 'form-control bg-light'

        self.fields['final_grade'].disabled = True
        self.fields['final_grade'].widget.attrs['readonly'] = True
        # self.fields['final_grade'].widget.attrs['class'] = 'form-control bg-light'

        # Populate subject_name for display if initial data exists
        if self.initial.get('subject'):
            try:
                subj = Subject.objects.get(pk=self.initial['subject'])
                self.fields['subject_name'].initial = subj.subject_name
            except Subject.DoesNotExist:
                pass

        # Populate student_name for display if initial data exists
        if self.initial.get('student_name'):
            self.fields['student_name'].initial = self.initial['student_name']

    class Meta:
        model = ReportcardGrade
        fields = ['student_name', 'subject', 'final_score', 'final_grade', 'teacher_notes']
        widgets = {
            'student_name': forms.Textarea(attrs={'class': 'form-control', 'rows': 1}),
            'subject': forms.HiddenInput(),
            'final_score': forms.NumberInput(attrs={'class': 'form-control'}),
            'final_grade': forms.Select(attrs={'class': 'form-select'}),
            'teacher_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 1}),
        }
        exclude = ('reportcard',)